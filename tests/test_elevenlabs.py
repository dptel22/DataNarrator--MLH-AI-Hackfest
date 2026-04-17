"""Unit tests for ElevenLabsAgent."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "backend"))

from elevenlabs_agent import ElevenLabsAgent  # noqa: E402


# ── ElevenLabsAgent ────────────────────────────────────────────────────────────


@patch("elevenlabs_agent.ElevenLabs")
def test_synthesize_returns_bytes(mock_elevenlabs_cls, monkeypatch):
    """synthesize() should concatenate iterator chunks into bytes."""
    monkeypatch.setenv("ELEVENLABS_API_KEY", "fake-key")
    monkeypatch.setenv("ELEVENLABS_VOICE_ID", "test-voice-id")

    # Simulate the SDK returning an iterable of byte chunks
    mock_client = MagicMock()
    mock_client.text_to_speech.convert.return_value = iter([b"chunk1", b"chunk2"])
    mock_elevenlabs_cls.return_value = mock_client

    agent = ElevenLabsAgent()
    result = agent.synthesize("Hello, world!")

    assert result == b"chunk1chunk2"
    mock_client.text_to_speech.convert.assert_called_once()


@patch("elevenlabs_agent.ElevenLabs")
def test_synthesize_passes_text_to_sdk(mock_elevenlabs_cls, monkeypatch):
    """synthesize() must pass the text argument through to the SDK."""
    monkeypatch.setenv("ELEVENLABS_API_KEY", "fake-key")
    monkeypatch.setenv("ELEVENLABS_VOICE_ID", "test-voice-id")

    mock_client = MagicMock()
    mock_client.text_to_speech.convert.return_value = iter([b"audio"])
    mock_elevenlabs_cls.return_value = mock_client

    agent = ElevenLabsAgent()
    agent.synthesize("This is a test narrative.")

    call_kwargs = mock_client.text_to_speech.convert.call_args[1]
    assert call_kwargs.get("text") == "This is a test narrative."


@patch("elevenlabs_agent.ElevenLabs")
def test_synthesize_uses_voice_id_from_env(mock_elevenlabs_cls, monkeypatch):
    """The voice_id should come from the ELEVENLABS_VOICE_ID env var by default."""
    monkeypatch.setenv("ELEVENLABS_API_KEY", "fake-key")
    monkeypatch.setenv("ELEVENLABS_VOICE_ID", "env-voice-123")

    mock_client = MagicMock()
    mock_client.text_to_speech.convert.return_value = iter([b"data"])
    mock_elevenlabs_cls.return_value = mock_client

    agent = ElevenLabsAgent()
    agent.synthesize("Narrative text.")

    call_kwargs = mock_client.text_to_speech.convert.call_args[1]
    assert call_kwargs.get("voice_id") == "env-voice-123"


@patch("elevenlabs_agent.ElevenLabs")
def test_synthesize_uses_explicit_voice_id(mock_elevenlabs_cls, monkeypatch):
    """An explicit voice_id passed to the constructor should override the env var."""
    monkeypatch.setenv("ELEVENLABS_API_KEY", "fake-key")
    monkeypatch.setenv("ELEVENLABS_VOICE_ID", "env-voice-123")

    mock_client = MagicMock()
    mock_client.text_to_speech.convert.return_value = iter([b"data"])
    mock_elevenlabs_cls.return_value = mock_client

    agent = ElevenLabsAgent(voice_id="explicit-voice-456")
    agent.synthesize("Narrative text.")

    call_kwargs = mock_client.text_to_speech.convert.call_args[1]
    assert call_kwargs.get("voice_id") == "explicit-voice-456"
