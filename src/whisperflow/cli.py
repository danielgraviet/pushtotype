import time

import click
from faster_whisper import WhisperModel

from whisperflow import __version__
from whisperflow.audio import list_devices, record
from whisperflow.transcriber import Transcriber


@click.group()
@click.version_option(version=__version__)
def main():
    """WhisperFlow — real-time speech-to-text for Linux."""


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
