# X11 Text Injection — xclip Hang Diagnosis and Fix

## The Problem

End-to-end latency from hotkey release to text appearing was 5-8 seconds, despite transcription being fast (0.2-0.5s). The printed stats showed `transcribed in 0.54s` — yet the text took several more seconds to appear, pointing to the injection step.

## Diagnosis

Added per-step `time.perf_counter()` timing inside `_inject_x11()` and a `-v/--verbose` CLI flag to enable DEBUG logging on demand. Output immediately revealed the culprit:

```
whisperflow.transcriber DEBUG Transcribed in 0.24s
whisperflow.injector DEBUG xclip write: 5.006s   ← timed out
whisperflow.injector DEBUG window class ('firefox'): 0.000s
whisperflow.injector DEBUG paste key: 0.002s
whisperflow.injector DEBUG inject total: 5.008s
```

The `xclip` write took **exactly 5.006s** — the subprocess timeout value. xclip was hanging, getting killed by the timeout, and the clipboard write was silently failing. The paste that followed was a no-op.

**Key tell: a step taking exactly N seconds where N is the timeout = subprocess hanging, not just slow.**

## Root Cause

`xclip -selection clipboard` forks a daemon to own the CLIPBOARD selection and serve SelectionRequest events. On this system it was not forking/exiting properly — the parent process hung until timeout. The exact trigger (clipboard manager conflict, display issue, etc.) wasn't traced further since switching away was faster and more reliable.

## Fix

Replaced the three-step clipboard flow with a single `xdotool type` call:

```
# Before (3 steps, ~5008ms)
xclip -selection clipboard       # write text to clipboard
xdotool getactivewindow          # detect if terminal (needs Ctrl+Shift+V)
xdotool key ctrl+v               # simulate paste

# After (1 step, ~27ms)
xdotool type --delay 0 --clearmodifiers -- <text>
```

`xdotool type` simulates keystrokes directly into the focused window — no clipboard involved.

## What Was Removed

The old approach required detecting the focused window class to distinguish terminals (Ctrl+Shift+V) from normal apps (Ctrl+V). With `xdotool type` that distinction is irrelevant, so the entire `DEFAULT_SHIFT_PASTE_APPS` list, window class detection, Xlib XTest paste simulation, and `xclip` dependency were all deleted. `TextInjector` went from ~170 lines to ~40.

## Result

```
whisperflow.transcriber DEBUG Transcribed in 0.23s
whisperflow.injector DEBUG xdotool type: 0.027s
```

Total post-release latency: ~250ms.
