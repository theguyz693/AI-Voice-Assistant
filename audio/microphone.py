"""
Microphone input and audio recording with voice activity / silence detection.
"""

import time
import threading
import numpy as np
import sounddevice as sd
from typing import Optional, Callable
import config


class MicrophoneRecorder:
    def __init__(
        self,
        sample_rate: int = config.SAMPLE_RATE,
        channels: int = config.CHANNELS,
        chunk_size: int = config.CHUNK_SIZE,
        silence_threshold: float = config.SILENCE_THRESHOLD,
        silence_duration: float = config.SILENCE_DURATION,
        max_duration: float = config.MAX_RECORD_SECONDS,
    ):
        self.sample_rate = sample_rate
        self.channels = channels
        self.chunk_size = chunk_size
        self.silence_threshold = silence_threshold
        self.silence_duration = silence_duration
        self.max_duration = max_duration

        self._is_recording = False
        self._stop_requested = False
        self._lock = threading.Lock()

    @property
    def is_recording(self) -> bool:
        with self._lock:
            return self._is_recording

    def stop(self) -> None:
        """Signal recording to stop immediately."""
        with self._lock:
            self._stop_requested = True

    def record_phrase(
        self,
        on_start_listening: Optional[Callable[[], None]] = None,
        on_speech_started: Optional[Callable[[], None]] = None,
    ) -> Optional[np.ndarray]:
        """
        Records audio from the default microphone until silence is detected
        after speech or until max_duration is reached / manual stop is requested.

        Returns:
            np.ndarray: Audio data as float32 array, or None if no speech detected.
        """
        with self._lock:
            if self._is_recording:
                return None
            self._is_recording = True
            self._stop_requested = False

        audio_chunks = []
        speech_detected = False
        silence_start_time = None
        start_time = time.time()

        if on_start_listening:
            on_start_listening()

        try:
            with sd.InputStream(
                samplerate=self.sample_rate,
                channels=self.channels,
                dtype="float32",
                blocksize=self.chunk_size,
            ) as stream:
                while True:
                    # Check manual stop request
                    with self._lock:
                        if self._stop_requested:
                            break

                    chunk, overflowed = stream.read(self.chunk_size)
                    audio_chunks.append(chunk)

                    # Compute RMS energy of this chunk
                    rms = np.sqrt(np.mean(chunk**2))
                    current_time = time.time()
                    elapsed = current_time - start_time

                    if not speech_detected:
                        if rms >= self.silence_threshold:
                            speech_detected = True
                            silence_start_time = None
                            if on_speech_started:
                                on_speech_started()
                        elif elapsed > self.max_duration:
                            # Waited too long with no speech detected
                            break
                    else:
                        # Speech was previously detected; now monitor for trailing silence
                        if rms < self.silence_threshold:
                            if silence_start_time is None:
                                silence_start_time = current_time
                            elif current_time - silence_start_time >= self.silence_duration:
                                # Silence threshold reached after speaking
                                break
                        else:
                            # Still speaking or speech resumed
                            silence_start_time = None

                        if elapsed >= self.max_duration:
                            break

        except Exception as e:
            print(f"[Microphone Error]: Failed reading from microphone: {e}")
            return None
        finally:
            with self._lock:
                self._is_recording = False
                self._stop_requested = False

        if not audio_chunks or not speech_detected:
            return None

        # Concatenate and flatten all recorded chunks into single 1D float32 array
        full_audio = np.concatenate(audio_chunks, axis=0).flatten()
        return full_audio
