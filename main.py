import uuid
import base64
import pandas as pd
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

import supabase_agent
import gemini_agent
import elevenlabs_agent

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class FollowupRequest(BaseModel):
    insight: str
    question: str

@app.post("/analyze")
async def analyze(file: UploadFile = File(...)):
    if not file.filename.endswith(".csv"):
        raise HTTPException(status_code=400, detail="Only CSV files are allowed.")

    try:
        df = pd.read_csv(file.file)
        table_name = "upload_" + uuid.uuid4().hex[:8]

        supabase_agent.ingest_csv(df, table_name)
        summary = supabase_agent.get_table_summary(df)

        insight_text = gemini_agent.generate_insight(summary)
        audio_bytes = elevenlabs_agent.text_to_audio(insight_text)
        audio_b64 = base64.b64encode(audio_bytes).decode("utf-8") if audio_bytes else ""

        return {
            "insight": insight_text,
            "audio_b64": audio_b64,
            "table_name": table_name,
            "row_count": len(df),
            "columns": list(df.columns)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/followup")
async def followup(req: FollowupRequest):
    try:
        answer = gemini_agent.answer_followup(req.insight, req.question)
        audio_bytes = elevenlabs_agent.text_to_audio(answer)
        audio_b64 = base64.b64encode(audio_bytes).decode("utf-8") if audio_bytes else ""

        return {
            "answer": answer,
            "audio_b64": audio_b64
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health")
async def health():
    return {"status": "ok"}
