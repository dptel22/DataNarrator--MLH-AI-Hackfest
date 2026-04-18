import pytest
from fastapi.testclient import TestClient
from main import app
import io
from unittest.mock import patch, MagicMock

client = TestClient(app)

def test_health():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}

@patch('main.supabase_agent')
@patch('main.gemini_agent')
@patch('main.elevenlabs_agent')
@patch('main.uuid.uuid4')
def test_analyze(mock_uuid4, mock_elevenlabs, mock_gemini, mock_supabase):
    mock_uuid = MagicMock()
    mock_uuid.hex = "abcdef1234567890"
    mock_uuid4.return_value = mock_uuid

    # Mock implementations
    mock_supabase.ingest_csv.return_value = "upload_abcdef12"
    mock_supabase.get_table_summary.return_value = {"row_count": 1, "columns": ["col1", "col2"], "sample": [], "stats": {}}

    mock_gemini.generate_insight.return_value = {
        "insight": "Mocked insight",
        "chart": {"type": "bar", "title": "T", "labels": ["val1"], "values": [1]},
    }

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
    assert "chart_data" in json_response
    assert "columns" in json_response
    assert json_response["insight"] == "Mocked insight"
    assert json_response["columns"] == ["col1", "col2"]
    assert json_response["row_count"] == 1
    assert json_response["table_name"] == "upload_abcdef12"

@pytest.mark.parametrize("filename,content_type", [
    ("test.txt", "text/plain"),
    ("test.xlsx", "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"),
    ("test.json", "application/json"),
    ("test", "application/octet-stream"),
])
def test_analyze_rejects_non_csv_file(filename, content_type):
    uploaded_file = io.BytesIO(b"not,a,csv")
    response = client.post("/analyze", files={"file": (filename, uploaded_file, content_type)})

    assert response.status_code == 400
    assert response.json()["detail"] == "Only CSV files are allowed."

@patch('main.supabase_agent')
def test_analyze_returns_500_on_processing_error(mock_supabase):
    mock_supabase.ingest_csv.side_effect = RuntimeError("ingest failed")

    csv_file = io.BytesIO(b"col1\nval1\n")
    response = client.post("/analyze", files={"file": ("test.csv", csv_file, "text/csv")})

    assert response.status_code == 500
    assert response.json()["detail"] == "ingest failed"

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

@patch('main.gemini_agent')
def test_followup_returns_500_when_answer_empty(mock_gemini):
    mock_gemini.answer_followup.return_value = ""

    response = client.post(
        "/followup",
        json={"insight": "Original insight", "question": "Followup question?"}
    )

    assert response.status_code == 500
    assert isinstance(response.json()["detail"], str)
    assert response.json()["detail"]
