"""Tests for pushtype.transcriber — mocked so CI works without GPU/model."""

from unittest.mock import MagicMock, patch

import numpy as np
import pytest


def _make_fake_model(text="hello world"):
    """Return a mock WhisperModel that yields one segment."""
    seg = MagicMock()
    seg.text = text

    model = MagicMock()
    model.transcribe.return_value = (iter([seg]), MagicMock())
    return model


@pytest.fixture(autouse=True)
def _no_ctranslate2_cuda(monkeypatch):
    """Force CPU path so tests never need a real GPU."""
    import ctranslate2  # noqa: PLC0415

    monkeypatch.setattr(
        ctranslate2,
        "get_supported_compute_types",
        lambda device: [] if device == "cuda" else ["int8"],
    )


def test_transcriber_init_uses_cpu_when_no_cuda():
    fake_model = _make_fake_model()
    with patch("pushtotype.transcriber.WhisperModel", return_value=fake_model) as mock_model_cls:
        from pushtotype.transcriber import Transcriber

        tx = Transcriber(model_name="base.en")

    assert tx.device == "cpu"
    assert tx.compute_type == "int8"
    mock_model_cls.assert_called_once_with("base.en", device="cpu", compute_type="int8")


def test_transcribe_returns_string():
    fake_model = _make_fake_model("this is a test")
    with patch("pushtotype.transcriber.WhisperModel", return_value=fake_model):
        from pushtotype.transcriber import Transcriber

        tx = Transcriber()
        audio = np.zeros(16000, dtype=np.float32)
        result = tx.transcribe(audio)

    assert isinstance(result, str)
    assert result == "this is a test"


def test_transcribe_strips_whitespace():
    fake_model = _make_fake_model("  padded text  ")
    with patch("pushtotype.transcriber.WhisperModel", return_value=fake_model):
        from pushtotype.transcriber import Transcriber

        tx = Transcriber()
        result = tx.transcribe(np.zeros(16000, dtype=np.float32))

    assert result == "padded text"


def test_transcriber_explicit_cpu():
    fake_model = _make_fake_model()
    with patch("pushtotype.transcriber.WhisperModel", return_value=fake_model) as mock_model_cls:
        from pushtotype.transcriber import Transcriber

        tx = Transcriber(model_name="tiny", device="cpu", compute_type="int8")

    assert tx.device == "cpu"
    mock_model_cls.assert_called_once_with("tiny", device="cpu", compute_type="int8")
