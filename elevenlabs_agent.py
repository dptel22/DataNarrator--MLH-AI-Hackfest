import logging
import os
from elevenlabs import ElevenLabs

logger = logging.getLogger(__name__)

def text_to_audio(text: str, prefix: str = "") -> bytes:
    full_text = f"{prefix} {text}".strip() if prefix else text
    api_key = os.getenv("ELEVENLABS_API_KEY")
    voice_id = os.getenv("ELEVENLABS_VOICE_ID", "21m00Tcm4TthDqHBiM3H") # Default voice

    if not api_key:
        logger.warning("ELEVENLABS_API_KEY not found in environment.")
        return b""

    try:
        client = ElevenLabs(api_key=api_key)
        audio_generator = client.generate(
            text=full_text[:5000],
            voice=voice_id,
            model="eleven_flash_v1"
        )
        # client.generate returns an iterator of bytes
        audio_bytes = b"".join(audio_generator)
        return audio_bytes
    except Exception as e:
        logger.error(f"ElevenLabs failed: {e}")
        return b""
