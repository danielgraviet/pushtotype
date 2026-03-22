"""Global hotkey listener using evdev (Wayland-compatible)."""

from __future__ import annotations

import asyncio
import logging
from collections.abc import Callable

logger = logging.getLogger(__name__)

# Lazy import so the module can be imported in CI without kernel input devices.
try:
    import evdev
    from evdev import categorize, ecodes
except ImportError:  # pragma: no cover
    evdev = None  # type: ignore[assignment]
    categorize = None
    ecodes = None

# A device must have all of these keys to be classified as a keyboard
# (filters out mice, gamepads, and other EV_KEY devices).
_KEYBOARD_KEYS = (
    {
        ecodes.KEY_A,
        ecodes.KEY_S,
        ecodes.KEY_D,
        ecodes.KEY_SPACE,
        ecodes.KEY_ENTER,
        ecodes.KEY_LEFTSHIFT,
    }
    if ecodes
    else set()
)

# Maps the key names accepted in hotkey strings (e.g. "Ctrl+Shift+S") to evdev keycodes.
# Letters are added programmatically below to avoid listing all 26 individually.
_KEY_NAME_MAP: dict[str, int] = {}
if ecodes:
    _KEY_NAME_MAP = {
        "ctrl": ecodes.KEY_LEFTCTRL,
        "leftctrl": ecodes.KEY_LEFTCTRL,
        "rightctrl": ecodes.KEY_RIGHTCTRL,
        "shift": ecodes.KEY_LEFTSHIFT,
        "leftshift": ecodes.KEY_LEFTSHIFT,
        "rightshift": ecodes.KEY_RIGHTSHIFT,
        "space": ecodes.KEY_SPACE,
    }
    for _c in "abcdefghijklmnopqrstuvwxyz":
        _key_attr = f"KEY_{_c.upper()}"
        if hasattr(ecodes, _key_attr):
            _KEY_NAME_MAP[_c] = getattr(ecodes, _key_attr)


def normalize_hotkey_key(name: str) -> str:
    """Convert an evdev key name to the format expected by parse_hotkey.

    Handles both config-file format (``KEY_RIGHTCTRL``) and human format
    (``rightctrl``) so either can be stored in config and passed through here.

    Examples::

        normalize_hotkey_key("KEY_RIGHTCTRL") -> "rightctrl"
        normalize_hotkey_key("KEY_A")         -> "a"
        normalize_hotkey_key("rightctrl")     -> "rightctrl"
    """
    n = name.strip()
    if n.upper().startswith("KEY_"):
        n = n[4:]
    return n.lower()


def parse_hotkey(hotkey_str: str) -> frozenset[int]:
    """Parse a hotkey string like 'Ctrl+Shift+S' into a frozenset of evdev keycodes.

    A frozenset is used because a combo is an unordered, immutable collection of keys —
    "Ctrl+Shift+S" is identical to "Shift+Ctrl+S".
    """
    codes: set[int] = set()
    for part in hotkey_str.split("+"):
        name = part.strip().lower()
        if name not in _KEY_NAME_MAP:
            raise ValueError(f"Unknown key name: '{part}'. Supported: {sorted(_KEY_NAME_MAP)}")
        codes.add(_KEY_NAME_MAP[name])
    return frozenset(codes)


def find_keyboards() -> list:
    """Return all evdev InputDevices that look like keyboards.

    Most systems expose multiple keyboard devices — e.g. a laptop has its built-in
    keyboard plus any connected USB keyboards. We listen to all of them so the hotkey
    works regardless of which physical keyboard the user presses it on.
    """
    if evdev is None:
        return []

    keyboards = []
    for path in evdev.list_devices():
        try:
            dev = evdev.InputDevice(path)
            caps = dev.capabilities()
            ev_key_caps = caps.get(ecodes.EV_KEY, [])
            if ev_key_caps and _KEYBOARD_KEYS.issubset(set(ev_key_caps)):
                keyboards.append(dev)
            else:
                dev.close()
        except PermissionError:
            logger.error(
                "Permission denied reading %s. "
                "Make sure your user is in the 'input' group: sudo usermod -aG input $USER",
                path,
            )
        except OSError:
            pass

    return keyboards


class HotkeyListener:
    """Listens to all detected keyboards for a key combo.

    Fires ``on_press`` when the full combo is held and ``on_release`` when any
    combo key is released while the combo was active.
    """

    def __init__(
        self,
        keys: list[str],
        on_press: Callable[[], None],
        on_release: Callable[[], None],
    ) -> None:
        self.combo: frozenset[int] = parse_hotkey("+".join(keys))
        self.on_press = on_press
        self.on_release = on_release
        self._pressed: set[int] = set()
        self._combo_active = False

    def _handle_key(self, keycode: int, keystate: int) -> None:
        """Process a single key event (keystate: 0=up, 1=down, 2=repeat)."""
        if keystate == 2:  # Ignore key repeat
            return

        if keystate == 1:  # Key down
            self._pressed.add(keycode)
            if not self._combo_active and self.combo.issubset(self._pressed):
                self._combo_active = True
                self.on_press()

        elif keystate == 0:  # Key up
            if self._combo_active and keycode in self.combo:
                self._combo_active = False
                self.on_release()
            self._pressed.discard(keycode)

    async def _listen_device(self, device) -> None:
        """Async loop reading events from a single device."""
        try:
            async for event in device.async_read_loop():
                if event.type == ecodes.EV_KEY:
                    key_event = categorize(event)
                    self._handle_key(key_event.scancode, key_event.keystate)
        except OSError:
            logger.debug("Device %s disconnected.", device.path)

    async def run(self) -> None:
        """Start listening on all detected keyboards. Runs until cancelled."""
        keyboards = find_keyboards()
        if not keyboards:
            logger.warning("No keyboard devices found — hotkey detection will not work.")
            return

        logger.debug("Listening on %d keyboard(s).", len(keyboards))
        tasks = [asyncio.create_task(self._listen_device(dev)) for dev in keyboards]
        try:
            await asyncio.gather(*tasks)
        finally:
            for t in tasks:
                t.cancel()
            for dev in keyboards:
                try:
                    dev.close()
                except Exception:
                    pass
