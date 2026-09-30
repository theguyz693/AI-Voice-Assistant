"""
Feedback tool for spoken (TTS) and console confirmation.
"""

import threading
import pyttsx3
import config


def _speak_thread(text: str):
    try:
        engine = pyttsx3.init()
        engine.setProperty("rate", 185)  # Slightly faster, snappy speaking rate
        engine.say(text)
        engine.runAndWait()
    except Exception as e:
        # Gracefully handle any TTS audio device or COM initialization error
        pass


def provide_feedback(message: str, spoken_text: str = None):
    """
    Print confirmation to console and optionally speak confirmation aloud.
    """
    print(f"\n[🤖 Assistant]: {message}")

    if config.ENABLE_TTS_FEEDBACK:
        phrase = spoken_text if spoken_text else message
        threading.Thread(target=_speak_thread, args=(phrase,), daemon=True).start()
