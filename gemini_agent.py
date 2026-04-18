import os
import google.generativeai as genai
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure Gemini
api_key = os.getenv("GEMINI_API_KEY")
if api_key:
    genai.configure(api_key=api_key)

def generate_insight(table_summary: dict) -> str:
    """
    Generate a plain language briefing from a table summary.
    """
    try:
        system_instruction = "You are a professional data narrator. Convert data findings into a clear 3-sentence spoken briefing. Plain language only. End with one actionable recommendation."
        model = genai.GenerativeModel(
            model_name="gemini-1.5-flash",
            system_instruction=system_instruction
        )
        
        prompt = (
            f"Here is a summary of the data table:\n"
            f"- Row Count: {table_summary.get('row_count')}\n"
            f"- Columns: {table_summary.get('columns')}\n"
            f"- Sample Data: {table_summary.get('sample')}\n"
            f"- Key Stats: {table_summary.get('stats')}\n"
        )
        
        response = model.generate_content(prompt)
        return response.text.strip()
    except Exception as e:
        print(f"Error generating insight: {e}")
        return ""

def answer_followup(insight: str, question: str) -> str:
    """
    Answer a follow-up question based on the previous insight.
    """
    try:
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
