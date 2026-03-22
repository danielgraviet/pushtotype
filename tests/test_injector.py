"""Tests for the text injector module."""

from __future__ import annotations

from subprocess import CompletedProcess
from unittest.mock import patch

import pytest

from pushtotype.injector import TextInjector


def _ok(stdout: str = "") -> CompletedProcess:
    return CompletedProcess(args=[], returncode=0, stdout=stdout, stderr="")


# ---------------------------------------------------------------------------
# Session routing
# ---------------------------------------------------------------------------


def test_auto_routes_to_x11():
    with patch("pushtotype.injector.detect_session", return_value="x11"):
        injector = TextInjector(method="auto")
    assert injector.method == "x11"


def test_auto_routes_to_wayland():
    with patch("pushtotype.injector.detect_session", return_value="wayland"):
        injector = TextInjector(method="auto")
    assert injector.method == "wayland"


# ---------------------------------------------------------------------------
# X11 injection
# ---------------------------------------------------------------------------


def test_inject_x11_calls_xdotool_type():
    injector = TextInjector(method="x11")
    with patch("pushtotype.injector._run", return_value=_ok()) as mock_run:
        injector.inject("hello world")

    args = mock_run.call_args[0][0]
    assert args[0] == "xdotool"
    assert "type" in args


def test_inject_x11_single_subprocess_call():
    injector = TextInjector(method="x11")
    with patch("pushtotype.injector._run", return_value=_ok()) as mock_run:
        injector.inject("hello")

    assert len(mock_run.call_args_list) == 1


def test_inject_x11_passes_text_to_xdotool():
    injector = TextInjector(method="x11")
    with patch("pushtotype.injector._run", return_value=_ok()) as mock_run:
        injector.inject("March Madness")

    args = mock_run.call_args[0][0]
    assert "March Madness" in args


# ---------------------------------------------------------------------------
# Wayland injection
# ---------------------------------------------------------------------------


def test_inject_wayland_calls_wl_copy_and_wtype():
    injector = TextInjector(method="wayland")
    with patch("pushtotype.injector._run", return_value=_ok()) as mock_run:
        injector.inject("hello world")

    calls = [c.args[0] for c in mock_run.call_args_list]
    assert any("wl-copy" in c for c in calls)
    assert any("wtype" in c for c in calls)


# ---------------------------------------------------------------------------
# Missing tools / error handling
# ---------------------------------------------------------------------------


def test_missing_tool_does_not_crash():
    injector = TextInjector(method="x11")
    with patch("pushtotype.injector._run", side_effect=RuntimeError("xdotool not found")):
        injector.inject("hello")  # should not raise


def test_run_raises_on_missing_tool():
    from pushtotype.injector import _run

    with patch("subprocess.run", side_effect=FileNotFoundError):
        with pytest.raises(RuntimeError, match="xdotool not found"):
            _run(["xdotool", "type", "--", "hello"])


def test_empty_text_skips_injection():
    injector = TextInjector(method="x11")
    with patch("pushtotype.injector._run") as mock_run:
        injector.inject("   ")
    mock_run.assert_not_called()
