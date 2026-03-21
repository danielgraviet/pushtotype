"""Text injection via clipboard + paste shortcut."""

from __future__ import annotations

import logging
import subprocess

from whisperflow.session import detect_session

logger = logging.getLogger(__name__)

# Terminals that use Ctrl+Shift+V instead of Ctrl+V to paste.
DEFAULT_SHIFT_PASTE_APPS = [
    "gnome-terminal",
    "gnome-terminal-server",
    "xfce4-terminal",
    "tilix",
    "terminator",
    "mate-terminal",
    "lxterminal",
    "guake",
    "terminology",
    "alacritty",
    "kitty",
    "wezterm",
    "st",
    "urxvt",
    "xterm",
    "code",  # VS Code integrated terminal
]

# Xlib keysym constants
_XK_Control_L = 0xFFE3
_XK_Shift_L = 0xFFE1
_XK_v = ord("v")

try:
    from Xlib import display as _xdisplay
    from Xlib.ext import xtest as _xtest

    _XLIB_AVAILABLE = True
except ImportError:
    _XLIB_AVAILABLE = False


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
        elif tool == "xclip":
            msg = "xclip not found. Install it: sudo apt install xclip"
        elif tool in ("wl-copy", "wl-paste"):
            msg = "wl-clipboard not found. Install it: sudo apt install wl-clipboard"
        elif tool == "wtype":
            msg = "wtype not found. Install it: sudo apt install wtype"
        else:
            msg = f"{tool} not found."
        raise RuntimeError(msg)


class TextInjector:
    """Injects text into the focused application via clipboard + paste shortcut.

    On X11 uses python-xlib for zero-subprocess key simulation and window
    detection. Falls back to xdotool if Xlib is unavailable.
    """

    def __init__(
        self,
        method: str = "auto",
        shift_paste_apps: list[str] | None = None,
    ) -> None:
        self.method = method if method != "auto" else detect_session()
        self.shift_paste_apps = (
            shift_paste_apps if shift_paste_apps is not None else DEFAULT_SHIFT_PASTE_APPS
        )
        # Open a persistent X11 display connection — reused on every inject call.
        self._display = None
        if self.method == "x11" and _XLIB_AVAILABLE:
            try:
                self._display = _xdisplay.Display()
            except Exception as exc:
                logger.warning("Could not open Xlib display: %s — falling back to xdotool", exc)

    def _get_window_class(self) -> str:
        """Return the WM_CLASS of the focused window, lowercase."""
        if self._display is not None:
            try:
                focus = self._display.get_input_focus()
                wm_class = focus.focus.get_wm_class()
                if wm_class:
                    return wm_class[1].lower()
            except Exception:
                pass
        # Subprocess fallback
        try:
            id_res = _run(["xdotool", "getactivewindow"], timeout=2)
            if id_res.returncode == 0:
                prop_res = _run(["xprop", "WM_CLASS", "-id", id_res.stdout.strip()], timeout=2)
                if prop_res.returncode == 0:
                    parts = prop_res.stdout.split('"')
                    if len(parts) >= 4:
                        return parts[-2].lower()
        except RuntimeError:
            pass
        return ""

    def _send_paste_xlib(self, use_shift: bool) -> None:
        """Simulate Ctrl+V or Ctrl+Shift+V via XTest — no subprocess."""
        from Xlib import X

        d = self._display
        ctrl = d.keysym_to_keycode(_XK_Control_L)
        v = d.keysym_to_keycode(_XK_v)
        keys = [ctrl]
        if use_shift:
            keys.append(d.keysym_to_keycode(_XK_Shift_L))
        keys.append(v)

        for k in keys:
            _xtest.fake_input(d, X.KeyPress, k)
        for k in reversed(keys):
            _xtest.fake_input(d, X.KeyRelease, k)
        d.sync()

    def inject(self, text: str) -> None:
        """Paste text into the currently focused application."""
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
        # Write to clipboard via xclip (fast — forks a daemon to hold the selection)
        _run(["xclip", "-selection", "clipboard"], input=text)

        # Detect terminal vs normal app
        window_class = self._get_window_class()
        logger.debug("Focused window class: %r", window_class)
        is_terminal = any(app in window_class for app in self.shift_paste_apps)

        # Simulate paste — via Xlib if available, subprocess otherwise
        if self._display is not None:
            self._send_paste_xlib(is_terminal)
        else:
            shortcut = "ctrl+shift+v" if is_terminal else "ctrl+v"
            _run(["xdotool", "key", "--clearmodifiers", shortcut])

    def _inject_wayland(self, text: str) -> None:
        _run(["wl-copy"], input=text)
        _run(["wtype", "-M", "ctrl", "-k", "v", "-m", "ctrl"])
