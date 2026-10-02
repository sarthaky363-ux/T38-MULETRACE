"""Test scaffolding and environment integrity."""
from pathlib import Path
import yaml
import pytest


def test_thresholds_file_exists_and_parses():
    """Verify thresholds.yaml exists and parses with all required presets."""
    root_dir = Path(__file__).resolve().parent.parent.parent
    thresholds_path = root_dir / "backend" / "config" / "thresholds.yaml"
    assert thresholds_path.exists(), f"Missing thresholds file: {thresholds_path}"

    with open(thresholds_path, "r", encoding="utf-8") as f:
        config = yaml.safe_load(f)

    assert "default_preset" in config
    assert config["default_preset"] == "balanced"
    assert "presets" in config

    presets = config["presets"]
    for preset_name in ["relaxed", "balanced", "strict"]:
        assert preset_name in presets, f"Preset {preset_name} missing from thresholds.yaml"
        preset = presets[preset_name]
        assert "fan_in_out" in preset
        assert "passthrough" in preset
        assert "cycles" in preset
        assert "sybil" in preset

    assert "scoring" in config
    scoring = config["scoring"]
    assert "base_points" in scoring
    assert "bonuses" in scoring
    assert "dampeners" in scoring
    assert "bands" in scoring


def test_directory_structure_exists():
    """Verify standard directories exist."""
    root_dir = Path(__file__).resolve().parent.parent.parent
    expected_dirs = [
        root_dir / "backend" / "config",
        root_dir / "backend" / "detectors",
        root_dir / "backend" / "evaluation",
        root_dir / "backend" / "tests",
        root_dir / "data" / "demo",
        root_dir / "frontend",
    ]
    for d in expected_dirs:
        assert d.exists(), f"Required directory {d} missing"
