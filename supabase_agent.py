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
    return normalized.strip("_")


def _create_supabase_client() -> Client:
    supabase_url = os.getenv("SUPABASE_URL")
    supabase_key = os.getenv("SUPABASE_KEY")

    if not supabase_url or not supabase_key:
        raise ValueError("SUPABASE_URL and SUPABASE_KEY must be set in the .env file.")

    return create_client(supabase_url, supabase_key)


def ingest_csv(df: pd.DataFrame, table_name: str) -> str:
    """
    Insert all rows from a DataFrame into an existing Supabase table.
    """
    try:
        normalized_df = df.copy()
        normalized_df.columns = [_normalize_column_name(column) for column in normalized_df.columns]
        normalized_df = normalized_df.where(pd.notnull(normalized_df), None)

        records = normalized_df.to_dict(orient="records")
        client = _create_supabase_client()
        client.table(table_name).insert(records).execute()
        return table_name
    except Exception as error:
        print(f"Error ingesting CSV into Supabase: {error}")
        return ""


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
