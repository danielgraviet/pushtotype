# Milestone 4: Configuration & Polish

> **Goal:** PushToType loads settings from a config file, guides first-time users through setup, handles errors gracefully, and runs reliably as a background daemon.

---

## Why This Phase Matters

After M3, PushToType works — but everything is hardcoded. Users have to pass CLI flags every time, there's no first-run experience, and errors can be confusing. This phase makes PushToType feel like a finished tool: config files persist settings, first-run setup walks you through choices, and error messages actually help you fix problems. This is the difference between "a script that works" and "software I'd recommend to someone."

---

## Prerequisites

- M3 is complete (full end-to-end flow: hotkey → record → transcribe → inject text)
- You've been dogfooding PushToType and have a list of friction points

---

## Learning Objectives

By completing this milestone you will understand:

- How to design a layered config system (defaults → file → env vars → CLI flags)
- How TOML config files work and how to read/write them in Python
- How to build interactive CLI setup wizards with `click`
- How to write defensive code that fails gracefully with helpful messages
- How to run a Python process as a background daemon with proper logging
- How to validate user configuration and report errors clearly

---

## Tasks

### 4.1 — Config module (`config.py`)
- [ ] Create `src/pushtotype/config.py` with:
  - `DEFAULT_CONFIG` — a dict with all default values:

```python
DEFAULT_CONFIG = {
    "general": {
        "language": "en",
    },
    "hotkey": {
        "keys": ["KEY_LEFTMETA", "KEY_LEFTSHIFT", "KEY_S"],
    },
    "audio": {
        "device": "default",
        "sample_rate": 16000,
    },
    "model": {
        "name": "base.en",
        "device": "auto",
        "compute_type": "float16",
    },
    "feedback": {
        "enabled": True,
        "volume": 0.5,
    },
    "output": {
        "method": "auto",
        "shift_paste_apps": [
            "gnome-terminal", "gnome-terminal-server",
            "xfce4-terminal", "tilix", "terminator",
            "mate-terminal", "kitty", "alacritty", "wezterm",
        ],
    },
}
```

  - `config_path() -> Path` — returns `~/.config/pushtotype/config.toml`
  - `load_config() -> dict` — loads config from file, merges with defaults (defaults fill any missing keys)
  - `save_config(config: dict)` — writes config to TOML file, creates directory if needed
  - `validate_config(config: dict) -> list[str]` — returns a list of warnings/errors (e.g., invalid model name, unknown key names)

- [ ] **Config priority (highest to lowest):**
  1. CLI flags (e.g., `--model small.en`)
  2. Environment variables (e.g., `PUSHTYPE_MODEL=small.en`)
  3. Config file (`~/.config/pushtotype/config.toml`)
  4. Built-in defaults

- [ ] Add `tomli` (read) and `tomli-w` (write) to dependencies:

```toml
"tomli>=2.0; python_version < '3.11'",
"tomli-w>=1.0",
```

Note: Python 3.11+ has `tomllib` in the stdlib for reading. Use `tomli` for 3.10 compat.

### 4.2 — Interactive setup (`pushtotype config`)
- [ ] Implement `pushtotype config` as an interactive wizard:
  1. **Audio device selection:**
     - List available devices (from `audio.list_devices()`)
     - Let user pick by number, or press Enter for default
  2. **Model selection:**
     - Show model options with size/speed estimates
     - Let user pick, default to `base.en`
     - Offer to download the selected model now
  3. **Hotkey configuration:**
     - Prompt: "Press the key combination you want to use for push-to-talk..."
     - Use evdev to listen for a key combo, display what was pressed
     - Confirm with user
  4. **GPU detection:**
     - Auto-detect CUDA availability
     - Show which device will be used (cuda/cpu)
     - If CUDA available, recommend `float16`; if CPU, recommend `int8`
  5. **Save config:**
     - Write to `~/.config/pushtotype/config.toml`
     - Print the file path and a summary

- [ ] `pushtotype config --show` — prints current effective config (merged defaults + file + env) without modifying anything

### 4.3 — Wire config into all modules
- [ ] Update `daemon.py` to load config on startup:
  - Load config file, merge with defaults
  - Override with CLI flags where provided
  - Pass relevant config sections to each module
- [ ] Update `cli.py`:
  - All CLI flags should have `default=None` so they don't override config file values unless explicitly set
  - Print effective config on daemon startup (model, hotkey, device, session type)
- [ ] Update all modules to accept config values instead of hardcoded defaults

### 4.4 — First-run experience
- [ ] If no config file exists when `pushtotype` starts:
  - Print a welcome message
  - Suggest running `pushtotype config` for guided setup
  - Continue with defaults (don't block the user)
- [ ] If the model hasn't been downloaded yet:
  - Print "Downloading model base.en... (this only happens once)"
  - Show download progress
  - Continue after download completes

### 4.5 — Dependency checking
- [ ] On daemon startup, check for required system dependencies:
  - PortAudio: try `import sounddevice` — if it fails, suggest `apt install libportaudio2`
  - evdev permissions: try reading from `/dev/input/` — if permission denied, suggest `input` group
  - X11 tools (if X11 session): check `xdotool` and `xclip` exist on PATH
  - Wayland tools (if Wayland session): check `wtype` and `wl-copy` exist on PATH
  - CUDA: try loading a model on CUDA — if fails, note CPU fallback
- [ ] Print a clear status block on startup:

```
PushToType v0.1.0 — Startup Checks
  ✓ Audio:      libportaudio2 found
  ✓ Input:      /dev/input/ accessible (input group)
  ✓ Session:    X11 detected
  ✓ Injection:  xdotool + xclip found
  ✓ GPU:        NVIDIA RTX 2060 (CUDA)
  ✓ Model:      base.en loaded (float16, 0.3s)
```

- [ ] If a check fails, print the issue AND how to fix it:

```
  ✗ Injection:  xdotool not found
    → Install: sudo apt install xdotool
```

### 4.6 — Logging
- [ ] Add proper logging throughout the application:
  - Use Python's `logging` module
  - Default level: `INFO` (prints startup info, transcriptions, timing)
  - `--verbose` / `-v` flag: sets to `DEBUG` (prints evdev events, audio buffer sizes, etc.)
  - `--quiet` / `-q` flag: sets to `WARNING` (only print errors)
- [ ] Log to both stderr and optionally a file:
  - `--log-file PATH` flag for daemon mode
  - Default: stderr only

### 4.7 — Daemon robustness
- [ ] Handle errors during transcription without crashing:
  - If transcription fails, log the error and play error sound
  - Continue listening for the next hotkey press
- [ ] Handle audio device disconnection:
  - If recording fails, log error and play error sound
  - Continue listening
- [ ] Handle keyboard disconnection:
  - If evdev device becomes unavailable, log warning
  - Attempt to re-detect keyboards periodically (every 30s)

### 4.8 — Tests
- [ ] `tests/test_config.py`:
  - Test default config has all required keys
  - Test `load_config()` with no file returns defaults
  - Test `load_config()` with partial file merges correctly (missing keys filled from defaults)
  - Test `save_config()` creates directory and writes valid TOML
  - Test `validate_config()` catches invalid model names
  - Test config priority: CLI > env > file > defaults
- [ ] Update existing tests to use config where appropriate

---

## Checkpoints

| # | Checkpoint | How to verify |
|---|---|---|
| 1 | Config file created | `pushtotype config` creates `~/.config/pushtotype/config.toml` |
| 2 | Config loads correctly | `pushtotype config --show` prints merged config |
| 3 | CLI flags override config | `pushtotype --model small.en` uses small.en even if config says base.en |
| 4 | First-run works | Delete config file, run `pushtotype` — see welcome message, runs with defaults |
| 5 | Dep checks pass | Startup shows green checkmarks for all dependencies |
| 6 | Dep check failures are helpful | Uninstall `xdotool`, start daemon — see clear error with fix instructions |
| 7 | Logging works | `pushtotype -v` shows debug output; `pushtotype -q` shows only errors |
| 8 | Daemon survives errors | Simulate a transcription error — daemon continues running |

---

## Definition of Done

**You are ready to move to M5 when ALL of the following are true:**

- [ ] `pushtotype config` walks through interactive setup and saves to TOML file
- [ ] `pushtotype config --show` displays the effective config
- [ ] Config file values are used when no CLI flags are provided
- [ ] CLI flags override config file values
- [ ] First-run experience shows a welcome message and continues with defaults
- [ ] Startup dependency checks print clear status with fix instructions for failures
- [ ] Logging works at INFO, DEBUG, and WARNING levels
- [ ] Daemon recovers from transcription and audio errors without crashing
- [ ] Tests pass in CI
- [ ] Code passes `ruff check` and `ruff format --check`

---

## What NOT to Do in This Phase

- Do NOT build a GUI settings panel — the interactive CLI wizard is sufficient
- Do NOT implement auto-start on login (systemd service) — document it, but don't automate it yet
- Do NOT over-validate config — warn about unknown keys, don't reject them (forward compatibility)
- Do NOT support config hot-reloading — restart the daemon to pick up changes

---

## Estimated Effort

**6–8 hours** — the config module itself is straightforward, but the interactive setup wizard, dependency checking, and error handling add up.

---

## Technical Notes

### TOML reading (Python 3.10 compatible)

```python
try:
    import tomllib  # Python 3.11+
except ModuleNotFoundError:
    import tomli as tomllib  # Python 3.10

with open(path, "rb") as f:
    config = tomllib.load(f)
```

### TOML writing

```python
import tomli_w

with open(path, "wb") as f:
    tomli_w.dump(config, f)
```

### Config merge strategy

```python
def merge_config(defaults: dict, overrides: dict) -> dict:
    """Deep merge overrides into defaults. Overrides win."""
    result = defaults.copy()
    for key, value in overrides.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = merge_config(result[key], value)
        else:
            result[key] = value
    return result
```

### Interactive hotkey capture

```python
import evdev

def capture_hotkey():
    """Listen for a key combo and return the key names."""
    devices = [evdev.InputDevice(p) for p in evdev.list_devices()]
    keyboards = [d for d in devices if evdev.ecodes.EV_KEY in d.capabilities()]
    
    print("Press your desired hotkey combo (hold all keys, then release)...")
    pressed = set()
    # Read events, track pressed keys, return when all released
```

---

## Files to Create / Modify

| File | Action | Purpose |
|---|---|---|
| `src/pushtotype/config.py` | Create | Config loading, saving, validation, defaults |
| `src/pushtotype/cli.py` | Modify | Add `config` subcommand, wire config into all commands |
| `src/pushtotype/daemon.py` | Modify | Load config on startup, dependency checks, logging |
| `src/pushtotype/hotkey.py` | Modify | Accept config values instead of hardcoded defaults |
| `src/pushtotype/transcriber.py` | Modify | Accept config values |
| `src/pushtotype/audio.py` | Modify | Accept config values |
| `src/pushtotype/injector.py` | Modify | Accept config values |
| `tests/test_config.py` | Create | Config module tests |
| `pyproject.toml` | Modify | Add `tomli`, `tomli-w` dependencies |
