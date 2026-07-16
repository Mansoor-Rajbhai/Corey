"""
Free, fully offline TTS using Piper.
Voice: en_US-lessac-medium (clean, professional American female voice)

SETUP (one-time):
    pip install piper-tts --break-system-packages

    Then download the voice model (only needs internet this one time):
    python -m piper.download_voices en_US-lessac-medium

USAGE:
    python tts.py "Hello, this is a test." output.wav
    python tts.py "Hello, this is a test."          # plays "output.wav" by default
"""

import os
import sys
import wave
import platform
import subprocess
from piper import PiperVoice

VOICE_MODEL = "en_US-amy-medium.onnx"  # swap for another downloaded voice if you like


def speak(text: str, out_path: str = "output.wav", play: bool = True):
    voice = PiperVoice.load(VOICE_MODEL)

    with wave.open(out_path, "wb") as wav_file:
        voice.synthesize_wav(text, wav_file)

    print(f"Saved audio to {out_path}")

    if play:
        play_audio(out_path)


def play_audio(path: str):
    system = platform.system()
    try:
        if system == "Windows":
            os.startfile(path)  # opens with default player (e.g. Media Player/browser)
        elif system == "Darwin":
            subprocess.run(["afplay", path])
        else:
            subprocess.run(["aplay", path])
    except Exception as e:
        print(f"Could not auto-play audio ({e}). Open {path} manually to listen.")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print('Usage: python tts.py "your text here" [output.wav]')
        sys.exit(1)

    text = sys.argv[1]
    out_path = sys.argv[2] if len(sys.argv) > 2 else "output.wav"
    speak(text, out_path)