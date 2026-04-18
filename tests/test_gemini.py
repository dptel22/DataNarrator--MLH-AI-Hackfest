import pytest
from unittest.mock import patch, MagicMock
import gemini_agent

@patch('gemini_agent.genai.GenerativeModel')
def test_generate_insight(mock_model_class):
    mock_model = MagicMock()
    mock_response = MagicMock()
    mock_response.text = "This is a mocked insight."
    mock_model.generate_content.return_value = mock_response
    mock_model_class.return_value = mock_model

    table_summary = {"col1": "val1", "col2": "val2"}
    result = gemini_agent.generate_insight(table_summary)

    assert isinstance(result, str)
    assert len(result) > 0
    assert result == "This is a mocked insight."

@patch('gemini_agent.genai.GenerativeModel')
def test_answer_followup(mock_model_class):
    mock_model = MagicMock()
    mock_response = MagicMock()
    mock_response.text = "This is a mocked answer."
    mock_model.generate_content.return_value = mock_response
    mock_model_class.return_value = mock_model

    insight = "Original insight"
    question = "Followup question?"
    result = gemini_agent.answer_followup(insight, question)

    assert isinstance(result, str)
    assert len(result) > 0
    assert result == "This is a mocked answer."
