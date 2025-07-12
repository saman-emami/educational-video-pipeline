# main.py
import json
import logging
from typing import Dict, List, Optional
from dataclasses import dataclass
from pathlib import Path

from models.llm_handler import LLMHandler
from models.tts_handler import TTSHandler
from video_generation.scene_renderer import SceneRenderer
from video_generation.audio_processor import AudioProcessor
from video_generation.video_composer import VideoComposer
from utils.config import Config
from utils.progress_tracker import ProgressTracker


@dataclass
class VideoRequest:
    """Video generation request parameters"""

    concept: str
    video_format: str  # 'short', 'medium', 'long'
    audience_level: str = "general"
    llm_params: Optional[Dict] = None
    tts_params: Optional[Dict] = None


class EducationalVideoPipeline:
    """Main pipeline orchestrator for educational video generation"""

    def __init__(self, config: Config):
        self.config = config
        self.llm_handler = LLMHandler(config.llm_config)
        self.tts_handler = TTSHandler(config.tts_config)
        self.scene_renderer = SceneRenderer(config.manim_config)
        self.audio_processor = AudioProcessor(config.audio_config)
        self.video_composer = VideoComposer(config.video_config)
        self.progress_tracker = ProgressTracker()

        # Setup logging
        logging.basicConfig(
            level=logging.INFO,
            format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        )
        self.logger = logging.getLogger(__name__)

    def generate_video(self, request: VideoRequest) -> Path:
        """
        Generate educational video from concept description

        Args:
            request: Video generation parameters

        Returns:
            Path to generated video file
        """
        self.progress_tracker.start(f"Generating video: {request.concept}")

        try:
            # Step 1: Generate content structure
            self.logger.info("Generating video structure and content...")
            video_structure = self._generate_video_structure(request)
            self.progress_tracker.update(20, "Content structure generated")

            # Step 2: Render individual scenes
            self.logger.info("Rendering Manim scenes...")
            scene_videos = self._render_scenes(video_structure)
            self.progress_tracker.update(50, "Scenes rendered")

            # Step 3: Generate and process audio
            self.logger.info("Generating voice-over audio...")
            audio_files = self._generate_audio(video_structure)
            self.progress_tracker.update(70, "Audio generated")

            # Step 4: Compose final video
            self.logger.info("Composing final video...")
            final_video = self._compose_video(
                scene_videos, audio_files, video_structure
            )
            self.progress_tracker.update(100, "Video generation complete")

            return final_video

        except Exception as e:
            self.logger.error(f"Video generation failed: {str(e)}")
            raise

    def _generate_video_structure(self, request: VideoRequest) -> Dict:
        """Generate video structure using LLM"""
        prompt = self._build_master_prompt(request)
        response = self.llm_handler.generate(prompt, request.llm_params)

        # Parse and validate response
        try:
            structure = json.loads(response)
            self._validate_structure(structure)
            return structure
        except json.JSONDecodeError:
            raise ValueError("Invalid JSON response from LLM")

    def _render_scenes(self, structure: Dict) -> List[Path]:
        """Render individual Manim scenes"""
        scene_videos = []

        for scene in structure["scenes"]:
            self.logger.info(f"Rendering scene: {scene['scene_name']}")

            # Create temporary scene file
            scene_file = self._create_scene_file(scene)

            # Render with Manim
            video_path = self.scene_renderer.render_scene(
                scene_file, scene["scene_name"], structure["rendering_instructions"]
            )

            scene_videos.append(video_path)

            # Cleanup temporary file
            scene_file.unlink()

        return scene_videos

    def _generate_audio(self, structure: Dict) -> List[Path]:
        """Generate TTS audio for each scene"""
        audio_files = []

        for scene in structure["scenes"]:
            self.logger.info(f"Generating audio for: {scene['scene_name']}")

            audio_path = self.tts_handler.generate_speech(
                text=scene["voice_over"],
                output_path=f"audio_{scene['scene_number']}.wav",
            )

            # Process audio for timing
            processed_audio = self.audio_processor.process_audio(
                audio_path, target_duration=scene["duration_seconds"]
            )

            audio_files.append(processed_audio)

        return audio_files

    def _compose_video(
        self, scene_videos: List[Path], audio_files: List[Path], structure: Dict
    ) -> Path:
        """Compose final video with audio sync"""
        return self.video_composer.compose_final_video(
            scene_videos=scene_videos,
            audio_files=audio_files,
            metadata=structure["video_metadata"],
            rendering_config=structure["rendering_instructions"],
        )

    def _build_master_prompt(self, request: VideoRequest) -> str:
        """Build the master prompt from template"""
        from templates.prompts import (
            EDUCATIONAL_VIDEO_MASTER_PROMPT,
            FORMAT_INSTRUCTIONS,
        )

        format_specs = self._get_format_specs(request.video_format)

        return EDUCATIONAL_VIDEO_MASTER_PROMPT.format(
            concept=request.concept,
            video_format=request.video_format,
            duration=format_specs["duration"],
            duration_specs=format_specs["duration_specs"],
            aspect_ratio=format_specs["aspect_ratio"],
            audience_level=request.audience_level,
            format_instructions=FORMAT_INSTRUCTIONS[request.video_format],
        )

    def _get_format_specs(self, video_format: str) -> Dict:
        """Get format specifications"""
        specs = {
            "short": {
                "duration": "30-60 seconds",
                "duration_specs": "Quick concept introduction",
                "aspect_ratio": "9:16 (Portrait)",
            },
            "medium": {
                "duration": "10-15 minutes",
                "duration_specs": "Comprehensive explanation",
                "aspect_ratio": "16:9 (Landscape)",
            },
            "long": {
                "duration": "30-40 minutes",
                "duration_specs": "Deep dive exploration",
                "aspect_ratio": "16:9 (Landscape)",
            },
        }
        return specs[video_format]

    def _validate_structure(self, structure: Dict) -> None:
        """Validate generated video structure"""
        required_keys = ["video_metadata", "scenes", "rendering_instructions"]

        for key in required_keys:
            if key not in structure:
                raise ValueError(f"Missing required key: {key}")

        # Validate each scene
        for scene in structure["scenes"]:
            scene_keys = ["scene_number", "scene_name", "voice_over", "manim_code"]
            for key in scene_keys:
                if key not in scene:
                    raise ValueError(f"Missing scene key: {key}")

    def _create_scene_file(self, scene: Dict) -> Path:
        """Create temporary Python file for scene"""
        scene_code = f"""
from manim import *

class {scene['scene_name']}(Scene):
    def construct(self):
{scene['manim_code']}
"""

        file_path = Path(f"temp_{scene['scene_name']}.py")
        file_path.write_text(scene_code)
        return file_path


# Usage example
if __name__ == "__main__":
    config = Config.from_file("config.yaml")
    pipeline = EducationalVideoPipeline(config)

    request = VideoRequest(
        concept="Generate a video explaining the backpropagation algorithm",
        video_format="medium",
        audience_level="undergraduate",
        llm_params={"temperature": 0.7, "max_tokens": 4000},
        tts_params={"voice": "default", "speed": 1.0},
    )

    video_path = pipeline.generate_video(request)
    print(f"Video generated: {video_path}")
