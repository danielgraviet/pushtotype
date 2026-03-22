# Contributing to PushToType

Thanks for your interest in contributing. PushToType is a focused tool — the goal is to keep it simple, fast, and reliable.

---

## Development Setup

```bash
# Clone the repo
git clone https://github.com/danielgraviet/pushtotype.git
cd pushtotype

# Install with dev dependencies
uv pip install -e ".[dev]"

# Verify setup
uv run pytest tests/
uv run pushtotype test --duration 3
```

**System dependencies required for manual testing:**
```bash
sudo apt install libportaudio2 xdotool
sudo usermod -aG input $USER  # log out/in after
```

---

## Running Tests

```bash
uv run pytest tests/          # all tests
uv run pytest tests/ -v       # verbose
uv run pytest tests/ -q       # quiet
```

Tests use mocks for hardware (audio, evdev, GPU) so they run in CI without any devices attached.

---

## Code Style

PushToType uses [ruff](https://docs.astral.sh/ruff/) for linting and formatting.

```bash
uv run ruff check src/ tests/          # lint
uv run ruff format src/ tests/         # format
uv run ruff format --check src/ tests/ # check without changing
```

CI will fail if either check fails. Run both before submitting a PR.

---

## Architecture

```
src/pushtotype/
├── cli.py          Entry point — click commands, config wiring, wizard
├── daemon.py       Main loop — hotkey → record → transcribe → inject
├── config.py       TOML config loading, saving, validation, defaults
├── hotkey.py       evdev-based global hotkey listener (async)
├── transcriber.py  faster-whisper wrapper
├── injector.py     xdotool type (X11) / wtype (Wayland)
├── audio.py        sounddevice audio capture
├── feedback.py     Start/stop/error beep sounds
└── session.py      X11 / Wayland detection
```

**Data flow:**
1. `HotkeyListener` (evdev, async) fires `_on_press` / `_on_release` callbacks
2. `_on_release` concatenates recorded audio frames and schedules `_transcribe`
3. `_transcribe` runs `Transcriber.transcribe()` in a thread pool executor
4. Result is passed to `TextInjector.inject()` which calls `xdotool type`

---

## Where Help Is Wanted

Check the [issues](https://github.com/danielgraviet/pushtotype/issues) page for `good first issue` labels. Some areas:

- **Wayland improvements** — better session detection, testing on more compositors
- **AMD GPU support** — ROCm / DirectML via ctranslate2
- **Hotkey UX** — better evdev capture fallback for users not in the `input` group
- **Tests** — more coverage for daemon and CLI integration paths

---

## Submitting a PR

1. Fork the repo and create a branch from `master`
2. Make your changes
3. Run `uv run pytest tests/` and `uv run ruff check src/ tests/` — both must pass
4. Open a PR with a clear description of what changed and why

For larger changes, open an issue first to discuss the approach.

---

## Reporting Bugs

Use the [bug report template](.github/ISSUE_TEMPLATE/bug_report.md). Include:
- OS and display server (X11/Wayland)
- Python version
- Output of `pushtotype -v` startup block
- Steps to reproduce
