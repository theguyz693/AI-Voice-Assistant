"""
Lightweight local wake-word detector.

Architecture:
    Microphone (sounddevice)
        ↓
    RMS energy gate  (skip silent chunks — no STT on silence)
        ↓
    faster-whisper tiny.en  (same model already loaded by main)
        ↓
    String contains "novi"?
        ↓ YES
    Fire activate_callback(post_wake_audio)

The wake-word window is short (WAKE_WORD_CHUNK_S seconds).
If the user says "Novi, <command>" in a single breath, the audio
captured AFTER the wake word is passed back so main does not need
to re-record.  If the user pauses after "Novi", post_wake_audio is
None and main records fresh audio.

All STT is done with the SAME WhisperModel already loaded in memory
— no second model is created.
"""

import time
import threading
import numpy as np
import sounddevice as sd
from typing import Optional, Callable
import config


class WakeWordListener:
    """
    Continuously listens for the wake word in a background thread.
    Calls `activate_callback(post_wake_audio: Optional[np.ndarray])` when detected.
    """

    def __init__(self, stt_model, activate_callback: Callable):
        """
        Parameters
        ----------
        stt_model      : SpeechToText instance (model already loaded)
        activate_callback : called with optional post-wake audio ndarray
        """
        self._stt          = stt_model
        self._callback     = activate_callback
        self._running      = False
        self._thread: Optional[threading.Thread] = None
        self._paused       = False   # paused while main pipeline is active
        self._lock         = threading.Lock()

        self._chunk_frames = int(config.SAMPLE_RATE * config.WAKE_WORD_CHUNK_S)
        self._wake         = config.WAKE_WORD.lower().strip()

    # ── public ────────────────────────────────────────────────────────────────

    def start(self) -> None:
        """Start the background detection loop."""
        with self._lock:
            if self._running:
                return
            self._running = True
        self._thread = threading.Thread(target=self._loop, daemon=True)
        self._thread.start()
        print(f"[Wake] Listening for wake word: '{config.WAKE_WORD}'")

    def stop(self) -> None:
        with self._lock:
            self._running = False

    def pause(self) -> None:
        """Pause detection while the main pipeline is processing."""
        with self._lock:
            self._paused = True

    def resume(self) -> None:
        """Resume after main pipeline finishes."""
        with self._lock:
            self._paused = False

    # ── detection loop ────────────────────────────────────────────────────────

    def _loop(self) -> None:
        """Continuously record short windows and check for wake word."""
        while True:
            with self._lock:
                if not self._running:
                    break
                paused = self._paused

            if paused:
                time.sleep(0.1)
                continue

            try:
                chunk = self._record_chunk()
            except Exception as e:
                print(f"[Wake] Microphone error: {e}")
                time.sleep(0.5)
                continue

            if chunk is None:
                continue  # silent chunk, skip STT

            # Run STT on the short chunk
            try:
                text = self._stt.transcribe(chunk).lower().strip()
            except Exception:
                continue

            if not text:
                continue

            # Check for wake word
            if self._wake in text:
                print(f"[Wake] Wake word detected in: '{text}'")
                # Extract post-wake audio (text after "novi")
                post_wake_audio = self._extract_post_wake(text, chunk)
                # Pause self before firing callback
                with self._lock:
                    self._paused = True
                try:
                    self._callback(post_wake_audio)
                except Exception as e:
                    print(f"[Wake] Callback error: {e}")
                # Resume is called by main after pipeline finishes

    def _record_chunk(self) -> Optional[np.ndarray]:
        """
        Record WAKE_WORD_CHUNK_S seconds of audio.
        Returns None if the chunk is below the RMS gate (silence).
        """
        frames = sd.rec(
            self._chunk_frames,
            samplerate=config.SAMPLE_RATE,
            channels=config.CHANNELS,
            dtype="float32",
        )
        sd.wait()
        audio = frames.flatten()

        rms = float(np.sqrt(np.mean(audio ** 2)))
        if rms < config.WAKE_WORD_RMS_GATE:
            return None  # silent — skip STT

        return audio

    def _extract_post_wake(
        self, text: str, audio: np.ndarray
    ) -> Optional[np.ndarray]:
        """
        If the transcript contains content after the wake word (e.g.
        "novi open spotify"), return the approximate audio slice that
        corresponds to everything after "novi".

        Because we cannot do word-level timestamp alignment with tiny.en
        easily, we use a conservative heuristic: if meaningful text follows
        the wake word (> 4 chars after stripping "novi"), return the second
        half of the audio window.  Otherwise return None so main re-records.
        """
        idx = text.find(self._wake)
        if idx == -1:
            return None

        remainder = text[idx + len(self._wake):].strip().lstrip(",.:; ")

        if len(remainder) < 4:
            # User just said "Novi" — no command yet
            return None

        # Rough heuristic: command occupies the latter portion of the window
        half = len(audio) // 2
        post = audio[half:]
        return post if len(post) > config.SAMPLE_RATE * 0.3 else None
