import io
import logging

logger = logging.getLogger(__name__)


def text_to_audio(text: str, prefix: str = "") -> bytes:
    full_text = f"{prefix} {text}".strip() if prefix else text
    try:
        from gtts import gTTS
        tts = gTTS(text=full_text[:5000], lang="en", slow=False)
        buf = io.BytesIO()
        tts.write_to_fp(buf)
        return buf.getvalue()
    except Exception as e:
        logger.warning(f"gTTS failed: {e}")
        return b""
