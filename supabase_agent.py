import logging
import os
import re

import pandas as pd
from dotenv import load_dotenv
from supabase import create_client

# Load environment variables from the local .env file.
load_dotenv()

logger = logging.getLogger(__name__)


def _normalize_column_name(column_name: str) -> str:
    normalized = re.sub(r"\s+", "_", str(column_name).strip().lower())
    normalized = re.sub(r"[^a-z0-9_]", "_", normalized)
    normalized = re.sub(r"_+", "_", normalized)
    normalized = normalized.strip("_")
    if not normalized:
        normalized = "col_unknown"
    return normalized

def get_table_summary(df: pd.DataFrame) -> dict:
    """
    Return a lightweight summary of the provided DataFrame.
    """
    return {
        "row_count": int(len(df)),
        "columns": [str(column) for column in df.columns.tolist()],
        "sample": df.head(5).to_dict(orient="records"),
        "stats": df.describe().to_dict(),
    }


def log_upload(session_id: str, row_count: int, columns: list[str]) -> None:
    try:
        supabase_url = os.getenv("SUPABASE_URL")
        supabase_key = os.getenv("SUPABASE_KEY")

        if not supabase_url or not supabase_key:
            return

        client = create_client(supabase_url, supabase_key)
        client.table("csv_uploads").insert(
            {
                "session_id": session_id,
                "row_count": row_count,
                "columns": list(columns),
            }
        ).execute()
    except Exception:
        logger.exception("Failed to log upload to Supabase.")
