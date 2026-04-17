"""Snowflake agent — executes SQL queries and returns structured results."""

from __future__ import annotations

from typing import Any

import snowflake.connector

from utils import get_env, rows_to_dicts


class SnowflakeAgent:
    """Manages a Snowflake connection and exposes a simple query interface."""

    def __init__(self) -> None:
        self._conn: snowflake.connector.SnowflakeConnection | None = None

    # ── connection management ──────────────────────────────────────────────────

    def connect(self) -> None:
        """Open a Snowflake connection using environment-variable credentials."""
        self._conn = snowflake.connector.connect(
            account=get_env("SNOWFLAKE_ACCOUNT"),
            user=get_env("SNOWFLAKE_USER"),
            password=get_env("SNOWFLAKE_PASSWORD"),
            warehouse=get_env("SNOWFLAKE_WAREHOUSE"),
            database=get_env("SNOWFLAKE_DATABASE"),
            schema=get_env("SNOWFLAKE_SCHEMA"),
            role=get_env("SNOWFLAKE_ROLE", ""),
        )

    def disconnect(self) -> None:
        """Close the Snowflake connection if it is open."""
        if self._conn:
            self._conn.close()
            self._conn = None

    # ── query ──────────────────────────────────────────────────────────────────

    def run_query(self, sql: str, params: tuple | None = None) -> list[dict[str, Any]]:
        """Execute *sql* and return results as a list of row-dicts.

        Parameters
        ----------
        sql:
            The SQL statement to execute (SELECT only; DML is not prevented but
            callers should use read-only warehouse roles).
        params:
            Optional positional bind parameters passed to the cursor.
        """
        if self._conn is None:
            self.connect()

        cursor = self._conn.cursor()  # type: ignore[union-attr]
        try:
            cursor.execute(sql, params)
            rows = cursor.fetchall()
            return rows_to_dicts(cursor.description, rows)
        finally:
            cursor.close()

    # ── context manager ────────────────────────────────────────────────────────

    def __enter__(self) -> "SnowflakeAgent":
        self.connect()
        return self

    def __exit__(self, *_: object) -> None:
        self.disconnect()
