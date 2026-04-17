"""DataNarrator — FastAPI backend entry point."""

from __future__ import annotations

import base64
import os
import sys

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel

# Allow imports from the same directory when running with uvicorn
sys.path.insert(0, os.path.dirname(__file__))

load_dotenv()

from elevenlabs_agent import ElevenLabsAgent  # noqa: E402
from gemini_agent import GeminiAgent  # noqa: E402
from snowflake_agent import SnowflakeAgent  # noqa: E402

app = FastAPI(
    title="DataNarrator",
    description=(
        "Query your Snowflake data warehouse, generate an AI narrative with "
        "Google Gemini, and synthesize audio narration via ElevenLabs."
    ),
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── request / response models ──────────────────────────────────────────────────


class NarrateRequest(BaseModel):
    sql: str
    question: str


class NarrateResponse(BaseModel):
    records: list[dict]
    narrative: str
    audio_base64: str  # MP3 audio encoded as base64


# ── endpoints ──────────────────────────────────────────────────────────────────


@app.get("/health")
def health() -> dict:
    """Liveness check."""
    return {"status": "ok"}


@app.post("/narrate", response_model=NarrateResponse)
def narrate(body: NarrateRequest) -> NarrateResponse:
    """Run *sql* against Snowflake, generate a narrative, and synthesize audio.

    1. Execute the SQL query via :class:`SnowflakeAgent`.
    2. Generate a narrative with :class:`GeminiAgent`.
    3. Synthesize MP3 audio with :class:`ElevenLabsAgent`.
    4. Return all three artifacts to the caller.
    """
    # ── 1. query data ──────────────────────────────────────────────────────────
    try:
        with SnowflakeAgent() as agent:
            records = agent.run_query(body.sql)
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Snowflake error: {exc}") from exc

    # ── 2. generate narrative ──────────────────────────────────────────────────
    try:
        gemini = GeminiAgent()
        narrative = gemini.generate_narrative(records, body.question)
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Gemini error: {exc}") from exc

    # ── 3. synthesize audio ────────────────────────────────────────────────────
    try:
        tts = ElevenLabsAgent()
        audio_bytes = tts.synthesize(narrative)
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"ElevenLabs error: {exc}") from exc

    return NarrateResponse(
        records=records,
        narrative=narrative,
        audio_base64=base64.b64encode(audio_bytes).decode(),
    )


@app.post("/query")
def query_only(body: NarrateRequest) -> JSONResponse:
    """Execute *sql* and return raw records without narrative or audio."""
    try:
        with SnowflakeAgent() as agent:
            records = agent.run_query(body.sql)
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Snowflake error: {exc}") from exc
    return JSONResponse({"records": records})
