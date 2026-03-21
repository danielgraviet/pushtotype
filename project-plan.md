# WhisperFlow — Project Plan

> A real-time speech-to-text tool for Linux that types anywhere.
> Open-source alternative to OpenAI's Whisper Flow, which has no Linux support.

---

## Vision

**One sentence:** Hold a hotkey, speak, release — your words appear wherever your cursor is.

WhisperFlow captures microphone audio while a global hotkey is held, transcribes it using a local Whisper model on your GPU/CPU, and pastes the result into whatever application has focus — terminal, browser, editor, search bar, anything.

---

## Target Hardware

Development and primary testing on:

| Component | Spec |
|---|---|
| GPU | NVIDIA GeForce RTX 2060 (6 GB VRAM) |
| CPU | AMD Ryzen 7 3700X 8-Core Processor |
| OS | Linux Mint Cinnamon (X11 default) |

**Model performance estimates on this hardware:**

| Model | VRAM Usage | Speed (10s audio) | Recommended For |
|---|---|---|---|
| `tiny.en` | ~1 GB | <0.5s | Fastest response, acceptable quality |
| `base.en` | ~1 GB | ~0.7s | **Default — best speed/quality balance** |
| `small.en` | ~2 GB | ~1.5s | Higher accuracy when needed |
| `medium.en` | ~5 GB | ~3s | Near-max VRAM, diminishing returns |

Default: `base.en` with `float16` on CUDA. Falls back to CPU automatically if no NVIDIA GPU detected.

---

## What We ARE Building (v1)

### Core Features

1. **Global push-to-talk hotkey** — user holds a configurable key combo (e.g., `Super+Shift+S`), speaks, releases, and the transcription is typed at the cursor position. Implemented via `evdev` at the kernel level, so it works on both X11 and Wayland.

2. **System-wide text injection** — transcribed text is pasted into the currently focused application via clipboard (`xdotool`+`xclip` for X11, `wtype`+`wl-copy` for Wayland) so it works everywhere: terminals, browsers, editors, Claude Code, search boxes, etc.

3. **Local-only transcription** — runs `faster-whisper` (CTranslate2) on-device. Supports NVIDIA GPU (CUDA) with automatic CPU fallback. No cloud dependencies, no API keys, no network required.

4. **Punctuation & basic formatting** — Whisper natively handles punctuation, capitalization, and sentence structure. We preserve this.

5. **Audio feedback** — subtle start/stop sounds so you know when recording is active.

6. **Configuration file** — TOML config at `~/.config/whisperflow/config.toml` for hotkey, model size, audio device, etc.

7. **CLI interface (primary):**
   - `whisperflow` — start the daemon (listens for hotkey)
   - `whisperflow config` — interactive config setup
   - `whisperflow test` — record a short clip and transcribe it (verify setup)
   - `whisperflow devices` — list available audio input devices
   - `whisperflow download` — pre-download a model

8. **System tray indicator** (stretch for v1) — minimal tray icon showing status (idle / recording / transcribing). Not a full GUI — just visual feedback.

### Non-Functional Requirements

- **English only** for v1
- **Linux only** (X11 and Wayland)
- **Python 3.10+**
- **Installable via `pip install whisperflow`** (also works with `pipx` and `uv tool install`)
- **Open source from day one** — MIT license, GitHub repo
- **No network required** — fully offline after initial model download

---

## What We Are NOT Building (v1)

These are explicitly out of scope. They may become future features, but they will not block v1.

| Feature | Why not v1 |
|---|---|
| **Cloud / API transcription** | Local-only keeps it simple, private, and fast. Users with GPUs don't need it. |
| **Speaker diarization** (who said what) | Adds complexity, different model pipeline, not needed for single-user dictation |
| **Custom vocabulary / jargon support** | Whisper doesn't natively support this well; would need post-processing hacks |
| **Noise cancellation / filtering** | Adds audio processing dependency; Whisper handles moderate noise acceptably |
| **GUI application** | CLI-first; a tray icon is the most UI we'll ship in v1 |
| **Batch file transcription** | Different use case; plenty of tools already do this |
| **Live streaming / URL transcription** | Out of scope; mic input only |
| **Multi-language support** | English-only simplifies testing and model selection |
| **macOS / Windows support** | This project exists because Linux has no Whisper Flow — stay focused |
| **Summarization / LLM post-processing** | Keep it pure transcription; users can pipe output elsewhere |
| **Wake word detection** | Push-to-talk is simpler and more reliable |
| **Docker / AppImage / .deb packaging** | PyPI is sufficient for v1; packaging adds maintenance burden |
| **AMD GPU (ROCm) support** | CTranslate2/faster-whisper ROCm support is immature; CPU fallback works |

---

## Architecture

```
┌──────────────────────────────────────────────────────┐
│                   whisperflow daemon                  │
│                                                      │
│  ┌───────────┐   ┌───────────┐   ┌───────────────┐  │
│  │  Hotkey    │──▶│  Audio    │──▶│  Transcriber  │  │
│  │ Listener   │   │ Capture   │   │ (faster-      │  │
│  │ (evdev)    │   │(sounddev) │   │  whisper)     │  │
│  └───────────┘   └───────────┘   └──────┬────────┘  │
│                                         │            │
│                                         ▼            │
│                                 ┌──────────────┐     │
│                                 │ Text Injector │     │
│                                 │ (clipboard +  │     │
│                                 │  paste combo) │     │
│                                 └──────────────┘     │
│                                                      │
│  ┌────────────────────────────────────────────────┐  │
│  │              Event Loop (asyncio)               │  │
│  └────────────────────────────────────────────────┘  │
└──────────────────────────────────────────────────────┘
```

### Components

| Component | Responsibility | Key Libraries |
|---|---|---|
| **Hotkey Listener** | Capture global key press/release via kernel input events | `python-evdev` (reads `/dev/input/`, works on X11 + Wayland) |
| **Audio Capture** | Record mic audio while hotkey is held | `sounddevice` (PortAudio wrapper) |
| **Transcriber** | Convert audio → text using local Whisper model | `faster-whisper` (CTranslate2, CUDA + CPU) |
| **Text Injector** | Paste text into focused app | `xdotool`+`xclip` (X11), `wtype`+`wl-copy` (Wayland) |
| **Config Manager** | Load/save/validate TOML config | `tomli` / `tomli-w` |
| **Audio Feedback** | Play start/stop sounds | `sounddevice` (reuse) |
| **Session Detector** | Detect X11 vs Wayland to choose injection method | `$XDG_SESSION_TYPE` env var |

### Data Flow

1. User presses hotkey → evdev listener fires "key down" event
2. Audio Capture begins recording from selected mic
3. Audio feedback: start sound plays
4. User releases hotkey → evdev listener fires "key up" event
5. Audio Capture stops, returns audio buffer (numpy array, 16kHz mono)
6. Audio buffer passed directly to `faster-whisper` (no file I/O)
7. Transcriber returns text string
8. Text Injector copies text to clipboard, simulates Ctrl+V in focused app
9. Audio feedback: stop/done sound plays

### Hotkey Implementation Detail

`evdev` reads input events at the kernel level from `/dev/input/` devices. This works regardless of display server (X11 or Wayland).

**Requirements for users:**
- User must be in the `input` group: `sudo usermod -aG input $USER` (then log out/in)
- `whisperflow` auto-detects keyboard devices on startup
- Hotkey uses key down/up events for push-to-talk (not key combos that need to be pressed simultaneously, though we support modifier+key combos too)

**Why evdev over alternatives:**
- `pynput`: X11 only, no Wayland support
- D-Bus GlobalShortcuts portal: GNOME rejects non-Flatpak apps, Cinnamon doesn't support it yet
- `evdev`: kernel-level, works everywhere, perfect press/release model for push-to-talk

---

## Tech Stack

| Layer | Choice | Rationale |
|---|---|---|
| Language | Python 3.10+ | Whisper ecosystem is Python-native; fast prototyping |
| STT Engine | `faster-whisper` | 4x faster than OpenAI Whisper, lower VRAM, CTranslate2 backend |
| Audio I/O | `sounddevice` | Thin PortAudio wrapper, numpy integration, cross-platform |
| Hotkey | `python-evdev` | Kernel-level input, works on X11 + Wayland, async support |
| Text injection (X11) | `xdotool` + `xclip` | Standard, well-tested X11 tools |
| Text injection (Wayland) | `wtype` + `wl-copy` | Standard wlroots Wayland tools |
| Config | TOML (`tomli`/`tomli-w`) | Python standard for config; human-readable |
| Packaging | `setuptools` / `hatchling` + PyPI | Standard Python distribution |
| CLI framework | `click` | Clean CLI structure with subcommands |
| Event loop | `asyncio` | Native async support in evdev; non-blocking architecture |

### System Dependencies

These must be installed by the user (not pip-installable):

| Dependency | Required | Install (Debian/Ubuntu/Mint) |
|---|---|---|
| PortAudio | Always | `sudo apt install libportaudio2` |
| xdotool | X11 sessions | `sudo apt install xdotool` |
| xclip | X11 sessions | `sudo apt install xclip` |
| wtype | Wayland sessions | `sudo apt install wtype` |
| wl-clipboard | Wayland sessions | `sudo apt install wl-clipboard` |
| CUDA toolkit | GPU acceleration | Already installed with NVIDIA drivers typically |

---

## Milestones

### M0: Project Setup (Day 1)
- [ ] Create GitHub repo with MIT license
- [ ] Set up project structure (`src/whisperflow/`)
- [ ] `pyproject.toml` with dependencies and entry points
- [ ] Basic README with project description and vision
- [ ] CI: GitHub Actions for linting (`ruff`) and tests (`pytest`)

### M1: Audio Capture + Transcription (Core Pipeline)
- [ ] Record audio from default mic for N seconds → numpy array
- [ ] Transcribe with `faster-whisper` (CUDA, `base.en`)
- [ ] Automatic CPU fallback if no CUDA available
- [ ] `whisperflow test` command works end-to-end
- [ ] `whisperflow devices` lists audio inputs
- [ ] `whisperflow download [model]` pre-downloads a model

### M2: Global Hotkey + Push-to-Talk
- [ ] `evdev` keyboard device auto-detection
- [ ] Hold-to-record: audio capture starts on key down, stops on key up
- [ ] Support modifier+key combos (e.g., Super+Shift+S)
- [ ] Audio buffer handed to transcriber on release
- [ ] Basic audio feedback (start/stop beeps)
- [ ] Helpful error if user not in `input` group

### M3: Text Injection (System-Wide Output)
- [ ] Detect X11 vs Wayland via `$XDG_SESSION_TYPE`
- [ ] X11: copy to clipboard via `xclip`, simulate Ctrl+V via `xdotool`
- [ ] Wayland: copy via `wl-copy`, simulate via `wtype`
- [ ] Handle edge cases (terminals that use Ctrl+Shift+V)
- [ ] End-to-end: hold hotkey → speak → text appears at cursor

### M4: Configuration & Polish
- [ ] TOML config file with sensible defaults
- [ ] `whisperflow config` interactive setup (pick device, model, hotkey)
- [ ] Model download management with progress bar on first run
- [ ] Graceful error messages for missing system deps
- [ ] Daemon mode: runs in background, logs to file

### M5: Distribution & Docs
- [ ] Publish to PyPI as `whisperflow`
- [ ] README: installation, quickstart, configuration reference, troubleshooting
- [ ] CONTRIBUTING.md
- [ ] Record a demo GIF/video for the README
- [ ] System tray icon (stretch goal)

---

## Project Structure

```
whisperflow/
├── src/
│   └── whisperflow/
│       ├── __init__.py          # version
│       ├── __main__.py          # python -m whisperflow
│       ├── cli.py               # click CLI commands
│       ├── config.py            # TOML config loading/saving/defaults
│       ├── audio.py             # mic capture via sounddevice
│       ├── transcriber.py       # faster-whisper wrapper
│       ├── hotkey.py            # evdev global hotkey listener
│       ├── injector.py          # text injection (X11/Wayland)
│       ├── session.py           # X11/Wayland detection
│       ├── feedback.py          # audio feedback sounds
│       └── daemon.py            # asyncio main loop orchestrating everything
├── tests/
│   ├── test_audio.py
│   ├── test_transcriber.py
│   ├── test_config.py
│   ├── test_hotkey.py
│   └── test_injector.py
├── assets/
│   ├── start.wav                # recording start sound
│   └── stop.wav                 # recording stop sound
├── pyproject.toml
├── README.md
├── LICENSE                      # MIT
├── CONTRIBUTING.md
└── PROJECT_PLAN.md              # this file
```

---

## Configuration Reference

```toml
# ~/.config/whisperflow/config.toml

[general]
language = "en"

[hotkey]
# Key combo for push-to-talk
# Use evdev key names: KEY_LEFTMETA, KEY_LEFTSHIFT, KEY_S, etc.
# Run `whisperflow config` to set this interactively
keys = ["KEY_LEFTMETA", "KEY_LEFTSHIFT", "KEY_S"]

[audio]
device = "default"          # or device name/index from `whisperflow devices`
sample_rate = 16000

[model]
name = "base.en"            # tiny.en, base.en, small.en, medium.en
device = "auto"             # "auto" (prefers cuda), "cpu", or "cuda"
compute_type = "float16"    # float16 (gpu), int8 (cpu), float32

[feedback]
enabled = true
volume = 0.5

[output]
# How to inject text
method = "auto"             # "auto" (detect session), "x11", "wayland"
# Some terminals use Ctrl+Shift+V instead of Ctrl+V
# Add window class names here if paste doesn't work
shift_paste_apps = ["gnome-terminal", "xfce4-terminal", "tilix"]
```

---

## Open Questions

1. **Terminal paste detection** — terminals typically use Ctrl+Shift+V instead of Ctrl+V. We could detect the focused window class and switch behavior, or just document it. What's the best UX here?

2. **Model download UX** — `faster-whisper` auto-downloads from HuggingFace on first use. Should we wrap this with a progress bar in `whisperflow download`, or let it happen on first transcription?

3. **Latency budget** — with `base.en` on the RTX 2060, transcription itself is ~0.7s for 10s of audio. Total end-to-end (stop recording → text appears) should be under 1.5s. Is that acceptable?

4. **Multiple keyboards** — `evdev` sees all input devices. Should we listen to all keyboards, or let the user pick one? Listening to all is simpler and handles USB keyboards being plugged/unplugged.

5. **Minimum audio length** — should we skip transcription if the recording is very short (e.g., <0.3s)? This would prevent accidental triggers from quick key taps.

---

## Future Roadmap (Post-v1)

These are things we'd love to build but won't block the initial release:

- **Multi-language support** — leverage Whisper's multilingual models
- **Cloud API backend** — optional OpenAI Whisper API for users without GPUs
- **Voice activity detection** — auto-detect speech start/stop instead of push-to-talk
- **System tray GUI** — full tray app with settings, history, model management
- **Custom vocabulary** — post-processing with word lists for domain-specific jargon
- **Noise filtering** — pre-process audio with noise reduction before transcription
- **Speaker diarization** — identify different speakers
- **Continuous mode** — always-listening with automatic segmentation
- **Clipboard history** — keep a log of recent transcriptions
- **AMD ROCm support** — when faster-whisper/CTranslate2 matures on ROCm
- **macOS / Windows ports** — if demand exists