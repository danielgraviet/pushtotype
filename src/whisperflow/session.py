"""Display server detection and window class helpers."""

from __future__ import annotations

import logging
import os
import subprocess

logger = logging.getLogger(__name__)


def detect_session() -> str:
    """Return 'x11' or 'wayland' based on the current display server."""
    session = os.environ.get("XDG_SESSION_TYPE", "").lower()
    if session in ("x11", "wayland"):
        return session

    if os.environ.get("WAYLAND_DISPLAY"):
        return "wayland"

    logger.warning("Could not detect display server — defaulting to x11.")
    return "x11"


def get_focused_window_class() -> str | None:
    """Return the WM_CLASS of the currently focused window (X11 only).

    Returns None on Wayland or if detection fails.
    Prefer using TextInjector._get_window_class() which uses python-xlib directly.
    """
    if detect_session() != "x11":
        return None

    try:
        id_result = subprocess.run(
            ["xdotool", "getactivewindow"],
            capture_output=True,
            text=True,
            timeout=2,
        )
        if id_result.returncode != 0:
            return None

        prop_result = subprocess.run(
            ["xprop", "WM_CLASS", "-id", id_result.stdout.strip()],
            capture_output=True,
            text=True,
            timeout=2,
        )
        if prop_result.returncode == 0:
            parts = prop_result.stdout.split('"')
            if len(parts) >= 4:
                return parts[-2].lower()
    except (FileNotFoundError, subprocess.TimeoutExpired):
        pass

    return None
