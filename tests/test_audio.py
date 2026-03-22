"""Tests for pushtype.audio — uses mocks so CI works without hardware."""

from unittest.mock import MagicMock, patch

import numpy as np
import pytest


def _fake_query_devices():
    return [
        {
            "name": "Fake Mic",
            "max_input_channels": 2,
            "default_samplerate": 44100,
        },
        {
            "name": "Monitor Output",
            "max_input_channels": 0,
            "default_samplerate": 48000,
        },
    ]


def test_list_devices_returns_only_input_devices():
    with (
        patch("sounddevice.query_devices", side_effect=_fake_query_devices),
        patch("sounddevice.default", MagicMock(device=[0, 1])),
    ):
        from pushtotype.audio import list_devices

        devs = list_devices()
    # Only the device with max_input_channels > 0 should appear
    assert len(devs) == 1
    assert devs[0]["name"] == "Fake Mic"
    assert devs[0]["max_input_channels"] == 2


def test_list_devices_marks_default():
    with (
        patch("sounddevice.query_devices", side_effect=_fake_query_devices),
        patch("sounddevice.default", MagicMock(device=[0, 1])),
    ):
        from pushtotype.audio import list_devices

        devs = list_devices()
    assert devs[0]["is_default"] is True


def test_record_returns_float32_mono_array():
    """Verify that record() returns a 1-D float32 array of the right length."""
    sample_rate = 16000
    duration = 0.5
    expected_samples = int(sample_rate * duration)
    fake_chunk = np.zeros((expected_samples, 1), dtype=np.float32)

    class FakeInputStream:
        def __init__(self, *args, callback=None, **kwargs):
            self._cb = callback
            self._chunk = fake_chunk

        def __enter__(self):
            # Fire the callback once with our fake data
            self._cb(self._chunk, len(self._chunk), None, None)
            return self

        def __exit__(self, *args):
            pass

    with patch("sounddevice.InputStream", FakeInputStream):
        from pushtotype.audio import record

        audio = record(duration=duration, sample_rate=sample_rate)

    assert isinstance(audio, np.ndarray)
    assert audio.dtype == np.float32
    assert audio.ndim == 1
    assert len(audio) == expected_samples


def test_record_raises_when_no_audio_captured():
    class EmptyInputStream:
        def __init__(self, *args, **kwargs):
            pass

        def __enter__(self):
            return self

        def __exit__(self, *args):
            pass

    with patch("sounddevice.InputStream", EmptyInputStream):
        from pushtotype.audio import record

        with pytest.raises(RuntimeError, match="No audio captured"):
            record(duration=0.01)
