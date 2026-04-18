import logging
import os
from dotenv import load_dotenv
from elevenlabs.client import ElevenLabs

load_dotenv()

ELEVENLABS_API_KEY = os.getenv("ELEVENLABS_API_KEY")
# Sarah (EXAVITQu4vr4xnSDxMaL) — free premade voice, confirmed working on free tier API
# Rachel (21m00Tcm4TlvDq8ikWAM) is a library voice, requires paid plan via API
ELEVENLABS_VOICE_ID = os.getenv("ELEVENLABS_VOICE_ID", "EXAVITQu4vr4xnSDxMaL")
logger = logging.getLogger(__name__)

client = ElevenLabs(api_key=ELEVENLABS_API_KEY) if ELEVENLABS_API_KEY else None

def text_to_audio(text: str, prefix: str = "") -> bytes:
    full_text = f"{prefix} {text}".strip() if prefix else text

    if client is None:
        logger.warning("ELEVENLABS_API_KEY is missing; skipping audio generation.")
        return b""

    try:
        audio_generator = client.text_to_speech.convert(
            voice_id=ELEVENLABS_VOICE_ID,
            output_format="mp3_44100_128",
            text=full_text,
            model_id="eleven_turbo_v2",
        )

        audio_bytes = b"".join([chunk for chunk in audio_generator])
        return audio_bytes
    except Exception as e:
        print(f"Error in text_to_audio: {e}")
        return b""
