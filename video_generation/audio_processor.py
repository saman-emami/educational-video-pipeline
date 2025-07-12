from __future__ import annotations

import math
import subprocess
from pathlib import Path
from typing import Optional


class AudioProcessor:
    """
    Adjust TTS audio to match target scene duration using FFmpeg filters.
    """

    def __init__(self, audio_config: dict | None = None) -> None:
        self.sample_rate = audio_config.get("sample_rate") if audio_config else 48_000
        self.channels = audio_config.get("channels", 2) if audio_config else 2

    # ------------------------------------------------------------------ #
    def process_audio(
        self,
        wav_path: Path,
        target_duration: float,
        pitch_shift: Optional[float] = None,
    ) -> Path:
        """
        Time-stretch (and optionally pitch-shift) a WAV file to exact duration.

        Returns
        -------
        Path
            Path to processed WAV saved alongside original.
        """
        processed_path = wav_path.with_stem(wav_path.stem + "_proc")

        # FFmpeg atempo supports 0.5–2.0; chain filters for large factors.
        current_duration = self._probe_duration(wav_path)
        speed_factor = current_duration / target_duration
        filters: list[str] = []

        # Chain atempo filters to approximate desired speed.
        factors = self._split_speed_factor(speed_factor)
        filters.extend([f"atempo={f:.3f}" for f in factors])

        if pitch_shift:
            # Example pitch shift filter using rubberband (if compiled).
            filters.append(f"rubberband=pitch={pitch_shift}")

        filter_str = ",".join(filters)

        cmd = [
            "ffmpeg",
            "-y",
            "-i",
            str(wav_path),
            "-vn",
            "-ac",
            str(self.channels),
            "-ar",
            str(self.sample_rate),
            "-af",
            filter_str,
            str(processed_path),
        ]
        subprocess.run(cmd, capture_output=True, check=True)
        return processed_path

    # ------------------------------------------------------------------ #
    @staticmethod
    def _split_speed_factor(speed: float) -> list[float]:
        """
        Split an arbitrary speed factor into 0.5–2.0 chunks acceptable by atempo.
        """
        factors: list[float] = []
        remaining = speed
        while remaining < 0.5 or remaining > 2.0:
            segment = 2.0 if remaining > 2.0 else 0.5
            factors.append(segment)
            remaining /= segment
        factors.append(remaining)
        return factors

    # ------------------------------------------------------------------ #
    @staticmethod
    def _probe_duration(audio_path: Path) -> float:
        """
        Retrieve duration of audio file in seconds via ffprobe.
        """
        cmd = [
            "ffprobe",
            "-v",
            "error",
            "-show_entries",
            "format=duration",
            "-of",
            "default=noprint_wrappers=1:nokey=1",
            str(audio_path),
        ]
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        return float(result.stdout.strip())
