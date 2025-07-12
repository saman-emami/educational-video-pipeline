from __future__ import annotations

import subprocess
from pathlib import Path
from typing import Iterable, List


class VideoComposer:
    """
    Concatenate rendered scene videos and mix corresponding audio tracks.
    """

    def __init__(self, video_config: dict | None = None) -> None:
        self.bitrate = video_config.get("bitrate", "4M") if video_config else "4M"
        self.output_dir = (
            Path(video_config.get("output_dir", "final_videos"))
            if video_config
            else Path("final_videos")
        )
        self.output_dir.mkdir(parents=True, exist_ok=True)

    # ------------------------------------------------------------------ #
    def compose_final_video(
        self,
        scene_videos: Iterable[Path],
        audio_files: Iterable[Path],
        metadata: dict,
        rendering_config: dict | None = None,
    ) -> Path:
        """
        Stitch scene videos and align audio tracks into a single MP4.

        Scene count and audio count must be equal.
        """
        scene_videos = list(scene_videos)
        audio_files = list(audio_files)

        if len(scene_videos) != len(audio_files):
            raise ValueError("Scene and audio counts differ.")

        concat_list = self._generate_concat_list(scene_videos)
        concat_file = self.output_dir / "concat.txt"
        concat_file.write_text(concat_list)

        video_no_audio = self.output_dir / "temp_no_audio.mp4"

        # 1. Concatenate videos (no audio)
        cmd_concat = [
            "ffmpeg",
            "-y",
            "-f",
            "concat",
            "-safe",
            "0",
            "-i",
            str(concat_file),
            "-c",
            "copy",
            str(video_no_audio),
        ]
        subprocess.run(cmd_concat, check=True)

        # 2. Merge audio tracks sequentially
        merged_audio = self._merge_audios(audio_files)

        # 3. Combine concatenated video with merged audio
        final_path = self.output_dir / f"{metadata['title'].replace(' ', '_')}.mp4"
        cmd_mux = [
            "ffmpeg",
            "-y",
            "-i",
            str(video_no_audio),
            "-i",
            str(merged_audio),
            "-c:v",
            "copy",
            "-c:a",
            "aac",
            "-b:a",
            "192k",
            str(final_path),
        ]
        subprocess.run(cmd_mux, check=True)

        # Cleanup temp files
        video_no_audio.unlink(missing_ok=True)
        merged_audio.unlink(missing_ok=True)
        concat_file.unlink(missing_ok=True)

        return final_path

    # ------------------------------------------------------------------ #
    @staticmethod
    def _generate_concat_list(videos: List[Path]) -> str:
        """
        Create FFmpeg concat demuxer list text.
        """
        return "\n".join(f"file '{v.resolve()}'" for v in videos)

    # ------------------------------------------------------------------ #
    def _merge_audios(self, wav_paths: List[Path]) -> Path:
        """
        Concatenate WAV audio sequentially using FFmpeg.
        """
        concat_file = self.output_dir / "audio_concat.txt"
        concat_file.write_text("\n".join(f"file '{p.resolve()}'" for p in wav_paths))
        merged_path = self.output_dir / "merged_audio.wav"

        cmd = [
            "ffmpeg",
            "-y",
            "-f",
            "concat",
            "-safe",
            "0",
            "-i",
            str(concat_file),
            "-c",
            "copy",
            str(merged_path),
        ]
        subprocess.run(cmd, check=True)
        concat_file.unlink(missing_ok=True)
        return merged_path
