"""ElevenLabs agent — converts narrative text to speech and returns audio bytes."""

from __future__ import annotations

from elevenlabs.client import ElevenLabs
from elevenlabs import VoiceSettings

from utils import get_env

_DEFAULT_MODEL = "eleven_multilingual_v2"


class ElevenLabsAgent:
    """Wraps the ElevenLabs Python SDK to synthesize speech from text."""

    def __init__(self, voice_id: str | None = None, model_id: str = _DEFAULT_MODEL) -> None:
        self._client = ElevenLabs(api_key=get_env("ELEVENLABS_API_KEY"))
        self._voice_id = voice_id or get_env("ELEVENLABS_VOICE_ID")
        self._model_id = model_id

    def synthesize(self, text: str) -> bytes:
        """Convert *text* to speech and return raw MP3 audio bytes.

        Parameters
        ----------
        text:
            The narrative text to synthesize (max ~5 000 characters).
        """
        audio_iter = self._client.text_to_speech.convert(
            voice_id=self._voice_id,
            text=text,
            model_id=self._model_id,
            voice_settings=VoiceSettings(
                stability=0.5,
                similarity_boost=0.75,
                style=0.0,
                use_speaker_boost=True,
            ),
        )
        return b"".join(audio_iter)
