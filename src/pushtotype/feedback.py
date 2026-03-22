"""Audio feedback tones for recording start/stop/error."""

from __future__ import annotations

import wave
import logging
from pathlib import Path

import numpy as np
import sounddevice as sd

logger = logging.getLogger(__name__)

SAMPLE_RATE = 44100

_SOUNDS_DIR = Path(__file__).parent / "sounds"
_BUNDLED_START = _SOUNDS_DIR / "start.wav"
_BUNDLED_STOP = _SOUNDS_DIR / "stop.wav"


def _make_tone(
    freq: float,
    duration_ms: int,
    volume: float = 0.4,
    fade_ms: int = 10,
) -> np.ndarray:
    """Generate a sine-wave tone with a short fade in/out envelope."""
    n_samples = int(SAMPLE_RATE * duration_ms / 1000)
    t = np.linspace(0, duration_ms / 1000, n_samples, endpoint=False)
    wave = np.sin(2 * np.pi * freq * t).astype(np.float32) * volume

    fade_n = min(int(SAMPLE_RATE * fade_ms / 1000), n_samples // 4)
    if fade_n > 0:
        wave[:fade_n] *= np.linspace(0.0, 1.0, fade_n, dtype=np.float32)
        wave[-fade_n:] *= np.linspace(1.0, 0.0, fade_n, dtype=np.float32)

    return wave


def _make_chirp(
    freq_start: float,
    freq_end: float,
    duration_ms: int,
    volume: float = 0.4,
    fade_ms: int = 8,
) -> np.ndarray:
    """Generate a linear frequency sweep (chirp)."""
    n_samples = int(SAMPLE_RATE * duration_ms / 1000)
    t = np.linspace(0, duration_ms / 1000, n_samples, endpoint=False)
    # Instantaneous phase for linear chirp
    phase = 2 * np.pi * (freq_start * t + (freq_end - freq_start) / (2 * duration_ms / 1000) * t**2)
    wave = np.sin(phase).astype(np.float32) * volume

    fade_n = min(int(SAMPLE_RATE * fade_ms / 1000), n_samples // 4)
    if fade_n > 0:
        wave[:fade_n] *= np.linspace(0.0, 1.0, fade_n, dtype=np.float32)
        wave[-fade_n:] *= np.linspace(1.0, 0.0, fade_n, dtype=np.float32)

    return wave


def _make_double(
    freq_low: float,
    freq_high: float,
    note_ms: int,
    gap_ms: int,
    volume: float,
    ascending: bool,
) -> np.ndarray:
    """Two quick notes with a small gap."""
    first_freq, second_freq = (freq_low, freq_high) if ascending else (freq_high, freq_low)
    note1 = _make_tone(first_freq, note_ms, volume=volume)
    silence = np.zeros(int(SAMPLE_RATE * gap_ms / 1000), dtype=np.float32)
    note2 = _make_tone(second_freq, note_ms, volume=volume)
    return np.concatenate([note1, silence, note2])


def _load_wav(path: str) -> tuple[np.ndarray, int] | None:
    """Load a WAV file and return (float32 array, sample_rate), or None on failure."""
    try:
        with wave.open(path, "rb") as wf:
            n_channels = wf.getnchannels()
            sampwidth = wf.getsampwidth()
            framerate = wf.getframerate()
            frames = wf.readframes(wf.getnframes())

        dtype_map = {1: np.int8, 2: np.int16, 4: np.int32}
        dtype = dtype_map.get(sampwidth)
        if dtype is None:
            logger.warning("Unsupported WAV sample width: %d bytes", sampwidth)
            return None

        audio = np.frombuffer(frames, dtype=dtype).astype(np.float32)
        audio /= float(np.iinfo(dtype).max)

        if n_channels > 1:
            audio = audio.reshape(-1, n_channels).mean(axis=1)

        return audio, framerate
    except Exception as exc:
        logger.warning("Could not load custom sound %r: %s", path, exc)
        return None


def _play_custom(path: str, volume: float) -> bool:
    """Play a WAV file at the given volume. Returns False if it couldn't be loaded."""
    result = _load_wav(path)
    if result is None:
        return False
    audio, rate = result
    sd.play(audio * volume, samplerate=rate, blocking=False)
    return True


def play_start_sound(
    volume: float = 0.4,
    enabled: bool = True,
    style: str = "custom",
    custom_path: str | None = None,
) -> None:
    """Play start-of-recording feedback."""
    if not enabled:
        return
    if style == "custom":
        path = custom_path or (str(_BUNDLED_START) if _BUNDLED_START.exists() else None)
        if path and _play_custom(path, volume):
            return
    if style == "chirp":
        tone = _make_chirp(300, 900, 110, volume=volume)
    elif style == "double":
        tone = _make_double(440, 660, 65, 18, volume, ascending=True)
    else:  # "beep"
        tone = _make_tone(440, 100, volume=volume)
    sd.play(tone, samplerate=SAMPLE_RATE, blocking=False)


def play_stop_sound(
    volume: float = 0.4,
    enabled: bool = True,
    style: str = "custom",
    custom_path: str | None = None,
) -> None:
    """Play stop-of-recording feedback."""
    if not enabled:
        return
    if style == "custom":
        path = custom_path or (str(_BUNDLED_STOP) if _BUNDLED_STOP.exists() else None)
        if path and _play_custom(path, volume):
            return
    if style == "chirp":
        tone = _make_chirp(900, 300, 110, volume=volume)
    elif style == "double":
        tone = _make_double(440, 660, 65, 18, volume, ascending=False)
    else:  # "beep"
        tone = _make_tone(880, 100, volume=volume)
    sd.play(tone, samplerate=SAMPLE_RATE, blocking=False)


def play_error_sound(
    volume: float = 0.4,
    enabled: bool = True,
    style: str = "chirp",
    custom_path: str | None = None,
) -> None:
    """Play error feedback — low descending tone."""
    if not enabled:
        return
    if style == "custom" and custom_path:
        if _play_custom(custom_path, volume):
            return
    if style == "chirp":
        tone = _make_chirp(300, 150, 250, volume=volume)
    else:
        tone = _make_tone(220, 200, volume=volume)
    sd.play(tone, samplerate=SAMPLE_RATE, blocking=False)
