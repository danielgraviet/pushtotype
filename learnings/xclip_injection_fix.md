---
name: X11 text injection — xclip hang diagnosis and fix
description: How we diagnosed and fixed 5-8s injection latency caused by xclip hanging on clipboard write
type: project
---

## The Problem

End-to-end latency from hotkey release to text appearing was 5-8 seconds, despite transcription being fast (0.2-0.5s). The user's first clue was the printed stats: `transcribed in 0.54s` — yet the text took several more seconds to appear.

## Diagnosis

Added per-step debug timing inside `_inject_x11()` and a `-v/--verbose` CLI flag that enables DEBUG logging. Output immediately revealed the culprit:

```
whisperflow.transcriber DEBUG Transcribed in 0.24s
whisperflow.injector DEBUG xclip write: 5.006s   ← timed out
whisperflow.injector DEBUG window class ('firefox'): 0.000s
whisperflow.injector DEBUG paste key: 0.002s
whisperflow.injector DEBUG inject total: 5.008s
```

The `xclip` write was taking **exactly 5.006s** — the subprocess timeout value. xclip was hanging, being killed by the timeout, and the clipboard write was silently failing (the paste that followed was a no-op).

## Root Cause

`xclip -selection clipboard` forks a daemon process to "own" the CLIPBOARD selection and serve SelectionRequest events from apps. On this system, xclip was not forking/exiting properly and the parent process hung until the timeout killed it. The exact reason xclip hung (clipboard manager conflict, display connection issue, etc.) was not fully traced — switching away was faster and more reliable.

## Fix

Replaced the three-step clipboard flow (`xclip write` → `get_window_class` → `Ctrl+V`) with a single `xdotool type --delay 0 --clearmodifiers -- <text>` call. This types keystrokes directly into the focused window — no clipboard involved at all.

**Before:** `xclip` + window class detection + paste key simulation = 5008ms
**After:** `xdotool type` = ~27ms

## What Was Removed

The old approach (clipboard + paste) required:
- `xclip` for writing to clipboard
- `python-xlib` or `xdotool`/`xprop` for detecting focused window class (to distinguish terminals needing Ctrl+Shift+V vs normal apps needing Ctrl+V)
- Xlib XTest or `xdotool key` for simulating the paste shortcut
- `DEFAULT_SHIFT_PASTE_APPS` list for terminal detection

All of this was deleted. `TextInjector` is now ~40 lines vs ~170.

## Lesson: How to Diagnose Injection Latency

1. Add `time.perf_counter()` timing around each subprocess call in the injection path
2. Enable it via a `--verbose` / `-v` flag so it's available on demand without changing code
3. A step taking exactly N seconds (where N is the timeout value) = subprocess hanging, not just slow

## Files Changed

- `src/whisperflow/injector.py` — complete rewrite of X11 injection path
- `src/whisperflow/daemon.py` — removed window_class prefetch task
- `src/whisperflow/cli.py` — added `-v/--verbose` flag for debug logging
