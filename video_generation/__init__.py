"""
Initialization for the video_generation package.
Exposes high-level classes used by the pipeline.
"""

from .scene_renderer import SceneRenderer
from .audio_processor import AudioProcessor
from .video_composer import VideoComposer

__all__: list[str] = [
    "SceneRenderer",
    "AudioProcessor",
    "VideoComposer",
]
