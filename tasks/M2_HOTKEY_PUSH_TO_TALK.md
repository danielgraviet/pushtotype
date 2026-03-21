# Milestone 2: Global Hotkey + Push-to-Talk

> **Goal:** Hold a key combo anywhere on your system, speak while holding, release, and see the transcription printed to the terminal. The daemon loop is running.

---

## Why This Phase Matters

This phase turns WhisperFlow from a "run a command and wait" tool into a background daemon that responds to your input in real-time. The push-to-talk interaction model is the core UX — it's what makes this feel like a product instead of a script. Getting `evdev` right here also guarantees Wayland compatibility from day one.

---

## Prerequisites

- M1 is complete (`whisperflow test` records and transcribes successfully)
- Your user is in the `input` group:

```bash
sudo usermod -aG input $USER
# Then log out and log back in
# Verify: groups | grep input
```

---

## Learning Objectives

By completing this milestone you will understand:

- How Linux input events work at the kernel level (`/dev/input/`)
- How `python-evdev` reads key events asynchronously
- How to detect and filter keyboard devices from other input devices
- How to implement a press-and-hold (push-to-talk) interaction model
- How `asyncio` coordinates multiple concurrent tasks (hotkey listening + audio recording)
- How to generate and play simple audio feedback tones

---

## Tasks

### 2.1 — Add dependencies
- [ ] Add to `pyproject.toml`:

```toml
"evdev>=1.6.0",
```

- [ ] Reinstall: `pip install -e ".[dev]"`
- [ ] Verify: `python -c "import evdev; print(evdev.list_devices())"`
- [ ] If empty list or permission error → confirm `input` group membership

### 2.2 — Hotkey listener module (`hotkey.py`)
- [ ] Create `src/whisperflow/hotkey.py` with:
  - `find_keyboards()` → scans `/dev/input/` and returns all devices that have `EV_KEY` capability with standard keyboard keys (filter out mice, gamepads, etc.)
  - `HotkeyListener` class:
    - `__init__(keys: list[str], on_press: Callable, on_release: Callable)` — configures the hotkey combo
    - `async run()` — async event loop that reads from all keyboards
    - Fires `on_press` when the full key combo is held down
    - Fires `on_release` when any key in the combo is released
    - Handles modifier keys (Shift, Ctrl, Super/Meta, Alt) correctly
- [ ] Handle edge cases:
  - Multiple keyboards: listen to all of them
  - USB keyboard hot-plug: detect new devices periodically or handle gracefully
  - Permission denied: catch and print helpful error about `input` group

**Key design decisions:**
- Use `evdev.InputDevice.async_read_loop()` with `asyncio` for non-blocking reads
- Track currently pressed keys in a `set()` — when the set matches the configured combo, fire `on_press`
- Fire `on_release` when any combo key goes up, not when all go up — this prevents "stuck" recordings
- Ignore key repeat events (`event.value == 2`) — only care about down (1) and up (0)

### 2.3 — Audio feedback module (`feedback.py`)
- [ ] Create `src/whisperflow/feedback.py` with:
  - `play_start_sound()` — plays a short "start recording" beep
  - `play_stop_sound()` — plays a short "stop recording" beep
  - `play_error_sound()` — plays a short error tone
- [ ] For v1, generate tones programmatically using numpy (sine waves):
  - Start: 440Hz, 100ms, gentle fade in/out
  - Stop: 880Hz, 100ms (higher pitch = done)
  - Error: 220Hz, 200ms (lower pitch = problem)
- [ ] Play via `sounddevice.play()` (non-blocking)
- [ ] Respect a `volume` parameter (0.0–1.0)
- [ ] Add an `enabled` flag so feedback can be turned off

### 2.4 — Daemon loop (`daemon.py`)
- [ ] Create `src/whisperflow/daemon.py` with the main orchestration:
  - On startup:
    - Load the Whisper model (print loading time)
    - Find keyboard devices
    - Print "WhisperFlow is running. Press [hotkey] to record. Ctrl+C to quit."
  - On hotkey press:
    - Play start sound
    - Begin recording audio
  - On hotkey release:
    - Stop recording
    - Play stop sound
    - Transcribe the audio buffer
    - **For now: print the transcription to stdout** (text injection comes in M3)
    - Print timing info
  - On Ctrl+C:
    - Clean shutdown, release devices

- [ ] Use `asyncio` to coordinate:
  - Hotkey listener runs as an async task
  - Audio recording starts/stops based on hotkey callbacks
  - Transcription runs after recording stops (can be synchronous — it's fast on GPU)

### 2.5 — Wire up the CLI
- [ ] Update `cli.py`:
  - `whisperflow` (root command, no subcommand) → starts the daemon
  - Accept flags: `--model`, `--hotkey`, `--device` (audio device)
  - Default hotkey: `Super+Shift+S` (configurable)
- [ ] `whisperflow` should print clear startup info:

```
WhisperFlow v0.1.0
  Model:    base.en (cuda, float16)
  Hotkey:   Super+Shift+S
  Audio:    HDA Intel PCH (16000 Hz)
  Keyboards: 2 devices detected

Ready. Hold [Super+Shift+S] to speak. Ctrl+C to quit.
```

### 2.6 — Minimum audio length guard
- [ ] If the recording is shorter than 0.3 seconds, skip transcription
- [ ] Print a message: "Recording too short, skipping."
- [ ] This prevents accidental triggers from quick key taps

### 2.7 — Tests
- [ ] `tests/test_hotkey.py`:
  - Test `find_keyboards()` returns a list (mock `evdev.list_devices` in CI)
  - Test key combo matching logic with simulated events
  - Test that key repeat events (value=2) are ignored
  - Test that release fires when any combo key goes up
- [ ] `tests/test_feedback.py`:
  - Test that tone generation produces numpy arrays of correct shape
  - Test that `enabled=False` prevents playback
- [ ] Update existing tests to ensure nothing is broken

---

## Checkpoints

| # | Checkpoint | How to verify |
|---|---|---|
| 1 | evdev can see keyboards | `python -c "import evdev; [print(evdev.InputDevice(p).name) for p in evdev.list_devices()]"` |
| 2 | Permission is working | No "Permission denied" errors when reading input devices |
| 3 | Hotkey detection works | Run daemon, press combo, see "key down" / "key up" log messages |
| 4 | Audio records during hold | Hold hotkey for 3s, release, see "Recorded 3.0s of audio" |
| 5 | Transcription runs on release | Release hotkey, see transcription printed to terminal |
| 6 | Audio feedback plays | Hear start beep when pressing, stop beep when releasing |
| 7 | Quick tap is ignored | Tap hotkey quickly (<0.3s), see "Recording too short" message |
| 8 | Ctrl+C exits cleanly | No tracebacks, devices released, process exits |

---

## Definition of Done

**You are ready to move to M3 when ALL of the following are true:**

- [ ] `whisperflow` starts a daemon that listens for a global hotkey
- [ ] Holding the hotkey records audio from your mic
- [ ] Releasing the hotkey transcribes and prints the result to stdout
- [ ] Audio feedback (start/stop beeps) plays correctly
- [ ] The hotkey works regardless of which application has focus
- [ ] Recordings under 0.3s are skipped with a message
- [ ] Ctrl+C exits the daemon cleanly
- [ ] Tests pass in CI
- [ ] Code passes `ruff check` and `ruff format --check`

---

## What NOT to Do in This Phase

- Do NOT implement text injection (clipboard paste) — that's M3. Just print to stdout for now.
- Do NOT implement the config file — use CLI flags and hardcoded defaults
- Do NOT try to handle keyboard hot-plug perfectly — basic detection at startup is fine
- Do NOT try to make the daemon run as a systemd service yet — foreground process is fine
- Do NOT implement the system tray icon — that's a stretch goal for M5

---

## Estimated Effort

**6–8 hours** — `evdev` has a learning curve, and coordinating async hotkey + audio recording takes some iteration to get right.

---

## Technical Notes

### evdev key event values

```python
# event.value meanings:
# 0 = key up (released)
# 1 = key down (pressed)
# 2 = key hold/repeat (ignore this)
```

### Common evdev key names

```python
from evdev import ecodes
ecodes.KEY_LEFTMETA    # Super/Windows key
ecodes.KEY_LEFTSHIFT   # Left Shift
ecodes.KEY_LEFTCTRL    # Left Ctrl
ecodes.KEY_LEFTALT     # Left Alt
ecodes.KEY_S           # S key
ecodes.KEY_SPACE       # Space bar
```

### Async evdev reading

```python
import asyncio
import evdev

async def listen(device):
    async for event in device.async_read_loop():
        if event.type == ecodes.EV_KEY:
            key_event = evdev.categorize(event)
            print(key_event.keycode, key_event.keystate)
```

### Coordinating hotkey + audio with asyncio

The daemon needs to:
1. Run the hotkey listener as a long-lived async task
2. When `on_press` fires, start audio recording (can be in a thread via `loop.run_in_executor`)
3. When `on_release` fires, stop recording, then transcribe
4. Transcription is CPU/GPU-bound — run in executor to avoid blocking the event loop

---

## Files to Create / Modify

| File | Action | Purpose |
|---|---|---|
| `src/whisperflow/hotkey.py` | Create | evdev global hotkey listener |
| `src/whisperflow/feedback.py` | Create | Audio feedback tones |
| `src/whisperflow/daemon.py` | Create | Main orchestration loop |
| `src/whisperflow/cli.py` | Modify | Wire `whisperflow` root command to daemon |
| `tests/test_hotkey.py` | Create | Hotkey listener tests |
| `tests/test_feedback.py` | Create | Feedback module tests |
| `pyproject.toml` | Modify | Add `evdev` dependency |
