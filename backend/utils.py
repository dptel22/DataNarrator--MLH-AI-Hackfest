"""Utility helpers shared across the DataNarrator backend."""

from __future__ import annotations

import os
from typing import Any


def get_env(key: str, default: str | None = None) -> str:
    """Return an environment variable, raising if it is missing and no default given."""
    value = os.environ.get(key, default)
    if value is None:
        raise EnvironmentError(
            f"Required environment variable '{key}' is not set. "
            "Copy .env.example to .env and fill in the values."
        )
    return value


def rows_to_dicts(cursor_description: list, rows: list[tuple]) -> list[dict[str, Any]]:
    """Convert raw Snowflake cursor rows to a list of dicts keyed by column name."""
    columns = [col[0].lower() for col in cursor_description]
    return [dict(zip(columns, row)) for row in rows]


def format_table(records: list[dict[str, Any]]) -> str:
    """Return a compact, human-readable plain-text table from a list of row dicts."""
    if not records:
        return "(no data)"
    headers = list(records[0].keys())
    col_widths = {h: len(h) for h in headers}
    for row in records:
        for h in headers:
            col_widths[h] = max(col_widths[h], len(str(row.get(h, ""))))

    separator = "+-" + "-+-".join("-" * col_widths[h] for h in headers) + "-+"
    header_row = "| " + " | ".join(h.ljust(col_widths[h]) for h in headers) + " |"
    lines = [separator, header_row, separator]
    for row in records:
        line = "| " + " | ".join(str(row.get(h, "")).ljust(col_widths[h]) for h in headers) + " |"
        lines.append(line)
    lines.append(separator)
    return "\n".join(lines)
