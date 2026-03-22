"""Audio feedback tones for recording start/stop/error."""

from __future__ import annotations

import numpy as np
import sounddevice as sd

SAMPLE_RATE = 44100


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

    # Apply fade in/out to avoid clicks
    fade_n = min(int(SAMPLE_RATE * fade_ms / 1000), n_samples // 4)
    if fade_n > 0:
        fade_in = np.linspace(0.0, 1.0, fade_n, dtype=np.float32)
        fade_out = np.linspace(1.0, 0.0, fade_n, dtype=np.float32)
        wave[:fade_n] *= fade_in
        wave[-fade_n:] *= fade_out

    return wave


def play_start_sound(volume: float = 0.4, enabled: bool = True) -> None:
    """Play a 440 Hz beep — recording started."""
    if not enabled:
        return
    tone = _make_tone(440, 100, volume=volume)
    sd.play(tone, samplerate=SAMPLE_RATE, blocking=False)


def play_stop_sound(volume: float = 0.4, enabled: bool = True) -> None:
    """Play an 880 Hz beep — recording stopped."""
    if not enabled:
        return
    tone = _make_tone(880, 100, volume=volume)
    sd.play(tone, samplerate=SAMPLE_RATE, blocking=False)


def play_error_sound(volume: float = 0.4, enabled: bool = True) -> None:
    """Play a 220 Hz tone — something went wrong."""
    if not enabled:
        return
    tone = _make_tone(220, 200, volume=volume)
    sd.play(tone, samplerate=SAMPLE_RATE, blocking=False)
