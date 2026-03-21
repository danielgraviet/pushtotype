"""Tests for the audio feedback module."""

from __future__ import annotations

from unittest.mock import patch

import numpy as np
import pytest

from whisperflow.feedback import (
    SAMPLE_RATE,
    _make_tone,
    play_error_sound,
    play_start_sound,
    play_stop_sound,
)

# ---------------------------------------------------------------------------
# Tone generation
# ---------------------------------------------------------------------------


def test_make_tone_shape():
    tone = _make_tone(440, 100)
    expected_samples = int(SAMPLE_RATE * 100 / 1000)
    assert tone.shape == (expected_samples,)


def test_make_tone_dtype():
    tone = _make_tone(440, 100)
    assert tone.dtype == np.float32


def test_make_tone_volume_respected():
    loud = _make_tone(440, 100, volume=1.0, fade_ms=0)
    quiet = _make_tone(440, 100, volume=0.1, fade_ms=0)
    assert loud.max() > quiet.max()


def test_make_tone_fade_reduces_endpoints():
    """With fade, first and last samples should be near zero."""
    tone = _make_tone(440, 100, volume=1.0, fade_ms=10)
    assert abs(float(tone[0])) < 0.05
    assert abs(float(tone[-1])) < 0.05


# ---------------------------------------------------------------------------
# Play functions respect enabled=False
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("fn", [play_start_sound, play_stop_sound, play_error_sound])
def test_disabled_prevents_playback(fn):
    with patch("whisperflow.feedback.sd.play") as mock_play:
        fn(enabled=False)
    mock_play.assert_not_called()


@pytest.mark.parametrize("fn", [play_start_sound, play_stop_sound, play_error_sound])
def test_enabled_triggers_playback(fn):
    with patch("whisperflow.feedback.sd.play") as mock_play:
        fn(enabled=True)
    mock_play.assert_called_once()
