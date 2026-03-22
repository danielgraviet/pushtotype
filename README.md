# PushToType

> Hold a hotkey, speak, release — your words appear wherever your cursor is.

[![PyPI version](https://img.shields.io/pypi/v/pushtotype)](https://pypi.org/project/pushtotype/)
[![Python](https://img.shields.io/pypi/pyversions/pushtotype)](https://pypi.org/project/pushtotype/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![CI](https://github.com/danielgraviet/pushtotype/actions/workflows/ci.yml/badge.svg)](https://github.com/danielgraviet/pushtotype/actions)

PushToType is a local, real-time speech-to-text tool for Linux. It transcribes your voice using a local Whisper model and types the result directly into whatever application has focus — no clipboard, no cloud, no API keys.

An open-source alternative to OpenAI's Whisper Flow, which has no Linux support.

---

## Features

- **Works everywhere** — types into any focused app: browsers, editors, terminals, search bars
- **Local-only** — `faster-whisper` runs on your GPU (CUDA) with automatic CPU fallback
- **No cloud** — no API keys, no network required after the one-time model download
- **Fast** — ~250ms from hotkey release to text appearing
- **Configurable** — TOML config file, interactive setup wizard, CLI flags
- **Wayland + X11** — works on both display servers via `evdev`

---

## Quick Start

```bash
# Install
uv add pushtotype        # or: pip install pushtotype

# System dependencies (X11)
sudo apt install libportaudio2 xdotool

# Add yourself to the input group (required for hotkey detection)
sudo usermod -aG input $USER
# Log out and back in for this to take effect

# Run the setup wizard
pushtotype config

# Start
pushtotype
```

Hold your configured hotkey (default: right Ctrl), speak, release. Text appears at the cursor.

---

## How It Works

```
[Hold hotkey] → [Record audio] → [Whisper transcription] → [Type into focused app]
     evdev            sounddevice       faster-whisper           xdotool type
```

PushToType runs as a background daemon. A global hotkey listener (via `evdev`, reading directly from `/dev/input/`) fires a recording callback. When you release the hotkey, the audio is sent to `faster-whisper` for transcription, then `xdotool type` injects the text into whatever window is focused.

---

## Installation

### Recommended: uv

```bash
uv tool install pushtotype
```

### pip / pipx

```bash
pip install pushtotype
# or
pipx install pushtotype
```

### From source

```bash
git clone https://github.com/danielgraviet/pushtotype.git
cd pushtotype
uv pip install -e ".[dev]"
```

---

## System Requirements

| Requirement | Notes |
|---|---|
| Linux | X11 or Wayland |
| Python 3.10+ | |
| `libportaudio2` | `sudo apt install libportaudio2` |
| `xdotool` | X11 only — `sudo apt install xdotool` |
| `wtype` + `wl-clipboard` | Wayland only — `sudo apt install wtype wl-clipboard` |
| `input` group | `sudo usermod -aG input $USER` |
| NVIDIA GPU | Recommended for speed — CPU works but is slower |

---

## Configuration

Config file lives at `~/.config/pushtotype/config.toml`. Run `pushtotype config` to create it interactively.

```toml
[hotkey]
keys = ["KEY_RIGHTCTRL"]

[audio]
device = "default"
sample_rate = 16000

[model]
name = "base.en"
device = "auto"
compute_type = "float16"

[feedback]
enabled = true
volume = 0.5

[output]
method = "auto"   # "auto", "x11", or "wayland"
```

### Config priority (highest to lowest)

1. CLI flags (e.g. `--model small.en`)
2. Environment variables (e.g. `PUSHTOTYPE_MODEL=small.en`)
3. Config file (`~/.config/pushtotype/config.toml`)
4. Built-in defaults

### Environment variables

| Variable | Config key |
|---|---|
| `PUSHTOTYPE_MODEL` | `model.name` |
| `PUSHTOTYPE_DEVICE` | `model.device` |
| `PUSHTOTYPE_AUDIO_DEV` | `audio.device` |
| `PUSHTOTYPE_FEEDBACK` | `feedback.enabled` |
| `PUSHTOTYPE_HOTKEY` | `hotkey.keys` (comma-separated) |

---

## CLI Reference

```
pushtotype                  Start the push-to-talk daemon
pushtotype config           Run the interactive setup wizard
pushtotype config --show    Print the current effective config
pushtotype devices          List available audio input devices
pushtotype test             Record 5 seconds and transcribe (verify setup)
pushtotype download [MODEL] Pre-download a Whisper model
```

**Global flags:**

```
-v, --verbose     Enable debug logging (shows per-step timings)
-q, --quiet       Suppress all output except errors
--log-file PATH   Write logs to a file
--model NAME      Override model (e.g. small.en)
--hotkey COMBO    Override hotkey (e.g. ctrl+shift+s)
--device INDEX    Override audio device index
--no-feedback     Disable start/stop beeps
```

---

## Troubleshooting

**`Permission denied` on `/dev/input/`**

You need to be in the `input` group:
```bash
sudo usermod -aG input $USER
# Log out and back in
```

**`xdotool not found`**
```bash
sudo apt install xdotool
```

**Text doesn't appear in my terminal**

Terminals use `Ctrl+Shift+V` to paste, but PushToType uses `xdotool type` which bypasses the clipboard entirely — it should work in all terminals without any special config.

**CUDA not available**

PushToType automatically falls back to CPU. Transcription will be slower (~1-3s per 5s of audio vs ~0.2s on GPU). Check `pushtotype -v` startup output to see which device is being used.

**Model download fails / slow**

Models are cached in `~/.cache/huggingface/hub/` after the first download. Pre-download manually:
```bash
pushtotype download base.en
```

**`wtype` or `wl-copy` not found (Wayland)**
```bash
sudo apt install wtype wl-clipboard
```

---

## Known Limitations

- English only (`base.en` model)
- No AMD GPU (ROCm) support
- Wayland session detection relies on `XDG_SESSION_TYPE` or `WAYLAND_DISPLAY`
- No GUI — terminal only

---

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md). Issues and PRs welcome.

---

## License

[MIT](LICENSE)
