"""Main daemon loop: hotkey → record → transcribe → inject."""

from __future__ import annotations

import asyncio
import glob
import logging
import shutil
import time

import numpy as np
import sounddevice as sd

from pushtotype import __version__
from pushtotype.feedback import play_error_sound, play_start_sound, play_stop_sound
from pushtotype.hotkey import HotkeyListener, parse_hotkey
from pushtotype.injector import TextInjector
from pushtotype.session import detect_session
from pushtotype.transcriber import Transcriber

logger = logging.getLogger(__name__)

MIN_RECORDING_SECONDS = 0.3


def _check_portaudio() -> tuple[bool, str]:
    try:
        import sounddevice  # noqa: F401

        return True, ""
    except Exception:
        return False, "sudo apt install libportaudio2"


def _check_evdev_permissions() -> tuple[bool, str]:
    devices = glob.glob("/dev/input/event*")
    if not devices:
        return False, "No /dev/input/event* devices found"
    try:
        with open(devices[0], "rb"):
            pass
        return True, ""
    except PermissionError:
        return False, "sudo usermod -aG input $USER  (then log out and back in)"
    except OSError:
        return False, f"Cannot open {devices[0]}"


def _check_injection_tools(session: str) -> tuple[bool, str]:
    if session == "x11":
        return (True, "") if shutil.which("xdotool") else (False, "sudo apt install xdotool")
    missing = [t for t in ("wtype", "wl-copy") if not shutil.which(t)]
    if not missing:
        return True, ""
    pkgs = []
    if "wtype" in missing:
        pkgs.append("wtype")
    if "wl-copy" in missing:
        pkgs.append("wl-clipboard")
    return False, f"sudo apt install {' '.join(pkgs)}"


def _check_cuda() -> tuple[bool, str]:
    try:
        # ctranslate2 is a faster-whisper dep, but CUDA support is optional.
        # get_supported_compute_types raises if the CUDA runtime isn't available.
        import ctranslate2

        if ctranslate2.get_supported_compute_types("cuda"):
            return True, ""
    except Exception:
        pass
    return False, "CPU will be used — no action needed"


def _print_check(label: str, passed: bool, detail: str = "", hint: str = "") -> None:
    mark = "✓" if passed else "✗"
    line = f"  {mark} {label:<14}{detail}"
    print(line)
    if not passed and hint:
        print(f"    → {hint}")


class Daemon:
    """Orchestrates hotkey listening, audio recording, transcription, and text injection."""

    def __init__(
        self,
        model_name: str = "base.en",
        hotkey: str = "rightctrl",
        audio_device: int | None = None,
        feedback: bool = True,
        sample_rate: int = 16000,
        compute_type: str = "float16",
        model_device: str = "auto",
        output_method: str = "auto",
    ) -> None:
        self.model_name = model_name
        self.hotkey_str = hotkey
        self.audio_device = audio_device
        self.feedback = feedback
        self.sample_rate = sample_rate
        self.compute_type = compute_type
        self.model_device = model_device

        self._recording = False
        self._frames: list[np.ndarray] = []
        self._stream: sd.InputStream | None = None
        self._record_start: float = 0.0
        self._transcriber: Transcriber | None = None
        self._injector = TextInjector(method=output_method)

    def _audio_callback(
        self,
        indata: np.ndarray,
        _frame_count: int,
        _time_info,
        _status,
    ) -> None:
        try:
            if self._recording:
                self._frames.append(indata.copy())
        except Exception:
            pass

    def _start_stream(self) -> None:
        self._stream = sd.InputStream(
            samplerate=self.sample_rate,
            channels=1,
            dtype="float32",
            device=self.audio_device,
            callback=self._audio_callback,
        )
        self._stream.start()

    def _stop_stream(self) -> None:
        if self._stream is not None:
            self._stream.stop()
            self._stream.close()
            self._stream = None

    def _on_press(self) -> None:
        if self._recording:
            return
        logger.debug("Hotkey pressed — starting recording.")
        self._frames = []
        self._recording = True
        self._record_start = time.perf_counter()
        play_start_sound(enabled=self.feedback)

    def _on_release(self) -> None:
        if not self._recording:
            return

        self._recording = False
        duration = time.perf_counter() - self._record_start
        logger.debug("Hotkey released — %.2fs recorded.", duration)

        play_stop_sound(enabled=self.feedback)

        if duration < MIN_RECORDING_SECONDS:
            print("Recording too short, skipping.")
            return

        if not self._frames:
            logger.warning("No audio captured.")
            play_error_sound(enabled=self.feedback)
            return

        audio = np.concatenate(self._frames, axis=0)
        if audio.ndim > 1:
            audio = audio.squeeze()
        audio = audio.astype(np.float32)

        loop = asyncio.get_event_loop()
        loop.create_task(self._transcribe(audio, duration))

    async def _transcribe(self, audio: np.ndarray, duration: float) -> None:
        loop = asyncio.get_event_loop()
        t0 = time.perf_counter()

        try:
            text = await loop.run_in_executor(
                None,
                self._transcriber.transcribe,  # type: ignore[union-attr]
                audio,
            )
        except Exception as exc:
            logger.exception("Transcription failed: %s", exc)
            play_error_sound(enabled=self.feedback)
            print(f"  [error: {exc}]")
            return

        elapsed = time.perf_counter() - t0

        await loop.run_in_executor(None, self._injector.inject, text)

        print(f"\n[pushtotype] {text}")
        print(
            f"  [{duration:.1f}s recorded | transcribed in {elapsed:.2f}s | "
            f"model: {self.model_name} ({self._transcriber.device})]"  # type: ignore[union-attr]
        )

    async def run(self) -> None:
        """Start the daemon: run checks, load model, then listen for hotkeys."""
        # First-run welcome
        from pushtotype.config import config_path

        if not config_path().exists():
            print("Welcome to Push to Type!")
            print("  No config file found. Running with defaults.")
            print("  Run 'pushtotype config' for guided setup.\n")

        # Validate hotkey before doing expensive work
        try:
            parse_hotkey(self.hotkey_str)
        except ValueError as exc:
            print(f"Invalid hotkey '{self.hotkey_str}': {exc}")
            return

        # Startup dependency checks
        session = detect_session()
        print(f"Push to Type v{__version__} — Startup Checks")
        _print_check("Audio", *_check_portaudio())
        _print_check("Input", *_check_evdev_permissions())
        _print_check("Session", True, session)
        _print_check("Injection", *_check_injection_tools(session))
        cuda_ok, cuda_hint = _check_cuda()
        _print_check("GPU", cuda_ok, "CUDA available" if cuda_ok else "no CUDA", cuda_hint)
        print()

        # Load model
        print(f"  Loading model '{self.model_name}'…", end=" ", flush=True)
        t0 = time.perf_counter()
        self._transcriber = Transcriber(
            model_name=self.model_name,
            device=self.model_device,
            compute_type=self.compute_type,
        )
        print(f"done ({time.perf_counter() - t0:.1f}s)")

        device_info = sd.query_devices(self.audio_device, "input")
        audio_name = device_info["name"] if device_info else "default"

        model_info = f"{self._transcriber.device}, {self._transcriber.compute_type}"
        print(f"  Model:     {self.model_name} ({model_info})")
        print(f"  Hotkey:    {self.hotkey_str}")
        print(f"  Audio:     {audio_name} ({self.sample_rate} Hz)")
        print()
        print(f"Ready. Hold [{self.hotkey_str}] to speak. Ctrl+C to quit.")

        self._start_stream()

        try:
            while True:
                listener = HotkeyListener(
                    keys=self.hotkey_str.split("+"),
                    on_press=self._on_press,
                    on_release=self._on_release,
                )
                await listener.run()
                logger.warning("Hotkey listener stopped. Retrying in 30s...")
                await asyncio.sleep(30)
        finally:
            self._stop_stream()
            print("\nPush to Type stopped.")
