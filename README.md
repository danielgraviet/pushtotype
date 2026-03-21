# WhisperFlow

> **Work in progress** — not yet functional.

A real-time speech-to-text tool for Linux that types anywhere. Hold a hotkey, speak, release — your words appear wherever your cursor is.

Open-source alternative to OpenAI's Whisper Flow, which has no Linux support.

---

## Vision

WhisperFlow captures microphone audio while a global hotkey is held, transcribes it using a local Whisper model on your GPU/CPU, and pastes the result into whatever application has focus — terminal, browser, editor, search bar, anything.

**No cloud. No API keys. No network required after model download.**

---

## Planned Features

- **Global push-to-talk hotkey** — configurable key combo (e.g. `Super+Shift+S`), works on X11 and Wayland via `evdev`
- **System-wide text injection** — pastes into any focused app (terminals, browsers, editors, etc.)
- **Local-only transcription** — `faster-whisper` on your GPU (CUDA) with automatic CPU fallback
- **Audio feedback** — subtle start/stop sounds so you know when recording is active
- **TOML config file** — hotkey, model size, audio device, all configurable
- **CLI interface** — `whisperflow`, `whisperflow test`, `whisperflow devices`, `whisperflow config`, `whisperflow download`

---

## Installation

```bash
pip install whisperflow  # coming soon
```

For now, install from source:

```bash
git clone https://github.com/danielgraviet/linux-whispr.git
cd linux-whispr
pip install -e ".[dev]"
```

---

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) (coming soon). Issues and PRs welcome.

---

## License

[MIT](LICENSE)
