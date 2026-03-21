"""Main daemon loop: hotkey → record → transcribe → print."""

from __future__ import annotations

import asyncio
import logging
import time

import numpy as np
import sounddevice as sd

from whisperflow import __version__
from whisperflow.feedback import play_error_sound, play_start_sound, play_stop_sound
from whisperflow.hotkey import HotkeyListener, find_keyboards, parse_hotkey
from whisperflow.injector import TextInjector
from whisperflow.session import detect_session
from whisperflow.transcriber import Transcriber

logger = logging.getLogger(__name__)

MIN_RECORDING_SECONDS = 0.3
SAMPLE_RATE = 16000


class Daemon:
    """
    Orchestrates hotkey listening, audio recording, and transcription.

    Usage::

        daemon = Daemon(model_name="base.en", hotkey="rightctrl")
        asyncio.run(daemon.run())
    """

    def __init__(
        self,
        model_name: str = "base.en",
        hotkey: str = "rightctrl",
        audio_device: int | None = None,
        feedback: bool = True,
    ) -> None:
        self.model_name = model_name
        self.hotkey_str = hotkey
        self.audio_device = audio_device
        self.feedback = feedback

        self._recording = False
        self._frames: list[np.ndarray] = []
        self._stream: sd.InputStream | None = None
        self._record_start: float = 0.0
        self._transcriber: Transcriber | None = None
        self._injector = TextInjector()

    def _audio_callback(
        self,
        indata: np.ndarray,
        frame_count: int,
        time_info,
        status,  # noqa: ARG002
    ) -> None:
        if self._recording:
            self._frames.append(indata.copy())

    def _start_stream(self) -> None:
        self._stream = sd.InputStream(
            samplerate=SAMPLE_RATE,
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

    # Hotkey callbacks

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

        # Collect frames
        if not self._frames:
            print("No audio captured.")
            return

        audio = np.concatenate(self._frames, axis=0)
        if audio.ndim > 1:
            audio = audio.squeeze()
        audio = audio.astype(np.float32)

        # Schedule transcription as a task so the event loop isn't blocked
        loop = asyncio.get_event_loop()
        loop.create_task(self._transcribe(audio, duration))

    async def _transcribe(self, audio: np.ndarray, duration: float) -> None:
        loop = asyncio.get_event_loop()
        t0 = time.perf_counter()

        try:
            text = await loop.run_in_executor(
                None,
                self._transcriber.transcribe,
                audio,  # type: ignore[arg-type]
            )

        except Exception as exc:
            logger.error("Transcription failed: %s", exc)
            play_error_sound(enabled=self.feedback)
            print(f"  [error: {exc}]")
            return

        elapsed = time.perf_counter() - t0

        await loop.run_in_executor(None, self._injector.inject, text)

        print(f"\n[whisperflow] {text}")
        print(
            f"  [{duration:.1f}s recorded | transcribed in {elapsed:.2f}s | "
            f"model: {self.model_name} ({self._transcriber.device})]"  # type: ignore[union-attr]
        )

    async def run(self) -> None:
        """Start the daemon: load model weights once into memory, then listen for hotkeys."""
        # Validate hotkey before doing expensive work
        try:
            parse_hotkey(self.hotkey_str.replace("+", "+"))
        except ValueError as exc:
            print(f"Invalid hotkey '{self.hotkey_str}': {exc}")
            return

        # Load model
        print(f"WhisperFlow v{__version__}")
        print(f"  Loading model '{self.model_name}'…", end=" ", flush=True)
        t0 = time.perf_counter()
        self._transcriber = Transcriber(model_name=self.model_name)
        print(f"done ({time.perf_counter() - t0:.1f}s)")

        keyboards = find_keyboards()
        device_info = sd.query_devices(self.audio_device, "input")
        audio_name = device_info["name"] if device_info else "default"

        model_info = f"{self._transcriber.device}, {self._transcriber.compute_type}"
        print(f"  Model:     {self.model_name} ({model_info})")
        print(f"  Hotkey:    {self.hotkey_str}")
        print(f"  Audio:     {audio_name} ({SAMPLE_RATE} Hz)")
        print(f"  Keyboards: {len(keyboards)} device(s) detected")
        print(f"  Session:   {detect_session()}")
        print()
        print(f"Ready. Hold [{self.hotkey_str}] to speak. Ctrl+C to quit.")

        self._start_stream()

        listener = HotkeyListener(
            keys=self.hotkey_str.split("+"),
            on_press=self._on_press,
            on_release=self._on_release,
        )

        try:
            await listener.run()
        finally:
            self._stop_stream()
            print("\nWhisperFlow stopped.")
