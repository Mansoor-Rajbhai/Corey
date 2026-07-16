"""
Free, fully offline STT using faster-whisper.
Push-to-talk style: press Enter to start recording, press Enter again to stop.

SETUP (one-time):
    pip install faster-whisper sounddevice numpy scipy

    First run will download the model (~150MB for "base", one-time, needs internet).
    After that, everything runs 100% offline.

USAGE:
    python stt.py
"""

import numpy as np
import sounddevice as sd
from faster_whisper import WhisperModel

MODEL_SIZE = "small"  # options: tiny, base, small, medium, large-v3
                       # bigger = more accurate but slower. "small" handles short
                       # commands and names much better than "base".
SAMPLE_RATE = 16000   # whisper expects 16kHz audio

# Add any non-standard words here: YouTube channel names, brand names, jargon, etc.
# This biases the model toward recognizing these specific words/phrases correctly.
CUSTOM_VOCAB = [
    "YouTube",
    "Hussaina",
    "Mansoor",
    "Corey",
    "Kamar Taj"
    # add your own here
]


def warm_up_mic():
    """Opens and closes a throwaway stream so the OS audio device is fully
    initialized before the first real recording (fixes garbled/hallucinated
    first transcriptions caused by Windows audio device startup latency)."""
    with sd.InputStream(samplerate=SAMPLE_RATE, channels=1, dtype="float32"):
        sd.sleep(300)


def record_audio() -> np.ndarray:
    input("Press Enter to start recording...")
    print("Recording... press Enter to stop.")

    frames = []

    def callback(indata, frame_count, time_info, status):
        frames.append(indata.copy())

    stream = sd.InputStream(
        samplerate=SAMPLE_RATE,
        channels=1,
        dtype="float32",
        callback=callback,
    )
    with stream:
        input()  # blocks until Enter is pressed again

    print("Stopped recording.")
    audio = np.concatenate(frames, axis=0).flatten()
    return audio


def transcribe(audio: np.ndarray, model: WhisperModel) -> str:
    hotwords_str = ", ".join(CUSTOM_VOCAB) if CUSTOM_VOCAB else None
    segments, info = model.transcribe(
        audio,
        language="en",
        beam_size=5,
        hotwords=hotwords_str,
        vad_filter=True,  # strips silence/noise so whisper doesn't hallucinate text
        vad_parameters=dict(min_silence_duration_ms=300),
        condition_on_previous_text=False,  # prevents one hallucination from biasing the next
        no_speech_threshold=0.4,  # more willing to say "nothing heard" instead of guessing
    )
    text = " ".join(segment.text.strip() for segment in segments)
    return text


def main():
    print(f"Loading Whisper model ({MODEL_SIZE})...")
    model = WhisperModel(MODEL_SIZE, device="cpu", compute_type="int8")
    print("Model loaded.\n")

    warm_up_mic()

    while True:
        audio = record_audio()
        print("Transcribing...")
        text = transcribe(audio, model)
        print(f"\n>> {text}\n")


if __name__ == "__main__":
    main()
