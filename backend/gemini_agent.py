"""Gemini agent — generates natural-language narratives from structured data."""

from __future__ import annotations

from typing import Any

from google import genai
from google.genai import types

from utils import format_table, get_env

_DEFAULT_MODEL = "gemini-1.5-flash"

_SYSTEM_PROMPT = (
    "You are DataNarrator, an AI analyst. "
    "You receive a table of query results and a user question. "
    "Write a clear, concise narrative (2–4 sentences) that directly answers the "
    "question using the data. Highlight key figures, trends, or anomalies. "
    "Do not reproduce the raw table in your answer."
)


class GeminiAgent:
    """Wraps the Google GenAI SDK to generate data narratives."""

    def __init__(self, model_name: str = _DEFAULT_MODEL) -> None:
        self._client = genai.Client(api_key=get_env("GEMINI_API_KEY"))
        self._model_name = model_name

    def generate_narrative(
        self,
        records: list[dict[str, Any]],
        question: str,
    ) -> str:
        """Return a narrative that answers *question* given the *records*.

        Parameters
        ----------
        records:
            List of row-dicts returned by :class:`SnowflakeAgent`.
        question:
            The original natural-language question posed by the user.
        """
        table_text = format_table(records)
        prompt = (
            f"User question: {question}\n\n"
            f"Query results:\n{table_text}"
        )
        response = self._client.models.generate_content(
            model=self._model_name,
            contents=prompt,
            config=types.GenerateContentConfig(
                system_instruction=_SYSTEM_PROMPT,
            ),
        )
        return response.text.strip()
