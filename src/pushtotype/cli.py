"""CLI entry point for Push to Type."""

from __future__ import annotations

import asyncio
import logging
import time

import click
from faster_whisper import WhisperModel

from pushtotype import __version__
from pushtotype.audio import list_devices, record
from pushtotype.transcriber import Transcriber


def _configure_logging(verbose: bool, quiet: bool, log_file: str | None) -> None:
    level = logging.DEBUG if verbose else logging.WARNING if quiet else logging.INFO
    handlers: list[logging.Handler] = [logging.StreamHandler()]
    if log_file:
        handlers.append(logging.FileHandler(log_file))
    logging.basicConfig(level=level, format="%(name)s %(levelname)s %(message)s", handlers=handlers)


@click.group(invoke_without_command=True)
@click.version_option(version=__version__)
@click.option("--model", "model_name", default=None, help="Whisper model (overrides config).")
@click.option("--hotkey", default=None, help="Push-to-talk hotkey combo (overrides config).")
@click.option("--device", "audio_device", default=None, type=int, help="Audio device index.")
@click.option("--no-feedback", is_flag=True, default=False, help="Disable audio feedback tones.")
@click.option("-v", "--verbose", is_flag=True, default=False, help="Enable debug logging.")
@click.option("-q", "--quiet", is_flag=True, default=False, help="Suppress all but errors.")
@click.option("--log-file", default=None, type=click.Path(), help="Write logs to this file.")
@click.pass_context
def main(ctx, model_name, hotkey, audio_device, no_feedback, verbose, quiet, log_file):
    """Push to Type — real-time speech-to-text for Linux.

    Run without a subcommand to start the push-to-talk daemon.
    """
    _configure_logging(verbose, quiet, log_file)

    if ctx.invoked_subcommand is None:
        from pushtotype.config import load_config, validate_config
        from pushtotype.hotkey import normalize_hotkey_key

        cfg = load_config()

        # Warn about invalid config values
        for warning in validate_config(cfg):
            click.echo(f"  [config warning] {warning}", err=True)

        # CLI flags override config (only when explicitly provided)
        if model_name is not None:
            cfg["model"]["name"] = model_name
        if audio_device is not None:
            cfg["audio"]["device"] = audio_device
        if no_feedback:
            cfg["feedback"]["enabled"] = False

        # Build effective hotkey string
        if hotkey is not None:
            effective_hotkey = hotkey
        else:
            effective_hotkey = "+".join(normalize_hotkey_key(k) for k in cfg["hotkey"]["keys"])

        # Resolve audio device (int or None for default)
        raw_device = cfg["audio"]["device"]
        effective_device: int | None = None if raw_device == "default" else int(raw_device)

        from pushtotype.daemon import Daemon

        daemon = Daemon(
            model_name=cfg["model"]["name"],
            hotkey=effective_hotkey,
            audio_device=effective_device,
            feedback=cfg["feedback"]["enabled"],
            sample_rate=cfg["audio"]["sample_rate"],
            compute_type=cfg["model"]["compute_type"],
            model_device=cfg["model"]["device"],
            output_method=cfg["output"]["method"],
        )
        try:
            asyncio.run(daemon.run())
        except KeyboardInterrupt:
            pass


@main.command("config")
@click.option("--show", is_flag=True, help="Print current effective config without modifying it.")
def config_cmd(show):
    """Interactive setup wizard, or --show to print current config."""
    from pushtotype.config import config_path, load_config

    if show:
        import tomli_w

        cfg = load_config()
        click.echo(f"# Effective config  (file: {config_path()})\n")
        click.echo(tomli_w.dumps(cfg))
        return

    _run_wizard()


def _capture_hotkey_evdev() -> list[str] | None:
    """Block and capture a key combo via evdev. Returns KEY_* names or None on failure."""
    try:
        import evdev
        from evdev import ecodes

        from pushtotype.hotkey import find_keyboards

        keyboards = find_keyboards()
        if not keyboards:
            return None

        import select

        pressed: set[int] = set()
        combo_names: list[str] = []

        # Poll all keyboards so the event is caught regardless of which device it comes from.
        while True:
            readable, _, _ = select.select(keyboards, [], [], 10.0)
            if not readable:
                return None  # 10s timeout — fall back to text prompt
            for dev in readable:
                for event in dev.read():
                    if event.type != ecodes.EV_KEY:
                        continue
                    key = evdev.categorize(event)
                    if key.keystate == 1:  # key down
                        code = key.scancode
                        if code not in pressed:
                            pressed.add(code)
                            name = ecodes.KEY.get(code, f"KEY_{code}")
                            if isinstance(name, list):
                                name = name[0]
                            combo_names.append(name)
                            click.echo(f"    + {name}")
                    elif key.keystate == 0:  # key up
                        pressed.discard(key.scancode)
                        if not pressed and combo_names:
                            return combo_names
    except Exception:
        return None
    return None


def _run_wizard() -> None:
    """Interactive first-time setup wizard."""
    from pushtotype.config import config_path, load_config, save_config

    cfg = load_config()

    click.echo(f"Push to Type Setup Wizard  (config: {config_path()})")
    click.echo("=" * 55)

    # 1. Audio device
    click.echo("\n[1/4] Audio Input Device")
    devices = list_devices()
    if devices:
        for i, dev in enumerate(devices, 1):
            marker = "*" if dev["is_default"] else " "
            click.echo(f"  {marker} {i}. {dev['name']}")
        choice = click.prompt("  Select (Enter for default)", default="")
        if choice.strip().isdigit():
            idx = int(choice) - 1
            if 0 <= idx < len(devices):
                cfg["audio"]["device"] = devices[idx]["index"]
            else:
                cfg["audio"]["device"] = "default"
        else:
            cfg["audio"]["device"] = "default"
    else:
        click.echo("  No audio devices found — using default.")

    # 2. Hotkey
    click.echo("\n[2/3] Hotkey")
    click.echo("  Press and hold your desired hotkey combo, then release…")
    keys = _capture_hotkey_evdev()
    if keys:
        click.echo(f"  Captured: {' + '.join(keys)}")
        if click.confirm("  Use this hotkey?", default=True):
            cfg["hotkey"]["keys"] = keys
        else:
            keys = None

    if not keys:
        from pushtotype.hotkey import normalize_hotkey_key

        current = "+".join(normalize_hotkey_key(k) for k in cfg["hotkey"]["keys"])
        hotkey_str = click.prompt("  Hotkey combo", default=current)
        # Store as KEY_* format
        cfg["hotkey"]["keys"] = [
            k.upper() if k.upper().startswith("KEY_") else f"KEY_{k.upper()}"
            for k in hotkey_str.split("+")
        ]

    # 3. GPU detection
    click.echo("\n[3/3] GPU Detection")
    from pushtotype.transcriber import _resolve_device

    device, compute_type = _resolve_device("auto")
    click.echo(f"  Device:       {device}")
    click.echo(f"  Compute type: {compute_type}")

    # Feedback
    cfg["feedback"]["enabled"] = click.confirm("\nEnable audio feedback (beeps)?", default=True)

    # Save
    save_config(cfg)
    click.echo(f"\nConfig saved to: {config_path()}")
    click.echo("Run 'pushtotype' to start.")


@main.command()
def devices():
    """List available audio input devices."""
    devs = list_devices()
    if not devs:
        click.echo("No audio input devices found.")
        return

    click.echo("Audio Input Devices:")
    for dev in devs:
        marker = "*" if dev["is_default"] else " "
        click.echo(
            f"  {marker} {dev['index']}: {dev['name']} "
            f"[{dev['default_samplerate']} Hz, {dev['max_input_channels']} ch]"
        )


@main.command()
@click.option("--duration", default=5.0, show_default=True, help="Seconds to record.")
@click.option("--model", "model_name", default="base.en", show_default=True, help="Whisper model.")
@click.option("--device", "audio_device", default=None, type=int, help="Audio device index.")
def test(duration: float, model_name: str, audio_device):
    """Record a short clip and transcribe it (verify setup)."""
    click.echo(f"Recording for {duration:.0f} seconds… speak now!")
    t0 = time.perf_counter()
    audio = record(duration=duration, device=audio_device)
    recorded_s = time.perf_counter() - t0

    click.echo("Transcribing…")
    tx = Transcriber(model_name=model_name)
    t1 = time.perf_counter()
    text = tx.transcribe(audio)
    transcribed_s = time.perf_counter() - t1

    click.echo(f'Transcription: "{text}"')
    click.echo(
        f"Recorded: {recorded_s:.1f}s | "
        f"Transcribed in: {transcribed_s:.2f}s | "
        f"Model: {model_name} ({tx.device})"
    )


@main.command()
@click.argument("model_name", default="base.en")
def download(model_name: str):
    """Pre-download a Whisper model for offline use."""
    click.echo(f"Downloading model '{model_name}'… (this may take a moment)")
    WhisperModel(model_name, device="cpu", compute_type="int8")
    click.echo(f"Model '{model_name}' is ready.")
