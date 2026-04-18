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

@patch('elevenlabs_agent.client')
def test_text_to_audio_with_prefix(mock_client):
    mock_client.text_to_speech.convert.return_value = [b"bytes"]

    result = elevenlabs_agent.text_to_audio("world", prefix="Hello")

    assert result == b"bytes"
    mock_client.text_to_speech.convert.assert_called_once_with(
        voice_id=elevenlabs_agent.ELEVENLABS_VOICE_ID,
        output_format="mp3_44100_128",
        text="Hello world",
        model_id="eleven_turbo_v2",
    )

@patch('elevenlabs_agent.client')
def test_text_to_audio_returns_empty_on_error(mock_client):
    mock_client.text_to_speech.convert.side_effect = Exception("api failure")

    result = elevenlabs_agent.text_to_audio("Hello world")

    assert result == b""
