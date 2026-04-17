"""Unit tests for SnowflakeAgent."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

# Allow importing backend modules without installing the package
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "backend"))

from snowflake_agent import SnowflakeAgent  # noqa: E402
from utils import rows_to_dicts  # noqa: E402


# ── rows_to_dicts helper ───────────────────────────────────────────────────────


def test_rows_to_dicts_basic():
    description = [("NAME",), ("AGE",)]
    rows = [("Alice", 30), ("Bob", 25)]
    result = rows_to_dicts(description, rows)
    assert result == [{"name": "Alice", "age": 30}, {"name": "Bob", "age": 25}]


def test_rows_to_dicts_empty():
    assert rows_to_dicts([("COL",)], []) == []


# ── SnowflakeAgent ─────────────────────────────────────────────────────────────


@pytest.fixture()
def mock_env(monkeypatch):
    """Inject dummy Snowflake environment variables."""
    for key, value in {
        "SNOWFLAKE_ACCOUNT": "test_account",
        "SNOWFLAKE_USER": "test_user",
        "SNOWFLAKE_PASSWORD": "test_pass",
        "SNOWFLAKE_WAREHOUSE": "test_wh",
        "SNOWFLAKE_DATABASE": "test_db",
        "SNOWFLAKE_SCHEMA": "test_schema",
        "SNOWFLAKE_ROLE": "test_role",
    }.items():
        monkeypatch.setenv(key, value)


@patch("snowflake_agent.snowflake.connector.connect")
def test_run_query_returns_dicts(mock_connect, mock_env):
    """run_query should return a list of row dicts."""
    mock_cursor = MagicMock()
    mock_cursor.description = [("product",), ("revenue",)]
    mock_cursor.fetchall.return_value = [("Widget", 1000), ("Gadget", 750)]
    mock_connect.return_value.cursor.return_value = mock_cursor

    agent = SnowflakeAgent()
    agent.connect()
    results = agent.run_query("SELECT product, revenue FROM sales")

    assert results == [
        {"product": "Widget", "revenue": 1000},
        {"product": "Gadget", "revenue": 750},
    ]
    mock_cursor.execute.assert_called_once_with("SELECT product, revenue FROM sales", None)
    mock_cursor.close.assert_called_once()


@patch("snowflake_agent.snowflake.connector.connect")
def test_context_manager_calls_connect_and_disconnect(mock_connect, mock_env):
    """Using SnowflakeAgent as a context manager should connect and disconnect."""
    mock_conn = MagicMock()
    mock_connect.return_value = mock_conn
    mock_cursor = MagicMock()
    mock_cursor.description = []
    mock_cursor.fetchall.return_value = []
    mock_conn.cursor.return_value = mock_cursor

    with SnowflakeAgent() as agent:
        agent.run_query("SELECT 1")

    mock_conn.close.assert_called_once()


@patch("snowflake_agent.snowflake.connector.connect")
def test_run_query_with_params(mock_connect, mock_env):
    """Bind parameters should be forwarded to cursor.execute."""
    mock_cursor = MagicMock()
    mock_cursor.description = [("id",)]
    mock_cursor.fetchall.return_value = [(42,)]
    mock_connect.return_value.cursor.return_value = mock_cursor

    agent = SnowflakeAgent()
    agent.connect()
    results = agent.run_query("SELECT id FROM tbl WHERE id = %s", (42,))

    mock_cursor.execute.assert_called_once_with("SELECT id FROM tbl WHERE id = %s", (42,))
    assert results == [{"id": 42}]
