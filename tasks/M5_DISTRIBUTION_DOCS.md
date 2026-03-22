# Milestone 5: Distribution & Documentation

> **Goal:** PushToType is published on PyPI, has complete documentation, and is ready for other people to install and use.

---

## Why This Phase Matters

A tool that only works on your machine isn't a project — it's a script. This phase makes PushToType real: installable with one command, documented well enough that a stranger can set it up, and presented in a way that makes people want to try it. The README is your product's front door. The demo GIF is your elevator pitch. The PyPI listing is your distribution channel. This is where your project goes from "works for me" to "works for everyone."

---

## Prerequisites

- M4 is complete (config file, first-run experience, dependency checks, stable daemon)
- You've been using PushToType daily for at least a few sessions
- You have a list of bugs/friction from dogfooding (fix the critical ones first)

---

## Learning Objectives

By completing this milestone you will understand:

- How to publish a Python package to PyPI (and TestPyPI)
- How to write a README that converts visitors into users
- How to record and optimize demo GIFs for GitHub
- How to write installation docs that actually work for people with different setups
- How to write a CONTRIBUTING.md that invites participation
- How to structure troubleshooting docs that reduce support burden

---

## Tasks

### 5.1 — Fix dogfooding bugs
- [ ] Review your list of issues from daily use
- [ ] Fix any critical bugs (crashes, incorrect behavior)
- [ ] Fix any high-friction UX issues (confusing errors, awkward flows)
- [ ] Note known limitations that won't be fixed for v1 — these go in the docs

### 5.2 — Finalize pyproject.toml for publishing
- [ ] Ensure all metadata is complete:

```toml
[project]
name = "pushtotype"
version = "0.1.0"
description = "Real-time speech-to-text for Linux. Hold a hotkey, speak, release — your words appear wherever your cursor is."
readme = "README.md"
license = {text = "MIT"}
requires-python = ">=3.10"
authors = [{name = "Your Name", email = "you@example.com"}]
keywords = ["whisper", "speech-to-text", "linux", "transcription", "voice-typing"]
classifiers = [
    "Development Status :: 3 - Alpha",
    "Environment :: X11 Applications",
    "Intended Audience :: End Users/Desktop",
    "License :: OSI Approved :: MIT License",
    "Operating System :: POSIX :: Linux",
    "Programming Language :: Python :: 3",
    "Programming Language :: Python :: 3.10",
    "Programming Language :: Python :: 3.11",
    "Programming Language :: Python :: 3.12",
    "Topic :: Multimedia :: Sound/Audio :: Speech",
]

[project.urls]
Homepage = "https://github.com/yourname/pushtotype"
Documentation = "https://github.com/yourname/pushtotype#readme"
Repository = "https://github.com/yourname/pushtotype"
Issues = "https://github.com/yourname/pushtotype/issues"
```

- [ ] Verify `assets/` directory is included in the package (for feedback sounds)
- [ ] Add `include` directive if using hatchling:

```toml
[tool.hatch.build.targets.wheel]
packages = ["src/pushtotype"]
artifacts = ["src/pushtotype/assets/*"]
```

### 5.3 — Publish to TestPyPI first
- [ ] Build the package: `python -m build`
- [ ] Upload to TestPyPI: `twine upload --repository testpypi dist/*`
- [ ] Test install from TestPyPI in a fresh venv:

```bash
pip install --index-url https://test.pypi.org/simple/ --extra-index-url https://pypi.org/simple/ pushtotype
pushtotype --help
```

- [ ] Verify the CLI entry point works
- [ ] Verify assets are included in the installed package

### 5.4 — Publish to PyPI
- [ ] Create a PyPI account if you don't have one
- [ ] Set up API token authentication
- [ ] Upload: `twine upload dist/*`
- [ ] Verify install from PyPI in a fresh venv:

```bash
pip install pushtotype
pushtotype --help
```

- [ ] Also verify `pipx install pushtotype` and `uv tool install pushtotype` work

### 5.5 — README.md (complete rewrite)
- [ ] Structure the README with these sections:

**Header:**
- Project name + tagline
- Demo GIF (task 5.6)
- Badges: PyPI version, Python version, License, CI status

**What it does:**
- One-paragraph description
- Feature list (concise, scannable)

**Quick Start:**
```bash
# Install
pip install pushtotype

# System dependencies
sudo apt install libportaudio2 xdotool xclip

# Add yourself to the input group (for hotkey)
sudo usermod -aG input $USER
# Log out and back in

# Run setup wizard
pushtotype config

# Start!
pushtotype
```

**How it works:**
- Brief architecture explanation (1 paragraph + diagram)

**Configuration:**
- Config file location and format
- Table of all config options with descriptions and defaults

**CLI Reference:**
- All commands with examples

**Troubleshooting:**
- "Permission denied on /dev/input/" → input group fix
- "xdotool not found" → apt install
- "CUDA not available" → CPU fallback explanation
- "Text doesn't appear in [app]" → terminal paste issue
- "Model download fails" → offline/proxy instructions

**System Requirements:**
- Linux (X11 or Wayland)
- Python 3.10+
- NVIDIA GPU recommended (CPU works but slower)
- System dependencies table

**Known Limitations:**
- English only
- Wayland terminal paste detection not automatic
- No AMD GPU support
- etc.

**Contributing:**
- Link to CONTRIBUTING.md
- "Issues and PRs welcome"

**License:**
- MIT

### 5.6 — Record demo GIF
- [ ] Install a screen recorder that captures to GIF (e.g., `peek`, `gifcap`, or record + convert)
- [ ] Script the demo:
  1. Show a text editor and terminal side by side
  2. Terminal shows `pushtotype` starting up with green checkmarks
  3. Switch focus to text editor
  4. Hold hotkey (show a visual indicator or just the terminal logging)
  5. Speak a clear sentence
  6. Release — text appears in the editor
  7. Repeat in a browser search bar for variety
- [ ] Keep the GIF under 10MB (optimize with `gifsicle` if needed)
- [ ] Place at the top of the README

### 5.7 — CONTRIBUTING.md
- [ ] Write a contributing guide covering:
  - How to set up the development environment
  - How to run tests
  - Code style (ruff config)
  - How to submit issues (bug template)
  - How to submit PRs
  - Architecture overview (where does new code go?)
  - Areas where help is wanted (link to GitHub issues with "good first issue" label)

### 5.8 — GitHub repo polish
- [ ] Add GitHub issue templates:
  - Bug report (OS, Python version, session type, steps to reproduce)
  - Feature request
- [ ] Add a "good first issue" label
- [ ] Create issues for known future work (from the roadmap in PROJECT_PLAN.md)
- [ ] Add repo description and topics on GitHub (speech-to-text, linux, whisper, voice-typing, python)
- [ ] Pin the repo if it's on your profile

### 5.9 — System tray icon (stretch goal)
- [ ] If time permits, add a minimal system tray indicator:
  - Shows a microphone icon in the system tray
  - Green = idle/ready
  - Red = recording
  - Yellow = transcribing
  - Right-click menu: "Quit", "Open Config"
- [ ] Use `pystray` library (works on X11, partial Wayland support)
- [ ] This is optional — skip if it adds too much complexity

---

## Checkpoints

| # | Checkpoint | How to verify |
|---|---|---|
| 1 | Package builds | `python -m build` produces `.whl` and `.tar.gz` in `dist/` |
| 2 | TestPyPI install works | Fresh venv, `pip install` from TestPyPI, `pushtotype --help` runs |
| 3 | PyPI install works | `pip install pushtotype` in fresh venv, full end-to-end test |
| 4 | pipx works | `pipx install pushtotype` → `pushtotype --help` |
| 5 | README is complete | All sections present, no placeholder text, demo GIF displays |
| 6 | Demo GIF shows the magic | Someone watching the GIF understands what PushToType does in 10 seconds |
| 7 | Troubleshooting covers common issues | Test each troubleshooting scenario, verify the fix works |
| 8 | A friend can install it | Hand the README to someone unfamiliar, they get it running without your help |

---

## Definition of Done

**PushToType v0.1.0 is ready for release when ALL of the following are true:**

- [ ] Published on PyPI and installable via `pip install pushtotype`
- [ ] `pipx install pushtotype` and `uv tool install pushtotype` also work
- [ ] README has: description, demo GIF, quick start, config reference, troubleshooting
- [ ] CONTRIBUTING.md exists with dev setup instructions
- [ ] GitHub issues created for future roadmap items
- [ ] At least one person other than you has successfully installed and used it
- [ ] All tests pass in CI
- [ ] No critical bugs from dogfooding remain open

---

## What NOT to Do in This Phase

- Do NOT add new features — this is about shipping what you have
- Do NOT rewrite modules — if it works, document it and ship it
- Do NOT spend more than a day on the demo GIF — good enough is good enough
- Do NOT set up a documentation site (ReadTheDocs, etc.) — the README is sufficient for v1
- Do NOT wait for perfection — v0.1.0 is an alpha, ship it and iterate

---

## Estimated Effort

**6–10 hours** — writing good docs takes longer than you think, and the PyPI publishing pipeline has a learning curve on first run.

---

## Technical Notes

### Building and publishing

```bash
# Install build tools
pip install build twine

# Build
python -m build

# Upload to TestPyPI
twine upload --repository testpypi dist/*

# Upload to PyPI
twine upload dist/*
```

### Testing the install in a clean environment

```bash
# Create a fresh venv
python -m venv /tmp/test-pushtotype
source /tmp/test-pushtotype/bin/activate

# Install from PyPI
pip install pushtotype

# Test
pushtotype --help
pushtotype test --duration 3
pushtotype devices
```

### GIF recording with peek

```bash
sudo apt install peek
# Run peek, select screen area, record, save as GIF
# Optimize: gifsicle --optimize=3 --colors 128 demo.gif -o demo-optimized.gif
```

### Badge markdown for README

```markdown
[![PyPI version](https://img.shields.io/pypi/v/pushtotype)](https://pypi.org/project/pushtotype/)
[![Python](https://img.shields.io/pypi/pyversions/pushtotype)](https://pypi.org/project/pushtotype/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![CI](https://github.com/yourname/pushtotype/actions/workflows/ci.yml/badge.svg)](https://github.com/yourname/pushtotype/actions)
```

---

## Files to Create / Modify

| File | Action | Purpose |
|---|---|---|
| `README.md` | Rewrite | Complete project documentation |
| `CONTRIBUTING.md` | Create | Contributing guide |
| `pyproject.toml` | Modify | Finalize metadata for PyPI |
| `.github/ISSUE_TEMPLATE/bug_report.md` | Create | Bug report template |
| `.github/ISSUE_TEMPLATE/feature_request.md` | Create | Feature request template |
| `assets/demo.gif` | Create | Demo recording |
