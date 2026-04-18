import pandas as pd
from unittest.mock import MagicMock, patch

import supabase_agent


def test_normalize_column_name():
    assert supabase_agent._normalize_column_name("  Revenue ($)  ") == "revenue"
    assert supabase_agent._normalize_column_name("Total   Sales") == "total_sales"
    assert supabase_agent._normalize_column_name("A__B") == "a_b"


def test_create_supabase_client_requires_env(monkeypatch):
    monkeypatch.delenv("SUPABASE_URL", raising=False)
    monkeypatch.delenv("SUPABASE_KEY", raising=False)

    try:
        supabase_agent._create_supabase_client()
        assert False, "Expected ValueError when env vars are missing"
    except ValueError as exc:
        assert "SUPABASE_URL and SUPABASE_KEY" in str(exc)


@patch("supabase_agent.create_client")
def test_create_supabase_client_success(mock_create_client, monkeypatch):
    monkeypatch.setenv("SUPABASE_URL", "https://example.supabase.co")
    monkeypatch.setenv("SUPABASE_KEY", "secret")

    mock_client = MagicMock()
    mock_create_client.return_value = mock_client

    result = supabase_agent._create_supabase_client()

    assert result == mock_client
    mock_create_client.assert_called_once_with("https://example.supabase.co", "secret")


@patch("supabase_agent._create_supabase_client")
def test_ingest_csv_normalizes_and_inserts_records(mock_create_client):
    mock_client = MagicMock()
    mock_create_client.return_value = mock_client

    df = pd.DataFrame({
        " First Name ": ["Ada"],
        "Score(%)": [None],
    })

    result = supabase_agent.ingest_csv(df, "people")

    assert result == "people"
    mock_client.table.assert_called_once_with("people")
    inserted_records = mock_client.table.return_value.insert.call_args.args[0]
    assert inserted_records == [{"first_name": "Ada", "score": None}]
    mock_client.table.return_value.insert.return_value.execute.assert_called_once()


@patch("supabase_agent._create_supabase_client")
def test_ingest_csv_returns_empty_on_error(mock_create_client):
    mock_create_client.side_effect = RuntimeError("connection failed")

    df = pd.DataFrame({"a": [1]})
    result = supabase_agent.ingest_csv(df, "tbl")

    assert result == ""


def test_get_table_summary_shape():
    df = pd.DataFrame({"a": [1, 2], "b": ["x", "y"]})

    summary = supabase_agent.get_table_summary(df)

    assert summary["row_count"] == 2
    assert summary["columns"] == ["a", "b"]
    assert isinstance(summary["sample"], list)
    assert len(summary["sample"]) == 2
    assert "a" in summary["stats"]
