import pytest
from fastapi.testclient import TestClient
from main import app
import io
from unittest.mock import patch

client = TestClient(app)

def test_health():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok", "service": "DataNarrator"}

@patch('main.supabase_agent')
@patch('main.gemini_agent')
@patch('main.elevenlabs_agent')
def test_analyze(mock_elevenlabs, mock_gemini, mock_supabase):
    # Mock implementations
    mock_supabase.get_table_summary.return_value = {"summary": "test"}
    mock_supabase.log_upload.return_value = None

    mock_gemini.generate_insight.return_value = {"insight": "Mocked insight", "chart_data": None}
    mock_gemini.ERROR_INSIGHT = "Unable to generate insight."

    mock_elevenlabs.text_to_audio.return_value = b"mocked_audio_bytes"

    # Create a mock CSV
    csv_content = "col1,col2\nval1,val2\n"
    csv_file = io.BytesIO(csv_content.encode('utf-8'))

    response = client.post(
        "/analyze",
        files={"file": ("test.csv", csv_file, "text/csv")}
    )

    assert response.status_code == 200
    json_response = response.json()
    assert "insight" in json_response
    assert "audio_b64" in json_response
    assert "columns" in json_response
    assert json_response["insight"] == "Mocked insight"
    assert json_response["audio_b64"] is not None
    assert json_response["columns"] == ["col1", "col2"]

    mock_supabase.log_upload.assert_called_once()
    call_args = mock_supabase.log_upload.call_args[0]
    assert call_args[0].startswith("upload_")
    assert call_args[1] == 1
    assert call_args[2] == ["col1", "col2"]

@patch('main.gemini_agent')
@patch('main.elevenlabs_agent')
def test_followup(mock_elevenlabs, mock_gemini):
    mock_gemini.answer_followup.return_value = "Mocked followup answer"
    mock_elevenlabs.text_to_audio.return_value = b"mocked_audio_bytes"

    response = client.post(
        "/followup",
        json={"insight": "Original insight", "question": "Followup question?"}
    )

    assert response.status_code == 200
    json_response = response.json()
    assert "answer" in json_response
    assert "audio_b64" in json_response
    assert json_response["answer"] == "Mocked followup answer"
