"""Text injection via xdotool type (X11) or wtype (Wayland)."""

from __future__ import annotations

import logging
import subprocess

from pushtotype.session import detect_session

logger = logging.getLogger(__name__)


def _run(
    args: list[str], input: str | None = None, timeout: int = 5
) -> subprocess.CompletedProcess:
    """Run a subprocess, raising a clear error if the tool is missing."""
    try:
        return subprocess.run(
            args,
            input=input,
            capture_output=True,
            text=True,
            timeout=timeout,
        )
    except subprocess.TimeoutExpired:
        return subprocess.CompletedProcess(args=args, returncode=1, stdout="", stderr="")
    except FileNotFoundError:
        tool = args[0]
        if tool == "xdotool":
            msg = "xdotool not found. Install it: sudo apt install xdotool"
        elif tool in ("wl-copy", "wl-paste"):
            msg = "wl-clipboard not found. Install it: sudo apt install wl-clipboard"
        elif tool == "wtype":
            msg = "wtype not found. Install it: sudo apt install wtype"
        else:
            msg = f"{tool} not found."
        raise RuntimeError(msg)


class TextInjector:
    """Injects transcribed text into the focused application.

    X11:     xdotool type — direct keystroke simulation, no clipboard.
    Wayland: wl-copy + wtype Ctrl+V.
    """

    def __init__(self, method: str = "auto") -> None:
        self.method = method if method != "auto" else detect_session()

    def inject(self, text: str) -> None:
        """Type text into the currently focused application."""
        if not text.strip():
            return
        try:
            if self.method == "x11":
                self._inject_x11(text)
            else:
                self._inject_wayland(text)
        except Exception as exc:
            logger.error("Text injection failed: %s", exc)
            print(f"  [injection error: {exc}]")

    def _inject_x11(self, text: str) -> None:
        import time as _time

        t0 = _time.perf_counter()
        _run(["xdotool", "type", "--delay", "0", "--clearmodifiers", "--", text])
        logger.debug("xdotool type: %.3fs", _time.perf_counter() - t0)

    def _inject_wayland(self, text: str) -> None:
        _run(["wl-copy"], input=text)
        _run(["wtype", "-M", "ctrl", "-k", "v", "-m", "ctrl"])
