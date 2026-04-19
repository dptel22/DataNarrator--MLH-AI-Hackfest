import re

import pandas as pd
from dotenv import load_dotenv

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
