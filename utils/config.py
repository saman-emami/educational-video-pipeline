from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict

import yaml


@dataclass(slots=True)
class Config:
    """Root configuration object loaded from YAML."""

    llm_config: Dict[str, Any]
    tts_config: Dict[str, Any]
    manim_config: Dict[str, Any]
    audio_config: Dict[str, Any]
    video_config: Dict[str, Any]

    # ------------------------------------------------------------------ #
    @classmethod
    def from_file(cls, path: str | Path) -> "Config":
        path = Path(path)
        if not path.exists():
            raise FileNotFoundError(f"Config file not found: {path}")

        with path.open("r", encoding="utf-8") as fh:
            raw = yaml.safe_load(fh)

        required_sections = [
            "llm_config",
            "tts_config",
            "manim_config",
            "audio_config",
            "video_config",
        ]
        for section in required_sections:
            if section not in raw:
                raise KeyError(f"Missing section '{section}' in config.")

        return cls(**{k: raw[k] for k in required_sections})
