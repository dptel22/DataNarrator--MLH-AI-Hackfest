import os
from dotenv import load_dotenv
load_dotenv()

print("ELEVENLABS_API_KEY loaded:", bool(os.getenv("ELEVENLABS_API_KEY")))
print("ELEVENLABS_VOICE_ID loaded:", os.getenv("ELEVENLABS_VOICE_ID", "NOT SET"))

from elevenlabs_agent import text_to_audio

print("Calling text_to_audio with test string...")
result = text_to_audio("Hello, this is a test of DataNarrator voice generation.")

print("Result type:", type(result))
print("Result length in bytes:", len(result))

if len(result) == 0:
    print("FAIL — ElevenLabs returned empty bytes. Check API key and quota.")
else:
    with open("test_output.mp3", "wb") as f:
        f.write(result)
    print("SUCCESS — Audio saved to test_output.mp3. Open it and confirm voice plays.")
