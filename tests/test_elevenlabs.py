import pytest
from unittest.mock import patch, MagicMock
import elevenlabs_agent

@patch('elevenlabs_agent.client')
def test_text_to_audio(mock_client):
    mock_audio_generator = [b"audio", b"data"]
    mock_client.text_to_speech.convert.return_value = mock_audio_generator

    result = elevenlabs_agent.text_to_audio("Hello world")

    assert isinstance(result, bytes)
    assert len(result) > 0
    assert result == b"audiodata"
