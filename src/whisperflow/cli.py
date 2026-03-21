import click

from whisperflow import __version__


@click.group()
@click.version_option(version=__version__)
def main():
    """WhisperFlow — real-time speech-to-text for Linux."""


@main.command()
def test():
    """Record a short clip and transcribe it (verify setup)."""
    click.echo("Not yet implemented")


@main.command()
def devices():
    """List available audio input devices."""
    click.echo("Not yet implemented")
