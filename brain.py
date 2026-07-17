"""
Corey — the brain (optimized: streams responses sentence-by-sentence into TTS).

Loop: record -> transcribe (Whisper) -> think (Ollama, streamed) -> speak (Piper)

Why streaming matters: without it, Corey stays silent for the entire time the
model is generating a reply. With it, Corey starts speaking the first
sentence the moment it's ready while later sentences are still being
generated — much lower perceived latency.

Run from the Corey/ root:
    python brain.py

Requires:
    pip install ollama
"""

import re
import sys
import os
import threading
import queue

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from ollama import chat
from STT.stt import (
    WhisperModel,
    warm_up_mic,
    record_until_silence,
    transcribe,
    MODEL_SIZE,
)
from TTS.tts import speak

MODEL_NAME = "qwen-3.5:4b"

# Keep the model loaded in memory between turns instead of Ollama unloading
# it after each call (avoids reload latency on every response).
KEEP_ALIVE = "30m"

# Cap how much conversation history gets sent each turn. Bigger history =
# slower responses since the model has to process more context every time.
MAX_HISTORY_MESSAGES = 20  # system prompt + last N turns

SYSTEM_PROMPT = """You are Corey, Mansoor's personal AI assistant — think Jarvis.

Speak the way Jarvis does: calm, precise, a little dry, never chatty.
Rules:
- Keep replies to 1-2 short sentences. Never ramble.
- No filler like "I'd be happy to" or "Great question!". Just answer.
- No markdown, no bullet points, no lists — you're spoken out loud.
- State facts plainly. Only add detail if directly asked for more.
- You can be quietly witty, but never goofy or overly enthusiastic.
- Address him as "Mansoor" or "sir" occasionally, not every line.
"""

# Matches end of a sentence: . ! ? followed by a space or end of string
SENTENCE_END = re.compile(r"(?<=[.!?])\s+")

# ---------------------------------------------------------------------------
# BACKGROUND TTS WORKER
# speak() blocks while audio plays. Running it on its own thread means the
# main thread can keep printing/streaming tokens without waiting on it —
# sentences get queued and spoken in order, but never hold up the printing.
# ---------------------------------------------------------------------------

_speech_queue = queue.Queue()


def _tts_worker():
    while True:
        sentence = _speech_queue.get()
        try:
            speak(sentence)
        finally:
            _speech_queue.task_done()


threading.Thread(target=_tts_worker, daemon=True).start()


def queue_speech(sentence: str):
    _speech_queue.put(sentence)


def wait_for_speech_to_finish():
    """Blocks until every queued sentence has actually finished playing."""
    _speech_queue.join()


def trim_history(messages: list) -> list:
    """Keep the system prompt plus only the most recent turns."""
    if len(messages) <= MAX_HISTORY_MESSAGES:
        return messages
    return [messages[0]] + messages[-(MAX_HISTORY_MESSAGES - 1):]


def ask_corey_streamed(messages: list) -> str:
    """
    Streams the model's reply token-by-token. Each token is printed to the
    console the instant it arrives (real typing effect). Separately, once a
    full sentence has accumulated, it's spoken immediately — TTS needs whole
    words/sentences to sound right, so it can't go as granular as printing.
    Returns the full reply text once generation is done, for history.
    """
    buffer = ""
    full_reply = ""
    first_token = True

    stream = chat(
        model=MODEL_NAME,
        messages=messages,
        stream=True,
        think=False,
        keep_alive=KEEP_ALIVE,
    )

    print("Corey: ", end="", flush=True)

    for chunk in stream:
        token = chunk["message"]["content"]
        if not token:
            continue

        print(token, end="", flush=True)  # prints instantly, token by token

        buffer += token
        full_reply += token

        # Whenever we've got at least one full sentence, queue it for
        # speech and keep only the leftover partial sentence in the buffer.
        parts = SENTENCE_END.split(buffer)
        if len(parts) > 1:
            *complete, buffer = parts
            for sentence in complete:
                sentence = sentence.strip()
                if sentence:
                    queue_speech(sentence)

    print()  # newline after streaming finishes

    # Queue whatever's left over (final sentence with no trailing space/EOF)
    leftover = buffer.strip()
    if leftover:
        queue_speech(leftover)

    return full_reply.strip()


def main():
    print(f"Loading Whisper model ({MODEL_SIZE})...")
    stt_model = WhisperModel(MODEL_SIZE, device="cpu", compute_type="int8")
    print("Model loaded.\n")
    warm_up_mic()

    messages = [{"role": "system", "content": SYSTEM_PROMPT}]

    print("Corey is online. Listening...\n")

    while True:
        audio = record_until_silence()
        print("Transcribing...")
        user_text = transcribe(audio, stt_model)
        if not user_text.strip():
            print("(heard nothing, try again)\n")
            continue
        print(f"You: {user_text}")

        messages.append({"role": "user", "content": user_text})
        reply = ask_corey_streamed(messages)
        messages.append({"role": "assistant", "content": reply})
        messages[:] = trim_history(messages)

        wait_for_speech_to_finish()  # don't start listening again mid-speech
        print()


if __name__ == "__main__":
    main()