# Milestone 1: Audio Capture + Transcription

> **Goal:** Record audio from the microphone and transcribe it to text using a local Whisper model. The `pushtotype test` command works end-to-end.

---

## Why This Phase Matters

This is the core value proposition of the entire project. If you can capture clean audio and turn it into accurate text locally on your GPU, everything else (hotkeys, text injection, config) is just plumbing around this pipeline. Get this right and you have a working product — the rest is UX.

---

## Prerequisites

- M0 is complete (project installs, CI is green)
- System dependencies installed:
  - `sudo apt install libportaudio2` (PortAudio for `sounddevice`)
- NVIDIA drivers + CUDA toolkit installed (for GPU acceleration)
  - Verify: `nvidia-smi` shows your RTX 2060

---

## Learning Objectives

By completing this milestone you will understand:

- How `sounddevice` captures raw audio as numpy arrays
- How audio sample rates and mono/stereo affect transcription quality
- How `faster-whisper` loads models and transcribes audio buffers
- The difference between Whisper model sizes and their speed/quality tradeoffs
- How CTranslate2 selects between CUDA and CPU backends
- How to structure a Python module with clean separation of concerns

---

## Tasks

### 1.1 — Add dependencies
- [ ] Add to `pyproject.toml`:

```toml
dependencies = [
    "click>=8.0",
    "sounddevice>=0.4.6",
    "numpy>=1.24",
    "faster-whisper>=1.0.0",
]
```

- [ ] Reinstall: `pip install -e ".[dev]"`
- [ ] Verify imports: `python -c "import sounddevice; import faster_whisper; print('OK')"`

### 1.2 — Audio capture module (`audio.py`)
- [ ] Create `src/pushtotype/audio.py` with:
  - `list_devices()` → returns list of input audio devices with names and indices
  - `record(duration: float, device=None, sample_rate=16000)` → records for N seconds, returns numpy array (float32, mono, 16kHz)
  - Proper error handling if no audio device is available
- [ ] Audio should be captured as 16kHz mono float32 — this is what Whisper expects

**Key design decisions:**
- Use `sounddevice.InputStream` with a callback to accumulate chunks into a buffer
- 16kHz sample rate, mono (1 channel), float32 dtype
- If the user's mic is stereo, downmix to mono
- Return a numpy array, not a file — we'll pass this directly to faster-whisper

### 1.3 — Transcriber module (`transcriber.py`)
- [ ] Create `src/pushtotype/transcriber.py` with:
  - `Transcriber` class that wraps `faster-whisper`:
    - `__init__(model_name="base.en", device="auto", compute_type="float16")` — loads the model
    - `transcribe(audio: np.ndarray) -> str` — transcribes audio buffer to text
  - `device="auto"` should prefer CUDA if available, fall back to CPU
  - When falling back to CPU, switch `compute_type` to `int8` automatically
- [ ] Model loading should happen once at init, not per-transcription
- [ ] Handle the case where the model hasn't been downloaded yet (faster-whisper auto-downloads, but we should log this clearly)

**Key design decisions:**
- `faster-whisper` accepts numpy arrays directly — no need to save to WAV
- Concatenate all segments into a single string with spaces
- Strip leading/trailing whitespace from output
- Log model load time and transcription time for debugging

### 1.4 — `pushtotype devices` command
- [ ] Implement in `cli.py`:
  - Lists all available audio input devices
  - Shows device index, name, default sample rate, max input channels
  - Marks the default device with an asterisk or similar indicator
- [ ] Example output:

```
Audio Input Devices:
  * 0: HDA Intel PCH: ALC892 Analog (hw:0,0) [48000 Hz, 2 ch]
    3: USB Microphone (hw:2,0) [44100 Hz, 1 ch]
```

### 1.5 — `pushtotype test` command
- [ ] Implement in `cli.py`:
  - Prints "Recording for 5 seconds... speak now!"
  - Records 5 seconds of audio from default device
  - Prints "Transcribing..."
  - Loads model and transcribes the audio
  - Prints the result: `Transcription: "whatever you said"`
  - Prints timing info: `Recorded: 5.0s | Transcribed in: 0.7s | Model: base.en (cuda)`
- [ ] Accept optional flags:
  - `--duration N` — record for N seconds (default 5)
  - `--model NAME` — use a specific model (default `base.en`)
  - `--device INDEX` — use a specific audio device

### 1.6 — `pushtotype download` command
- [ ] Implement in `cli.py`:
  - `pushtotype download` — downloads the default model (`base.en`)
  - `pushtotype download small.en` — downloads a specific model
  - Shows download progress or at minimum a "downloading..." message
  - Reports model size and location after download
- [ ] This is a convenience command so users can pre-download before going offline

### 1.7 — Tests
- [ ] `tests/test_audio.py`:
  - Test that `list_devices()` returns a list (may be empty in CI)
  - Test that `record()` returns a numpy array with correct dtype and sample rate
  - Mock `sounddevice` for CI environments without audio hardware
- [ ] `tests/test_transcriber.py`:
  - Test that `Transcriber` initializes (may need to skip if no GPU in CI)
  - Test that `transcribe()` returns a string
  - Test CPU fallback when CUDA is unavailable
  - Use a short synthetic audio array for testing (or a small pre-recorded fixture)

---

## Checkpoints

| # | Checkpoint | How to verify |
|---|---|---|
| 1 | Audio deps installed | `python -c "import sounddevice; import faster_whisper"` |
| 2 | Can list audio devices | `pushtotype devices` shows your mic |
| 3 | Can record audio | Run `pushtotype test --duration 3`, see "Recording..." message |
| 4 | Model downloads successfully | First run downloads `base.en`, subsequent runs load from cache |
| 5 | Transcription works on GPU | `pushtotype test` shows `(cuda)` in timing output |
| 6 | Transcription works on CPU | `pushtotype test --device cpu` falls back gracefully |
| 7 | Output is accurate | Say a clear sentence; transcription matches what you said |

---

## Definition of Done

**You are ready to move to M2 when ALL of the following are true:**

- [ ] `pushtotype test` records from your mic and prints accurate transcription
- [ ] `pushtotype devices` lists available audio input devices
- [ ] `pushtotype download` pre-downloads a model for offline use
- [ ] Transcription uses CUDA on your RTX 2060 and reports timing under 1s for 5s audio
- [ ] CPU fallback works when CUDA is not available
- [ ] Tests pass in CI (with appropriate mocking for audio/GPU)
- [ ] Code passes `ruff check` and `ruff format --check`

---

## What NOT to Do in This Phase

- Do NOT implement the hotkey listener — that's M2
- Do NOT implement text injection / clipboard — that's M3
- Do NOT implement config file loading — hardcoded defaults are fine for now
- Do NOT optimize for latency yet — correctness first
- Do NOT try to stream audio to the transcriber in real-time — batch after recording is simpler and what Whisper expects

---

## Estimated Effort

**4–6 hours** — most time will be spent understanding `faster-whisper` API and getting CUDA to work properly.

---

## Technical Notes

### faster-whisper API quick reference

```python
from faster_whisper import WhisperModel

model = WhisperModel("base.en", device="cuda", compute_type="float16")
segments, info = model.transcribe(audio_array, language="en")
text = " ".join(segment.text for segment in segments).strip()
```

### Audio format Whisper expects

- Sample rate: 16,000 Hz
- Channels: 1 (mono)
- Dtype: float32
- Range: -1.0 to 1.0

### Model storage location

`faster-whisper` caches models in `~/.cache/huggingface/hub/` by default. The `pushtotype download` command triggers this same download.

---

## Files to Create / Modify

| File | Action | Purpose |
|---|---|---|
| `src/pushtotype/audio.py` | Create | Mic capture via sounddevice |
| `src/pushtotype/transcriber.py` | Create | faster-whisper wrapper |
| `src/pushtotype/cli.py` | Modify | Add `test`, `devices`, `download` commands |
| `tests/test_audio.py` | Create | Audio module tests |
| `tests/test_transcriber.py` | Create | Transcriber module tests |
| `pyproject.toml` | Modify | Add new dependencies |
