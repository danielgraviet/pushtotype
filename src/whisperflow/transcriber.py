"""Whisper transcription via faster-whisper."""

from __future__ import annotations

import logging
import time

import numpy as np
from faster_whisper import WhisperModel

try:
    import ctranslate2
except ImportError:
    ctranslate2 = None

logger = logging.getLogger(__name__)


def _resolve_device(device: str) -> tuple[str, str]:
    """Return (device, compute_type) resolving 'auto' to cuda or cpu."""
    if device != "auto":
        compute_type = "float16" if device == "cuda" else "int8"
        return device, compute_type

    if ctranslate2 and ctranslate2.get_supported_compute_types("cuda"):
        return "cuda", "float16"

    return "cpu", "int8"


class Transcriber:
    """Wraps a faster-whisper WhisperModel for single-call transcription."""

    def __init__(
        self,
        model_name: str = "base.en",
        device: str = "auto",
        compute_type: str = "float16",
    ) -> None:
        resolved_device, resolved_compute = _resolve_device(device)
        # If caller explicitly passed compute_type and device isn't auto, honour it
        if device != "auto":
            resolved_compute = compute_type

        self.device = resolved_device
        self.compute_type = resolved_compute
        self.model_name = model_name

        logger.info("Loading model %s on %s (%s)…", model_name, self.device, self.compute_type)
        t0 = time.perf_counter()
        self._model = WhisperModel(model_name, device=self.device, compute_type=self.compute_type)
        elapsed = time.perf_counter() - t0
        logger.info("Model loaded in %.2fs", elapsed)

    def transcribe(self, audio: np.ndarray) -> str:
        """Transcribe a float32 mono 16 kHz numpy array to text."""
        t0 = time.perf_counter()
        segments, _info = self._model.transcribe(audio, language="en")
        text = " ".join(seg.text for seg in segments).strip()
        elapsed = time.perf_counter() - t0
        logger.debug("Transcribed in %.2fs", elapsed)
        return text
