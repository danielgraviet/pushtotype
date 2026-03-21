"""Tests for the hotkey listener module."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from whisperflow.hotkey import HotkeyListener, find_keyboards, parse_hotkey

# ---------------------------------------------------------------------------
# parse_hotkey
# ---------------------------------------------------------------------------


def test_parse_hotkey_single_key():
    codes = parse_hotkey("s")
    assert len(codes) == 1


def test_parse_hotkey_single_modifier():
    codes = parse_hotkey("rightctrl")
    assert len(codes) == 1


def test_parse_hotkey_unknown_key():
    with pytest.raises(ValueError, match="Unknown key name"):
        parse_hotkey("Banana")


# ---------------------------------------------------------------------------
# find_keyboards — mocked so CI doesn't need /dev/input
# ---------------------------------------------------------------------------


def test_find_keyboards_returns_list():
    with patch("whisperflow.hotkey.evdev") as mock_evdev:
        mock_evdev.list_devices.return_value = []
        result = find_keyboards()
    assert isinstance(result, list)


def test_find_keyboards_filters_non_keyboards():
    """A device without the standard keyboard keys should be excluded."""
    with patch("whisperflow.hotkey.evdev") as mock_evdev:
        from evdev import ecodes

        fake_dev = MagicMock()
        # Only has a single key — not enough to be a keyboard
        fake_dev.capabilities.return_value = {ecodes.EV_KEY: [ecodes.KEY_VOLUMEUP]}
        mock_evdev.list_devices.return_value = ["/dev/input/event99"]
        mock_evdev.InputDevice.return_value = fake_dev

        result = find_keyboards()

    assert result == []


# ---------------------------------------------------------------------------
# HotkeyListener key logic
# ---------------------------------------------------------------------------


def _make_listener():
    on_press = MagicMock()
    on_release = MagicMock()
    listener = HotkeyListener(
        keys=["rightctrl"],
        on_press=on_press,
        on_release=on_release,
    )
    return listener, on_press, on_release


def test_key_repeat_ignored():
    listener, on_press, on_release = _make_listener()
    for code in listener.combo:
        listener._handle_key(code, 2)  # repeat events
    on_press.assert_not_called()
    on_release.assert_not_called()


def test_combo_fires_on_press():
    listener, on_press, on_release = _make_listener()
    for code in listener.combo:
        listener._handle_key(code, 1)
    on_press.assert_called_once()
    on_release.assert_not_called()


def test_release_fires_when_any_combo_key_released():
    listener, on_press, on_release = _make_listener()
    # Press all combo keys
    for code in listener.combo:
        listener._handle_key(code, 1)
    on_press.assert_called_once()

    # Release just one
    first_key = next(iter(listener.combo))
    listener._handle_key(first_key, 0)
    on_release.assert_called_once()


def test_combo_not_active_after_release():
    listener, on_press, on_release = _make_listener()
    for code in listener.combo:
        listener._handle_key(code, 1)
    first_key = next(iter(listener.combo))
    listener._handle_key(first_key, 0)

    assert not listener._combo_active


def test_on_release_not_fired_without_prior_press():
    listener, on_press, on_release = _make_listener()
    # Release a combo key without ever pressing the full combo
    first_key = next(iter(listener.combo))
    listener._handle_key(first_key, 0)
    on_release.assert_not_called()
