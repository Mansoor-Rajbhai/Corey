"""
Free, fully offline STT using faster-whisper — now with:
  - Wake word detection ("Corey") running continuously in the background
  - Auto-stop recording based on silence, no more press-Enter-to-stop

SETUP (one-time):
    pip install faster-whisper sounddevice numpy

USAGE (standalone test):
    python stt.py
"""

import time

import numpy as np
import sounddevice as sd
from faster_whisper import WhisperModel

MODEL_SIZE = "small"      # used for transcribing commands
SAMPLE_RATE = 16000        # whisper expects 16kHz audio

# Add any non-standard words here: names, brand names, jargon, etc.
CUSTOM_VOCAB = [
    "YouTube",
    "Hussaina",
    "Mansoor",
    "Corey",
    "Kamar Taj",
]


def warm_up_mic():
    """Opens and closes a throwaway stream so the OS audio device is fully
    initialized before the first real recording (fixes garbled/hallucinated
    first transcriptions caused by Windows audio device startup latency)."""
    with sd.InputStream(samplerate=SAMPLE_RATE, channels=1, dtype="float32"):
        sd.sleep(300)


# ---------------------------------------------------------------------------
# AUTO LISTEN (starts recording once it detects you speaking, stops once
# you go quiet again)
# ---------------------------------------------------------------------------

def record_until_silence(silence_threshold: float = 0.015, silence_duration: float = 0.8,
                          max_duration: float = 15.0, timeout: float = 8.0) -> np.ndarray:
    """
    Starts capturing audio immediately, but only counts it as your command
    once your volume crosses `silence_threshold` (i.e. you actually started
    talking). Auto-stops `silence_duration` seconds after you go quiet.

    `timeout` = how long to wait for you to start speaking at all before
    giving up and returning empty audio (goes back to wake word listening).

    NOTE: `silence_threshold` depends on your mic's noise floor. If it cuts
    you off mid-sentence, raise it slightly (e.g. 0.02-0.03). If it never
    stops in quiet rooms, lower it (e.g. 0.008-0.01).
    """
    frames = []
    silence_start = None
    speech_started = False
    start_time = time.time()

    def callback(indata, frame_count, time_info, status):
        frames.append(indata.copy())

    stream = sd.InputStream(samplerate=SAMPLE_RATE, channels=1, dtype="float32",
                             callback=callback)
    with stream:
        while True:
            sd.sleep(100)
            if not frames:
                continue

            volume = float(np.sqrt(np.mean(frames[-1] ** 2)))
            elapsed = time.time() - start_time

            if volume > silence_threshold:
                speech_started = True
                silence_start = None
            elif speech_started:
                if silence_start is None:
                    silence_start = time.time()
                elif time.time() - silence_start > silence_duration:
                    break

            if not speech_started and elapsed > timeout:
                break  # gave up waiting for you to start talking

            if elapsed > max_duration:
                break

    audio = np.concatenate(frames, axis=0).flatten()
    return audio


def transcribe(audio: np.ndarray, model: WhisperModel) -> str:
    hotwords_str = ", ".join(CUSTOM_VOCAB) if CUSTOM_VOCAB else None
    segments, info = model.transcribe(
        audio,
        language="en",
        beam_size=2,
        hotwords=hotwords_str,
        vad_filter=True,
        vad_parameters=dict(min_silence_duration_ms=300),
        condition_on_previous_text=False,
        no_speech_threshold=0.4,
    )
    text = " ".join(segment.text.strip() for segment in segments)
    return text


def main():
    """Standalone test: speak, it auto-detects start/stop, then transcribes."""
    print(f"Loading command model ({MODEL_SIZE})...")
    command_model = WhisperModel(MODEL_SIZE, device="cpu", compute_type="int8")
    print("Model loaded.\n")

    warm_up_mic()

    while True:
        print("Listening...")
        audio = record_until_silence()
        print("Transcribing...")
        text = transcribe(audio, command_model)
        print(f"\n>> {text}\n")


if __name__ == "__main__":
    main()