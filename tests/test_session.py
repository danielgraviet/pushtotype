"""Tests for session detection."""

from __future__ import annotations

from unittest.mock import patch

from pushtotype.session import detect_session


def test_detect_x11_from_env():
    with patch.dict("os.environ", {"XDG_SESSION_TYPE": "x11"}):
        assert detect_session() == "x11"


def test_detect_wayland_from_env():
    with patch.dict("os.environ", {"XDG_SESSION_TYPE": "wayland"}):
        assert detect_session() == "wayland"


def test_detect_wayland_fallback():
    with patch.dict("os.environ", {"XDG_SESSION_TYPE": "", "WAYLAND_DISPLAY": "wayland-0"}):
        assert detect_session() == "wayland"


def test_detect_defaults_to_x11():
    with patch.dict("os.environ", {}, clear=True):
        assert detect_session() == "x11"
