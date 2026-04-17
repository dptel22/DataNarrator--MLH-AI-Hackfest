"""Unit tests for GeminiAgent."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "backend"))

from gemini_agent import GeminiAgent  # noqa: E402
from utils import format_table  # noqa: E402


# ── format_table helper ────────────────────────────────────────────────────────


def test_format_table_empty():
    assert format_table([]) == "(no data)"


def test_format_table_basic():
    records = [{"product": "Widget", "revenue": 1000}]
    table = format_table(records)
    assert "product" in table
    assert "Widget" in table
    assert "1000" in table


def test_format_table_multi_row():
    records = [
        {"name": "Alice", "score": 95},
        {"name": "Bob", "score": 87},
    ]
    table = format_table(records)
    assert "Alice" in table
    assert "Bob" in table
    assert "95" in table


# ── GeminiAgent ────────────────────────────────────────────────────────────────


@patch("gemini_agent.genai.Client")
def test_generate_narrative_calls_model(mock_client_cls, monkeypatch):
    """generate_narrative should call the underlying Gemini model and return text."""
    monkeypatch.setenv("GEMINI_API_KEY", "fake-key")

    mock_response = MagicMock()
    mock_response.text = "  Widget drove the highest revenue last quarter.  "
    mock_client = MagicMock()
    mock_client.models.generate_content.return_value = mock_response
    mock_client_cls.return_value = mock_client

    agent = GeminiAgent()
    records = [{"product": "Widget", "revenue": 1000}]
    narrative = agent.generate_narrative(records, "What was the top product?")

    assert narrative == "Widget drove the highest revenue last quarter."
    mock_client.models.generate_content.assert_called_once()

    # Verify the prompt includes the question and table content
    call_kwargs = mock_client.models.generate_content.call_args[1]
    assert "What was the top product?" in call_kwargs["contents"]
    assert "Widget" in call_kwargs["contents"]


@patch("gemini_agent.genai.Client")
def test_generate_narrative_empty_records(mock_client_cls, monkeypatch):
    """generate_narrative should handle empty record sets gracefully."""
    monkeypatch.setenv("GEMINI_API_KEY", "fake-key")

    mock_response = MagicMock()
    mock_response.text = "No data was returned for this query."
    mock_client = MagicMock()
    mock_client.models.generate_content.return_value = mock_response
    mock_client_cls.return_value = mock_client

    agent = GeminiAgent()
    narrative = agent.generate_narrative([], "Any question?")

    assert narrative == "No data was returned for this query."
    call_kwargs = mock_client.models.generate_content.call_args[1]
    assert "(no data)" in call_kwargs["contents"]
