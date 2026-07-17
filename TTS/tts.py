"""
Free, fully offline TTS using Piper — streams audio directly to speakers,
no file ever hits disk.

SETUP (one-time):
    pip install piper-tts --break-system-packages
    python -m piper.download_voices en_US-amy-medium

USAGE:
    python tts.py "Hello, this is a test."

    Or import and call speak() from brain.py:
        from TTS.tts import speak
        speak("Hello there.")
"""

import os
import sys
import numpy as np
import sounddevice as sd
from piper import PiperVoice

# Absolute path, anchored to this file's location — works no matter what
# directory the script is run from (e.g. brain.py running from Corey/ root)
VOICE_MODEL = os.path.join(os.path.dirname(os.path.abspath(__file__)), "en_US-amy-medium.onnx")

# Loaded once, reused across calls (brain.py will call speak() a lot)
_voice = None


def get_voice() -> PiperVoice:
    global _voice
    if _voice is None:
        _voice = PiperVoice.load(VOICE_MODEL)
    return _voice


def speak(text: str):
    """Synthesize and play text in real time, chunk by chunk. No file saved."""
    if not text or not text.strip():
        return

    voice = get_voice()
    sample_rate = voice.config.sample_rate

    stream = sd.OutputStream(samplerate=sample_rate, channels=1, dtype="int16")
    stream.start()
    try:
        for chunk in voice.synthesize(text):
            # chunk.audio_int16_bytes is raw PCM for this piece of audio
            audio = np.frombuffer(chunk.audio_int16_bytes, dtype=np.int16)
            stream.write(audio)
    finally:
        stream.stop()
        stream.close()


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print('Usage: python tts.py "your text here"')
        sys.exit(1)

    speak(sys.argv[1])