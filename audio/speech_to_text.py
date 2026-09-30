"""
Speech-to-Text module using faster-whisper.
"""

import numpy as np
from typing import Optional
from faster_whisper import WhisperModel
import config


class SpeechToText:
    def __init__(
        self,
        model_size: str = config.STT_MODEL_SIZE,
        device: str = config.STT_DEVICE,
        compute_type: str = config.STT_COMPUTE_TYPE,
    ):
        self.model_size = model_size
        self.device = device
        self.compute_type = compute_type
        self.model: Optional[WhisperModel] = None

    def load_model(self) -> None:
        """Load the Whisper model if not already loaded."""
        if self.model is None:
            print(f"[STT] Loading faster-whisper model '{self.model_size}' on {self.device} ({self.compute_type})...")
            self.model = WhisperModel(
                self.model_size,
                device=self.device,
                compute_type=self.compute_type,
            )
            print("[STT] Whisper model ready.")

    def transcribe(self, audio_data: np.ndarray) -> str:
        """
        Transcribe a 16kHz mono float32 numpy audio array.

        Returns:
            str: Transcribed text, or empty string on failure/silence.
        """
        if self.model is None:
            self.load_model()

        if audio_data is None or len(audio_data) == 0:
            return ""

        try:
            # beam_size=5 for good accuracy, language="en" for fast English transcription
            segments, info = self.model.transcribe(
                audio_data,
                beam_size=5,
                language="en",
                condition_on_previous_text=False,
            )
            transcription = " ".join(segment.text.strip() for segment in segments).strip()
            return transcription
        except Exception as e:
            print(f"[STT Error]: Failed transcribing audio: {e}")
            return ""
