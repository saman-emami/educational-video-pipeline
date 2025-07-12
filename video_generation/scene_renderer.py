from __future__ import annotations

import subprocess
from pathlib import Path
from typing import Any, Dict


class SceneRenderer:
    """Render individual Manim scenes to MP4 files."""

    def __init__(self, manim_config: Dict[str, Any]) -> None:
        """
        Parameters
        ----------
        manim_config : dict
            Keys:
            - 'quality' : str  (e.g. 'low_quality', 'medium_quality', 'high_quality')
            - 'frame_rate' : int
            - 'output_dir' : str
        """
        self.quality = manim_config.get("quality", "medium_quality")
        self.frame_rate = int(manim_config.get("frame_rate", 30))
        self.output_dir = Path(manim_config.get("output_dir", "renders"))
        self.output_dir.mkdir(parents=True, exist_ok=True)

    # ------------------------------------------------------------------ #
    def render_scene(
        self,
        scene_file: Path,
        scene_name: str,
        render_settings: Dict[str, Any] | None = None,
    ) -> Path:
        """
        Compile a single Manim scene via subprocess.

        Returns
        -------
        Path
            Final MP4 file path.
        """
        render_settings = render_settings or {}
        resolution = render_settings.get("resolution", "1920x1080")
        height = resolution.split("x")[1]

        cmd = [
            "manim",
            str(scene_file),
            scene_name,
            "--fps",
            str(self.frame_rate),
            "--" + self.quality,
            "-r",
            f"{resolution}",
            "--format",
            "mp4",
            "--renderer",
            "opengl",
        ]

        subprocess.run(cmd, check=True)

        # Locate the freshly rendered video
        output_pattern = self.output_dir / f"{scene_name}.mp4"
        fallback_pattern = scene_file.parent / "media" / "videos"
        # Search inside manim's default directory if not in configured output_dir
        if not output_pattern.exists():
            mp4_files = list(fallback_pattern.rglob("*.mp4"))
            if not mp4_files:
                raise FileNotFoundError(f"No MP4 output found for scene {scene_name}.")
            output_pattern = mp4_files[-1]

        # Move to output_dir with canonical name
        final_path = self.output_dir / f"{scene_name}.mp4"
        final_path.write_bytes(output_pattern.read_bytes())

        # Cleanup large build artifacts
        for cache_dir in (scene_file.parent / "media").rglob("*"):
            if cache_dir.is_dir():
                cache_dir.unlink(missing_ok=True)

        return final_path
