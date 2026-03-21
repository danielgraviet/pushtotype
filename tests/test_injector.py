"""Tests for the text injector module."""

from __future__ import annotations

from subprocess import CompletedProcess
from unittest.mock import MagicMock, patch

import pytest

from whisperflow.injector import DEFAULT_SHIFT_PASTE_APPS, TextInjector


def _ok(stdout: str = "") -> CompletedProcess:
    return CompletedProcess(args=[], returncode=0, stdout=stdout, stderr="")


def _x11_injector() -> TextInjector:
    """Return an X11 injector with Xlib disabled so tests use subprocess fallback."""
    injector = TextInjector(method="x11")
    injector._display = None  # force subprocess path
    return injector


# ---------------------------------------------------------------------------
# Session routing
# ---------------------------------------------------------------------------


def test_auto_routes_to_x11():
    with patch("whisperflow.injector.detect_session", return_value="x11"):
        injector = TextInjector(method="auto")
    assert injector.method == "x11"


def test_auto_routes_to_wayland():
    with patch("whisperflow.injector.detect_session", return_value="wayland"):
        injector = TextInjector(method="auto")
    assert injector.method == "wayland"


# ---------------------------------------------------------------------------
# X11 injection — subprocess fallback path (display=None)
# ---------------------------------------------------------------------------


def test_inject_x11_calls_xclip_and_xdotool():
    injector = _x11_injector()
    with (
        patch("whisperflow.injector._run", return_value=_ok()) as mock_run,
        patch.object(injector, "_get_window_class", return_value="firefox"),
    ):
        injector.inject("hello world")

    calls = [c.args[0] for c in mock_run.call_args_list]
    assert any("xclip" in c for c in calls)
    assert any("xdotool" in c for c in calls)


def test_inject_x11_uses_ctrl_v_for_normal_app():
    injector = _x11_injector()
    with (
        patch("whisperflow.injector._run", return_value=_ok()) as mock_run,
        patch.object(injector, "_get_window_class", return_value="firefox"),
    ):
        injector.inject("hello")

    xdotool_call = next(c for c in mock_run.call_args_list if "xdotool" in c.args[0])
    assert "ctrl+v" in xdotool_call.args[0]
    assert "ctrl+shift+v" not in xdotool_call.args[0]


def test_inject_x11_uses_ctrl_shift_v_for_terminal():
    injector = _x11_injector()
    with (
        patch("whisperflow.injector._run", return_value=_ok()) as mock_run,
        patch.object(injector, "_get_window_class", return_value="kitty"),
    ):
        injector.inject("hello")

    xdotool_call = next(c for c in mock_run.call_args_list if "xdotool" in c.args[0])
    assert "ctrl+shift+v" in xdotool_call.args[0]


def test_inject_x11_subprocess_path_two_calls():
    """Subprocess fallback: xclip write + xdotool key only."""
    injector = _x11_injector()
    with (
        patch("whisperflow.injector._run", return_value=_ok()) as mock_run,
        patch.object(injector, "_get_window_class", return_value="firefox"),
    ):
        injector.inject("hello")

    assert len(mock_run.call_args_list) == 2


# ---------------------------------------------------------------------------
# X11 injection — Xlib fast path
# ---------------------------------------------------------------------------


def test_inject_x11_xlib_path_uses_no_xdotool():
    """When Xlib display is available, no xdotool subprocess is spawned for keys."""
    injector = TextInjector(method="x11")
    injector._display = MagicMock()  # simulate live display
    with (
        patch("whisperflow.injector._run", return_value=_ok()) as mock_run,
        patch.object(injector, "_get_window_class", return_value="firefox"),
        patch.object(injector, "_send_paste_xlib"),
    ):
        injector.inject("hello")

    calls = [c.args[0] for c in mock_run.call_args_list]
    assert not any("xdotool" in c for c in calls)
    assert any("xclip" in c for c in calls)


def test_inject_x11_xlib_path_one_subprocess_call():
    """Only xclip clipboard write — key simulation uses Xlib."""
    injector = TextInjector(method="x11")
    injector._display = MagicMock()
    with (
        patch("whisperflow.injector._run", return_value=_ok()) as mock_run,
        patch.object(injector, "_get_window_class", return_value="firefox"),
        patch.object(injector, "_send_paste_xlib"),
    ):
        injector.inject("hello")

    assert len(mock_run.call_args_list) == 1


# ---------------------------------------------------------------------------
# Wayland injection
# ---------------------------------------------------------------------------


def test_inject_wayland_calls_wl_copy_and_wtype():
    injector = TextInjector(method="wayland")
    with (
        patch("whisperflow.injector._run", return_value=_ok()) as mock_run,
    ):
        injector.inject("hello world")

    calls = [c.args[0] for c in mock_run.call_args_list]
    assert any("wl-copy" in c for c in calls)
    assert any("wtype" in c for c in calls)


# ---------------------------------------------------------------------------
# Missing tools
# ---------------------------------------------------------------------------


def test_missing_tool_does_not_crash():
    injector = _x11_injector()
    with (
        patch("whisperflow.injector._run", side_effect=RuntimeError("xclip not found")),
        patch.object(injector, "_get_window_class", return_value="firefox"),
    ):
        injector.inject("hello")  # should not raise


def test_run_raises_on_missing_tool():
    from whisperflow.injector import _run

    with patch("subprocess.run", side_effect=FileNotFoundError):
        with pytest.raises(RuntimeError, match="xdotool not found"):
            _run(["xdotool", "key", "ctrl+v"])


# ---------------------------------------------------------------------------
# Terminal detection list
# ---------------------------------------------------------------------------


def test_default_shift_paste_apps_not_empty():
    assert len(DEFAULT_SHIFT_PASTE_APPS) > 0


def test_empty_text_skips_injection():
    injector = _x11_injector()
    with patch("whisperflow.injector._run") as mock_run:
        injector.inject("   ")
    mock_run.assert_not_called()
