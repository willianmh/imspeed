from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, Optional

from pydantic import BaseModel
import yaml

class AnimationSettings(BaseModel):
    gpx_file: Path
    output: str = "animation.fcpxml"
    track: Optional[int] = None
    segment: Optional[int] = None
    template: str = "default"
    interpolate: bool = True
    interpolation_step: float = 0.25
    duration: Optional[int] = None
    fps: int = 30


def _load_config(config_path: Optional[Path]) -> Dict[str, Any]:
    """Load YAML configuration if provided"""
    if not config_path:
        return {}

    if not config_path.exists():
        raise FileNotFoundError(f"Config file not found: {config_path}")

    with open(config_path, "r") as f:
        data = yaml.safe_load(f) or {}

    return {k: v for k, v in data.items() if k in AnimationSettings.model_fields.keys()}


class SettingsFactory:
    @staticmethod
    def from_sources(
        cli_overrides: Dict[str, Any], config_path: Optional[Path]
    ) -> AnimationSettings:
        """Build settings from YAML config and CLI overrides."""
        file_config = _load_config(config_path)

        merged: Dict[str, Any] = {**file_config, **cli_overrides}

        if not merged.get("gpx_file"):
            raise ValueError("GPX file path is required (provide via CLI or config).")

        merged["gpx_file"] = Path(merged["gpx_file"])
        merged["interpolate"] = bool(merged.get("interpolate"))
        merged["interpolation_step"] = float(merged["interpolation_step"])

        return AnimationSettings(**merged)


