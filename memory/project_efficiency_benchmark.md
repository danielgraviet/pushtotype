---
name: Efficiency benchmark milestone idea
description: User wants to demonstrate whisperflow's async efficiency vs thread-heavy tools
type: project
---

User wants a future milestone comparing whisperflow's resource usage against other voice-to-text tools (e.g. whisper-mic, nerd-dictation).

**Why:** whisperflow uses a single-threaded asyncio model — genuine story to tell about low idle CPU and memory vs thread-per-concern tools.

**How to apply:** Plan a `whisperflow bench` subcommand or dedicated milestone (M5/M6 candidate) that prints a live efficiency report. Metrics to cover:
- Memory: `/proc/<pid>/status` → `VmRSS`
- Idle CPU: `pidstat` or `top`
- Thread count: `/proc/<pid>/status` → `Threads`
- Latency: key release → transcription start
