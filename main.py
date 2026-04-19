import os
import uuid
import base64
import io
import logging

import pandas as pd
from fastapi import BackgroundTasks, FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

import supabase_agent
import gemini_agent
import tts_agent as elevenlabs_agent

logger = logging.getLogger(__name__)

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

class FollowupRequest(BaseModel):
    insight: str
    question: str

@app.get("/")
async def root():
    return FileResponse("index.html")

@app.post("/analyze")
async def analyze(background_tasks: BackgroundTasks, file: UploadFile = File(...)):
    if not file.filename.endswith(".csv"):
        raise HTTPException(status_code=400, detail="Only CSV files are allowed.")

    try:
        contents = await file.read()

        if len(contents) > 10 * 1024 * 1024:
            raise HTTPException(status_code=400, detail="File too large. Maximum size is 10MB.")

        try:
            df = pd.read_csv(io.BytesIO(contents))
        except (pd.errors.EmptyDataError, pd.errors.ParserError, UnicodeDecodeError):
            raise HTTPException(
                status_code=400,
                detail="Invalid CSV file format or encoding. Please save as UTF-8.",
            )

        if df.empty or len(df.columns) == 0:
            raise HTTPException(status_code=400, detail="CSV file is empty or has no columns.")

        session_id = "upload_" + uuid.uuid4().hex[:8]

        summary = supabase_agent.get_table_summary(df)
        background_tasks.add_task(supabase_agent.log_upload, session_id, len(df), list(df.columns))

        gemini_result = gemini_agent.generate_insight(summary)
        insight_text = gemini_result.get("insight", "")
        chart_data = gemini_result.get("chart_data")

        is_error_insight = (insight_text == gemini_agent.ERROR_INSIGHT or not insight_text)
        if is_error_insight:
            audio_b64 = ""
        else:
            audio_bytes = elevenlabs_agent.text_to_audio(insight_text)
            audio_b64 = base64.b64encode(audio_bytes).decode("utf-8") if audio_bytes else ""

        return {
            "insight": insight_text,
            "chart_data": chart_data,
            "audio_b64": audio_b64,
            "table_name": session_id,
            "row_count": len(df),
            "columns": list(df.columns)
        }
    except HTTPException:
        raise
    except Exception:
        logger.exception("Unhandled error in /analyze")
        raise HTTPException(status_code=500, detail="Internal server error.")

@app.post("/followup")
async def followup(req: FollowupRequest):
    try:
        answer = gemini_agent.answer_followup(req.insight, req.question)
        if not answer:
            raise HTTPException(status_code=500, detail="Gemini failed to generate an answer.")

        audio_bytes = elevenlabs_agent.text_to_audio(
            answer,
            prefix=f"You asked: {req.question}. Here's what I found:"
        )
        audio_b64 = base64.b64encode(audio_bytes).decode("utf-8") if audio_bytes else ""

        return {
            "answer": answer,
            "audio_b64": audio_b64
        }
    except HTTPException:
        raise
    except Exception:
        logger.exception("Unhandled error in /followup")
        raise HTTPException(status_code=500, detail="Internal server error.")

@app.get("/health")
async def health():
    return {"status": "ok", "service": "DataNarrator"}
