"""Audio capture via sounddevice."""

from __future__ import annotations

import threading

import numpy as np
import sounddevice as sd


def list_devices() -> list[dict]:
    """Return all available audio input devices."""
    devices = []
    for idx, dev in enumerate(sd.query_devices()):
        if dev["max_input_channels"] > 0:
            devices.append(
                {
                    "index": idx,
                    "name": dev["name"],
                    "default_samplerate": int(dev["default_samplerate"]),
                    "max_input_channels": dev["max_input_channels"],
                    "is_default": idx == sd.default.device[0],
                }
            )
    return devices


def record(duration: float, device=None, sample_rate: int = 16000) -> np.ndarray:
    """Record an audio stream and return it as a float32 mono numpy array."""
    frames: list[np.ndarray] = []
    done = threading.Event()

    def callback(indata: np.ndarray, frame_count: int, time_info, status):  # noqa: ARG001
        frames.append(indata.copy())

    with sd.InputStream(
        samplerate=sample_rate,
        channels=1,
        dtype="float32",
        device=device,
        callback=callback,
    ):
        done.wait(timeout=duration)

    if not frames:
        raise RuntimeError("No audio captured — check that a microphone is available.")

    audio = np.concatenate(frames, axis=0)

    # Downmix to mono if somehow we got multiple channels
    if audio.ndim > 1 and audio.shape[1] > 1:
        audio = audio.mean(axis=1)
    else:
        audio = audio.squeeze()  # (N, 1) → (N,)

    return audio.astype(np.float32)
