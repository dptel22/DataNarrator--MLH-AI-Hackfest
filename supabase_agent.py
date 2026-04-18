import os
import re

import pandas as pd
from dotenv import load_dotenv
from supabase import Client, create_client

# Load environment variables from the local .env file.
load_dotenv()


def _normalize_column_name(column_name: str) -> str:
    normalized = re.sub(r"\s+", "_", str(column_name).strip().lower())
    normalized = re.sub(r"[^a-z0-9_]", "_", normalized)
    normalized = re.sub(r"_+", "_", normalized)
    normalized = normalized.strip("_")
    if not normalized:
        normalized = "col_unknown"
    return normalized


def _create_supabase_client() -> Client:
    supabase_url = os.getenv("SUPABASE_URL")
    supabase_key = os.getenv("SUPABASE_KEY")

    if not supabase_url or not supabase_key:
        raise ValueError("SUPABASE_URL and SUPABASE_KEY must be set in the .env file.")

    return create_client(supabase_url, supabase_key)



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
