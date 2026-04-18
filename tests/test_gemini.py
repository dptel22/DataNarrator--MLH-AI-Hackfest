from unittest.mock import patch, MagicMock
import gemini_agent

@patch('gemini_agent.genai.GenerativeModel')
def test_generate_insight_parses_json(mock_model_class):
    mock_model = MagicMock()
    mock_response = MagicMock()
    mock_response.text = '{"insight":"This is a mocked insight.","chart":{"type":"bar","title":"T","labels":["a"],"values":[1]}}'
    mock_model.generate_content.return_value = mock_response
    mock_model_class.return_value = mock_model

    table_summary = {"row_count": 1, "columns": ["col1"], "sample": [], "stats": {}}
    result = gemini_agent.generate_insight(table_summary)

    assert isinstance(result, dict)
    assert result["insight"] == "This is a mocked insight."
    assert result["chart"]["type"] == "bar"

@patch('gemini_agent.genai.GenerativeModel')
def test_generate_insight_strips_markdown_json_block(mock_model_class):
    mock_model = MagicMock()
    mock_response = MagicMock()
    mock_response.text = '```json\n{"insight":"From markdown","chart":{"type":"pie","title":"T","labels":["x"],"values":[100]}}\n```'
    mock_model.generate_content.return_value = mock_response
    mock_model_class.return_value = mock_model

    result = gemini_agent.generate_insight({"row_count": 2, "columns": ["a"], "sample": [], "stats": {}})

    assert result["insight"] == "From markdown"
    assert result["chart"]["type"] == "pie"

@patch('gemini_agent.genai.GenerativeModel')
def test_generate_insight_returns_fallback_on_error(mock_model_class):
    mock_model = MagicMock()
    mock_model.generate_content.side_effect = Exception("boom")
    mock_model_class.return_value = mock_model

    result = gemini_agent.generate_insight({"row_count": 1, "columns": [], "sample": [], "stats": {}})

    assert result == {"insight": "Unable to generate insight.", "chart": None}

@patch('gemini_agent.genai.GenerativeModel')
def test_answer_followup(mock_model_class):
    mock_model = MagicMock()
    mock_response = MagicMock()
    mock_response.text = " This is a mocked answer. "
    mock_model.generate_content.return_value = mock_response
    mock_model_class.return_value = mock_model

    insight = "Original insight"
    question = "Followup question?"
    result = gemini_agent.answer_followup(insight, question)

    assert isinstance(result, str)
    assert len(result) > 0
    assert result == "This is a mocked answer."

@patch('gemini_agent.genai.GenerativeModel')
def test_answer_followup_returns_empty_on_error(mock_model_class):
    mock_model = MagicMock()
    mock_model.generate_content.side_effect = Exception("failed")
    mock_model_class.return_value = mock_model

    result = gemini_agent.answer_followup("insight", "question")

    assert result == ""
