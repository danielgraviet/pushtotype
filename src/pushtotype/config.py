"""Config loading, saving, and validation for Push to Type."""

from __future__ import annotations

import copy
import logging
import os
from pathlib import Path

logger = logging.getLogger(__name__)

try:
    import tomllib  # Python 3.11+
except ModuleNotFoundError:
    try:
        import tomli as tomllib  # type: ignore[no-redef]
    except ModuleNotFoundError:
        tomllib = None  # type: ignore[assignment]

DEFAULT_CONFIG: dict = {
    "general": {},
    "hotkey": {
        "keys": ["KEY_RIGHTCTRL"],
    },
    "audio": {
        "device": "default",
        "sample_rate": 16000,
    },
    "model": {
        "name": "base.en",
        "device": "auto",
        "compute_type": "float16",
    },
    "feedback": {
        "enabled": True,
        "volume": 0.5,
        "style": "custom",  # "custom" (default) | "beep" | "chirp" | "double"
    },
    "output": {
        "method": "auto",
    },
}

_KNOWN_MODELS = {
    "tiny",
    "tiny.en",
    "base",
    "base.en",
    "small",
    "small.en",
    "medium",
    "medium.en",
    "large-v1",
    "large-v2",
    "large-v3",
}
_KNOWN_DEVICES = {"auto", "cpu", "cuda"}
_KNOWN_METHODS = {"auto", "x11", "wayland"}
_KNOWN_SAMPLE_RATES = {8000, 16000, 22050, 44100}


def config_path() -> Path:
    """Return the path to the user config file."""
    return Path.home() / ".config" / "pushtotype" / "config.toml"


def merge_config(defaults: dict, overrides: dict) -> dict:
    """Deep-merge overrides into defaults. Overrides win; missing keys filled from defaults."""
    result = copy.deepcopy(defaults)
    for key, value in overrides.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = merge_config(result[key], value)
        else:
            result[key] = value
    return result


def load_config() -> dict:
    """Return the effective config: defaults → file → env vars."""
    cfg = copy.deepcopy(DEFAULT_CONFIG)

    path = config_path()
    if path.exists():
        if tomllib is None:
            logger.warning("tomllib/tomli not available — config file skipped.")
        else:
            try:
                with open(path, "rb") as f:
                    file_cfg = tomllib.load(f)
                cfg = merge_config(cfg, file_cfg)
            except Exception as exc:
                logger.warning("Could not read config %s: %s", path, exc)

    _apply_env_vars(cfg)
    return cfg


def _apply_env_vars(cfg: dict) -> None:
    """Apply PUSHTYPE_* environment variable overrides in-place."""
    if val := os.environ.get("PUSHTYPE_MODEL"):
        cfg["model"]["name"] = val
    if val := os.environ.get("PUSHTYPE_DEVICE"):
        cfg["model"]["device"] = val
    if val := os.environ.get("PUSHTYPE_AUDIO_DEV"):
        cfg["audio"]["device"] = int(val) if val.isdigit() else val
    if val := os.environ.get("PUSHTYPE_FEEDBACK"):
        cfg["feedback"]["enabled"] = val.lower() not in ("0", "false", "no")
    if val := os.environ.get("PUSHTYPE_HOTKEY"):
        cfg["hotkey"]["keys"] = val.split(",")


def save_config(cfg: dict) -> None:
    """Write config dict to the TOML file, creating the directory if needed."""
    import tomli_w

    path = config_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "wb") as f:
        tomli_w.dump(cfg, f)


def validate_config(cfg: dict) -> list[str]:
    """Return a list of warning strings for invalid/unknown config values."""
    warnings: list[str] = []

    model_name = cfg.get("model", {}).get("name", "")
    if model_name and model_name not in _KNOWN_MODELS:
        warnings.append(f"Unknown model: {model_name!r}. Known: {sorted(_KNOWN_MODELS)}")

    device = cfg.get("model", {}).get("device", "")
    if device and device not in _KNOWN_DEVICES:
        warnings.append(f"Unknown model device: {device!r}. Known: {sorted(_KNOWN_DEVICES)}")

    method = cfg.get("output", {}).get("method", "")
    if method and method not in _KNOWN_METHODS:
        warnings.append(f"Unknown output method: {method!r}. Known: {sorted(_KNOWN_METHODS)}")

    sample_rate = cfg.get("audio", {}).get("sample_rate")
    if sample_rate and sample_rate not in _KNOWN_SAMPLE_RATES:
        warnings.append(
            f"Unusual sample rate: {sample_rate}. Common: {sorted(_KNOWN_SAMPLE_RATES)}"
        )

    return warnings
