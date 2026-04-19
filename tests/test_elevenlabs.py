import pytest
from unittest.mock import patch, MagicMock
import io
import tts_agent as elevenlabs_agent


@patch("tts_agent.gTTS", create=True)
def test_text_to_audio(mock_gtts_class):
    # Mock gTTS instance: write_to_fp writes fake MP3 bytes into the buffer
    mock_tts = MagicMock()
    def fake_write(buf):
        buf.write(b"fake_mp3_audio")
    mock_tts.write_to_fp.side_effect = fake_write
    mock_gtts_class.return_value = mock_tts

    with patch.dict('sys.modules', {'gtts': MagicMock(gTTS=mock_gtts_class)}):
        result = elevenlabs_agent.text_to_audio("Hello world")

    assert isinstance(result, bytes)
    assert len(result) > 0


def test_text_to_audio_with_prefix():
    """Prefix is prepended before passing to gTTS."""
    captured = {}

    def fake_gtts(text, lang, slow):
        captured['text'] = text
        m = MagicMock()
        m.write_to_fp.side_effect = lambda buf: buf.write(b"audio")
        return m

    with patch.dict('sys.modules', {'gtts': MagicMock(gTTS=fake_gtts)}):
        result = elevenlabs_agent.text_to_audio("world", prefix="Hello")

    assert captured['text'] == "Hello world"
    assert result == b"audio"


def test_text_to_audio_gtts_failure_returns_empty():
    """If gTTS raises, the function returns b'' without crashing."""
    def bad_gtts(*args, **kwargs):
        raise RuntimeError("network error")

    with patch.dict('sys.modules', {'gtts': MagicMock(gTTS=bad_gtts)}):
        result = elevenlabs_agent.text_to_audio("Hello")

    assert result == b""
