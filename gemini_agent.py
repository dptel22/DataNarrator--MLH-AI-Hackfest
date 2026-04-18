import json
import os
import re

import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()

api_key = os.getenv("GEMINI_API_KEY")
if api_key:
    genai.configure(api_key=api_key)

ERROR_INSIGHT = "Unable to generate insight."

# gemini-2.5-flash: confirmed available and working on free tier
GEMINI_MODEL = "gemini-2.5-flash"

def generate_insight(table_summary: dict) -> dict:
    try:
        system_instruction = """You are a professional data narrator and analyst.
        You must respond with ONLY valid JSON, no markdown, no explanation outside the JSON.
        Return this exact structure:
        {
          "insight": "3 sentence spoken briefing ending with one actionable recommendation",
          "chart_data": {
            "type": "bar",
            "labels": ["label1", "label2", "label3"],
            "values": [10, 20, 30],
            "title": "descriptive chart title"
          }
        }
        For chart type: use "bar" for comparisons/counts, "pie" for distributions/percentages.
        Labels: pick the most meaningful column. Max 8 labels. If data has no good chart, still return chart_data using top value counts.
        Values must be numbers only."""

        model = genai.GenerativeModel(
            model_name=GEMINI_MODEL,
            system_instruction=system_instruction
        )

        # Truncate sample to 500 chars to prevent prompt injection and runaway token usage
        raw_sample = str(table_summary.get('sample', ''))[:500]

        prompt = (
            f"Analyze this dataset and return JSON:\n"
            f"- Row Count: {table_summary.get('row_count')}\n"
            f"- Columns: {table_summary.get('columns')}\n"
            f"- Sample Data: {raw_sample}\n"
            f"- Key Stats: {table_summary.get('stats')}\n"
        )

        response = model.generate_content(prompt)
        raw = response.text.strip()

        # Extract JSON from a markdown code block if present (handles filler text before the block)
        code_block = re.search(r"```(?:json)?\n?(.*?)\n?```", raw, re.DOTALL)
        if code_block:
            raw = code_block.group(1).strip()

        try:
            result = json.loads(raw)
        except (json.JSONDecodeError, ValueError):
            # Fallback: salvage the insight string via regex before giving up
            insight_match = re.search(r'"insight"\s*:\s*"((?:[^"\\]|\\.)*)"', raw)
            if insight_match:
                print("[warn] gemini_agent: JSON parse failed; salvaged insight via regex")
                return {"insight": insight_match.group(1), "chart_data": None}
            raise  # triggers outer except → ERROR_INSIGHT

        chart_data = result.get("chart_data") or result.get("chart")
        if isinstance(chart_data, dict):
            chart_data = {
                "type": chart_data.get("type", "bar"),
                "labels": chart_data.get("labels", []),
                "values": chart_data.get("values", []),
                "title": chart_data.get("title", ""),
            }
            if (
                not chart_data["labels"]
                or not chart_data["values"]
                or all(value == 0 for value in chart_data["values"])
            ):
                chart_data = None
        else:
            chart_data = None

        return {
            "insight": result.get("insight", ""),
            "chart_data": chart_data,
        }
    except Exception as e:
        print(f"Error generating insight: {e}")
        return {"insight": ERROR_INSIGHT, "chart_data": None}


def answer_followup(insight: str, question: str) -> str:
    try:
        model = genai.GenerativeModel(GEMINI_MODEL)
        prompt = (
            f"Based on the following data insight:\n"
            f"\"{insight}\"\n\n"
            f"Answer the user's follow-up question in maximum 2 sentences.\n"
            f"Question: {question}"
        )
        response = model.generate_content(prompt)
        return response.text.strip()
    except Exception as e:
        print(f"Error answering follow-up: {e}")
        return ""
