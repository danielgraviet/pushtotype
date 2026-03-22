"""Tests for the config module."""

from __future__ import annotations

import os
from unittest.mock import patch

from pushtotype.config import (
    DEFAULT_CONFIG,
    load_config,
    merge_config,
    save_config,
    validate_config,
)

# ---------------------------------------------------------------------------
# Default config structure
# ---------------------------------------------------------------------------


def test_default_config_has_required_sections():
    for section in ("general", "hotkey", "audio", "model", "feedback", "output"):
        assert section in DEFAULT_CONFIG, f"Missing section: {section}"


def test_default_config_has_expected_keys():
    assert "keys" in DEFAULT_CONFIG["hotkey"]
    assert "device" in DEFAULT_CONFIG["audio"]
    assert "sample_rate" in DEFAULT_CONFIG["audio"]
    assert "name" in DEFAULT_CONFIG["model"]
    assert "device" in DEFAULT_CONFIG["model"]
    assert "enabled" in DEFAULT_CONFIG["feedback"]
    assert "method" in DEFAULT_CONFIG["output"]


# ---------------------------------------------------------------------------
# merge_config
# ---------------------------------------------------------------------------


def test_merge_config_fills_missing_keys():
    defaults = {"a": {"x": 1, "y": 2}, "b": 3}
    overrides = {"a": {"x": 99}}
    result = merge_config(defaults, overrides)
    assert result["a"]["x"] == 99
    assert result["a"]["y"] == 2  # filled from defaults
    assert result["b"] == 3


def test_merge_config_does_not_mutate_defaults():
    defaults = {"a": {"x": 1}}
    overrides = {"a": {"x": 99}}
    merge_config(defaults, overrides)
    assert defaults["a"]["x"] == 1


def test_merge_config_override_wins():
    defaults = {"model": {"name": "base.en"}}
    overrides = {"model": {"name": "small.en"}}
    result = merge_config(defaults, overrides)
    assert result["model"]["name"] == "small.en"


# ---------------------------------------------------------------------------
# load_config — no file
# ---------------------------------------------------------------------------


def test_load_config_no_file_returns_defaults(tmp_path):
    fake_path = tmp_path / "nonexistent" / "config.toml"
    with patch("pushtotype.config.config_path", return_value=fake_path):
        cfg = load_config()
    assert cfg["model"]["name"] == DEFAULT_CONFIG["model"]["name"]
    assert cfg["hotkey"]["keys"] == DEFAULT_CONFIG["hotkey"]["keys"]


# ---------------------------------------------------------------------------
# load_config — partial file merges correctly
# ---------------------------------------------------------------------------


def test_load_config_partial_file_fills_defaults(tmp_path):
    toml_content = b'[model]\nname = "small.en"\n'
    cfg_file = tmp_path / "config.toml"
    cfg_file.write_bytes(toml_content)

    with patch("pushtotype.config.config_path", return_value=cfg_file):
        cfg = load_config()

    assert cfg["model"]["name"] == "small.en"
    # All other defaults should still be present
    assert cfg["audio"]["sample_rate"] == DEFAULT_CONFIG["audio"]["sample_rate"]
    assert cfg["feedback"]["enabled"] == DEFAULT_CONFIG["feedback"]["enabled"]


# ---------------------------------------------------------------------------
# save_config / round-trip
# ---------------------------------------------------------------------------


def test_save_config_creates_dir_and_file(tmp_path):
    cfg_file = tmp_path / "subdir" / "config.toml"
    with patch("pushtotype.config.config_path", return_value=cfg_file):
        save_config(DEFAULT_CONFIG)

    assert cfg_file.exists()


def test_save_config_round_trip(tmp_path):
    cfg_file = tmp_path / "config.toml"
    original = merge_config(DEFAULT_CONFIG, {"model": {"name": "small.en"}})

    with patch("pushtotype.config.config_path", return_value=cfg_file):
        save_config(original)
        loaded = load_config()

    assert loaded["model"]["name"] == "small.en"


# ---------------------------------------------------------------------------
# validate_config
# ---------------------------------------------------------------------------


def test_validate_config_valid_returns_empty():
    assert validate_config(DEFAULT_CONFIG) == []


def test_validate_config_invalid_model():
    cfg = merge_config(DEFAULT_CONFIG, {"model": {"name": "bogus-model"}})
    warnings = validate_config(cfg)
    assert any("bogus-model" in w for w in warnings)


def test_validate_config_invalid_device():
    cfg = merge_config(DEFAULT_CONFIG, {"model": {"device": "tpu"}})
    warnings = validate_config(cfg)
    assert any("tpu" in w for w in warnings)


def test_validate_config_invalid_output_method():
    cfg = merge_config(DEFAULT_CONFIG, {"output": {"method": "magic"}})
    warnings = validate_config(cfg)
    assert any("magic" in w for w in warnings)


# ---------------------------------------------------------------------------
# Env var overrides
# ---------------------------------------------------------------------------


def test_env_var_overrides_model(tmp_path):
    fake_path = tmp_path / "config.toml"
    with (
        patch("pushtotype.config.config_path", return_value=fake_path),
        patch.dict(os.environ, {"PUSHTYPE_MODEL": "large-v3"}),
    ):
        cfg = load_config()
    assert cfg["model"]["name"] == "large-v3"


def test_env_var_overrides_feedback_false(tmp_path):
    fake_path = tmp_path / "config.toml"
    with (
        patch("pushtotype.config.config_path", return_value=fake_path),
        patch.dict(os.environ, {"PUSHTYPE_FEEDBACK": "false"}),
    ):
        cfg = load_config()
    assert cfg["feedback"]["enabled"] is False
