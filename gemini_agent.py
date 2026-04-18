import json
import os

import google.generativeai as genai
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure Gemini
api_key = os.getenv("GEMINI_API_KEY")
if api_key:
    genai.configure(api_key=api_key)

ERROR_INSIGHT = "Unable to generate insight."

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
            model_name="gemini-1.5-flash",
            system_instruction=system_instruction
        )

        prompt = (
            f"Analyze this dataset and return JSON:\n"
            f"- Row Count: {table_summary.get('row_count')}\n"
            f"- Columns: {table_summary.get('columns')}\n"
            f"- Sample Data: {table_summary.get('sample')}\n"
            f"- Key Stats: {table_summary.get('stats')}\n"
        )

        response = model.generate_content(prompt)
        raw = response.text.strip()
        # Strip markdown code blocks if present
        if raw.startswith("```"):
            raw = raw.split("```")[1]
            if raw.startswith("json"):
                raw = raw[4:]
        result = json.loads(raw)

        chart_data = result.get("chart_data") or result.get("chart")
        if isinstance(chart_data, dict):
            chart_data = {
                "type": chart_data.get("type", "bar"),
                "labels": chart_data.get("labels", []),
                "values": chart_data.get("values", []),
                "title": chart_data.get("title", ""),
            }
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
    """
    Answer a follow-up question based on the previous insight.
    """
    try:
        # NOTE: gemini-2.0-flash quota is exhausted — keep gemini-1.5-flash here
        model = genai.GenerativeModel("gemini-1.5-flash")
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
