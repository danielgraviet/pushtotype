# Milestone 3: Text Injection (System-Wide Output)

> **Goal:** After transcription, the text is automatically pasted into whatever application has focus — browser, terminal, editor, search box, anywhere.

---

## Why This Phase Matters

This is the milestone where WhisperFlow becomes actually usable for daily work. Up until now, transcriptions were just printed to the terminal. After this phase, you can hold a hotkey in any app, speak, and your words appear right where your cursor is. This is the "magic moment" — the feature that makes people say "I need this."

---

## Prerequisites

- M2 is complete (daemon runs, hotkey records and transcribes, output prints to stdout)
- System dependencies for your display server:
  - **X11:** `sudo apt install xdotool xclip`
  - **Wayland:** `sudo apt install wtype wl-clipboard`
- Check your session type: `echo $XDG_SESSION_TYPE` (should output `x11` or `wayland`)

---

## Learning Objectives

By completing this milestone you will understand:

- The difference between X11 and Wayland from an application automation perspective
- How clipboard operations work on Linux (X11 selections vs Wayland clipboard)
- How `xdotool` / `wtype` simulate keyboard input
- Why some apps (terminals) use different paste shortcuts
- How to detect the focused window and its class on X11
- How to architect a module that abstracts over multiple display server backends

---

## Tasks

### 3.1 — Session detection module (`session.py`)
- [ ] Create `src/whisperflow/session.py` with:
  - `detect_session() -> str` — returns `"x11"` or `"wayland"`
  - Reads `$XDG_SESSION_TYPE` environment variable
  - Falls back to checking for `$WAYLAND_DISPLAY` (set on Wayland sessions)
  - If neither is detected, default to `"x11"` with a warning
- [ ] `get_focused_window_class() -> str | None` (X11 only for now):
  - Uses `xdotool getactivewindow getwindowclassname` to get the WM_CLASS
  - Returns `None` on Wayland or if detection fails
  - This will be used for terminal paste detection

### 3.2 — Text injector module (`injector.py`)
- [ ] Create `src/whisperflow/injector.py` with:
  - `TextInjector` class:
    - `__init__(method="auto", shift_paste_apps=None)` — configures injection method
    - `inject(text: str)` — pastes text into the focused application
  - `method="auto"` calls `detect_session()` and uses the appropriate backend
  - `method="x11"` forces X11 tools
  - `method="wayland"` forces Wayland tools

**X11 implementation (`_inject_x11`):**
1. Save the current clipboard contents (so we can restore it after)
2. Copy the transcription text to clipboard via `xclip -selection clipboard`
3. Detect the focused window class via `xdotool`
4. If the window class is in `shift_paste_apps` (terminals), simulate `Ctrl+Shift+V`
5. Otherwise, simulate `Ctrl+V`
6. Wait a short delay (50ms) for the paste to complete
7. Restore the original clipboard contents

**Wayland implementation (`_inject_wayland`):**
1. Save current clipboard via `wl-paste` (best effort)
2. Copy text to clipboard via `wl-copy`
3. Simulate `Ctrl+V` via `wtype -M ctrl -k v`
4. Wait a short delay
5. Restore original clipboard

- [ ] Use `subprocess.run()` for all external tool calls
- [ ] Handle missing tools gracefully — if `xdotool` isn't installed, print a clear error message with install instructions

### 3.3 — Terminal detection
- [ ] Build a default list of known terminal window classes that use `Ctrl+Shift+V`:

```python
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
]
```

- [ ] On X11: check focused window class against this list before pasting
- [ ] On Wayland: window class detection is compositor-dependent and unreliable. For v1, use `Ctrl+Shift+V` as a configurable option, or default to `Ctrl+V` and document the terminal limitation

### 3.4 — Wire into the daemon
- [ ] Update `daemon.py`:
  - After transcription, call `injector.inject(text)` instead of `print(text)`
  - Still print the transcription to the daemon's stdout for debugging/logging
  - Handle injection errors gracefully (print warning, don't crash)
- [ ] The full flow is now:
  1. Hold hotkey → start sound → record
  2. Release hotkey → stop sound → transcribe → inject text at cursor
  3. Print transcription and timing to daemon stdout

### 3.5 — Clipboard safety
- [ ] Before injecting, save the current clipboard
- [ ] After injecting (with a small delay), restore the previous clipboard
- [ ] This prevents WhisperFlow from destroying whatever the user had copied
- [ ] If clipboard save/restore fails, proceed anyway — it's not critical

### 3.6 — End-to-end testing (manual)
- [ ] Test in these scenarios:
  - [ ] Text editor (e.g., `xed`, `gedit`, VS Code) — Ctrl+V should work
  - [ ] Browser URL bar — Ctrl+V should work
  - [ ] Browser text input (e.g., Google search, Claude chat) — Ctrl+V should work
  - [ ] Terminal emulator — should auto-detect and use Ctrl+Shift+V
  - [ ] Claude Code / terminal-based apps — verify paste works
  - [ ] File manager search — verify paste works

### 3.7 — Tests
- [ ] `tests/test_injector.py`:
  - Test session detection returns `"x11"` or `"wayland"`
  - Test that `_inject_x11` calls `xclip` and `xdotool` with correct arguments (mock subprocess)
  - Test that `_inject_wayland` calls `wl-copy` and `wtype` with correct arguments (mock subprocess)
  - Test terminal detection: known terminals → Ctrl+Shift+V, unknown apps → Ctrl+V
  - Test clipboard save/restore flow (mock subprocess)
  - Test graceful error when tools are missing (mock subprocess raising FileNotFoundError)
- [ ] `tests/test_session.py`:
  - Test `detect_session()` with mocked env vars
  - Test fallback behavior when neither env var is set

---

## Checkpoints

| # | Checkpoint | How to verify |
|---|---|---|
| 1 | Session detection works | `python -c "from whisperflow.session import detect_session; print(detect_session())"` prints `x11` |
| 2 | System tools available | `which xdotool xclip` returns paths (X11) |
| 3 | Clipboard copy works | Programmatically copy text, then Ctrl+V in an editor — text appears |
| 4 | Text injection works in editor | Hold hotkey in a text editor, speak, release — words appear at cursor |
| 5 | Text injection works in browser | Hold hotkey in browser search/input, speak, release — words appear |
| 6 | Terminal paste works | Hold hotkey in a terminal, speak, release — words appear (via Ctrl+Shift+V) |
| 7 | Clipboard is preserved | Copy something to clipboard, use WhisperFlow, then Ctrl+V — original clipboard is restored |
| 8 | Missing tools handled | Uninstall `xdotool`, run daemon — get clear error, not a crash |

---

## Definition of Done

**You are ready to move to M4 when ALL of the following are true:**

- [ ] Hold hotkey → speak → release → text appears at cursor in **any** focused application
- [ ] Terminal emulators are auto-detected and use Ctrl+Shift+V
- [ ] The user's clipboard is saved and restored after injection
- [ ] Missing system tools produce helpful error messages, not crashes
- [ ] The daemon prints transcriptions and timing to its own stdout for debugging
- [ ] End-to-end tested in at least: text editor, browser, terminal
- [ ] Tests pass in CI (with subprocess mocking)
- [ ] Code passes `ruff check` and `ruff format --check`

---

## What NOT to Do in This Phase

- Do NOT implement config file loading — hardcoded defaults and CLI flags are still fine
- Do NOT try to support every Wayland compositor's quirks — X11 is your primary target, Wayland is best-effort
- Do NOT implement xdg-desktop-portal integration — it's not ready for our use case
- Do NOT try to detect terminals on Wayland — just document the limitation for v1
- Do NOT over-engineer clipboard restore — best-effort is fine, edge cases are acceptable

---

## Estimated Effort

**4–6 hours** — the core implementation is straightforward subprocess calls. Most time will be spent on manual end-to-end testing across different apps and handling edge cases.

---

## Technical Notes

### X11 text injection commands

```bash
# Copy text to clipboard
echo -n "your text" | xclip -selection clipboard

# Get current clipboard
xclip -selection clipboard -o

# Simulate Ctrl+V
xdotool key --clearmodifiers ctrl+v

# Simulate Ctrl+Shift+V (for terminals)
xdotool key --clearmodifiers ctrl+shift+v

# Get focused window class
xdotool getactivewindow getwindowclassname
```

### Wayland text injection commands

```bash
# Copy text to clipboard
echo -n "your text" | wl-copy

# Get current clipboard
wl-paste

# Simulate Ctrl+V
wtype -M ctrl -k v

# Simulate Ctrl+Shift+V
wtype -M ctrl -M shift -k v
```

### Why clipboard-paste instead of virtual typing?

We use clipboard + paste shortcut instead of `xdotool type` / `wtype` character-by-character because:
- It's instant (no character-by-character delay)
- It handles special characters, unicode, punctuation correctly
- `xdotool type` is unreliable with some keyboard layouts
- It works with all input fields, including those that don't accept synthetic key events

The tradeoff is that we temporarily overwrite the clipboard, but we restore it afterward.

### xdotool `--clearmodifiers` flag

This is critical. If the user is still holding modifier keys (like the Super key from the hotkey combo), `xdotool key ctrl+v` would actually send `Super+Ctrl+V`. The `--clearmodifiers` flag temporarily releases all modifiers before sending the keystroke.

---

## Files to Create / Modify

| File | Action | Purpose |
|---|---|---|
| `src/whisperflow/session.py` | Create | X11/Wayland detection |
| `src/whisperflow/injector.py` | Create | Text injection via clipboard+paste |
| `src/whisperflow/daemon.py` | Modify | Wire injector into the transcription flow |
| `tests/test_injector.py` | Create | Injector tests with mocked subprocess |
| `tests/test_session.py` | Create | Session detection tests |
