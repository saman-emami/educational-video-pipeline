# models/tts_handler.py
import torch
import torchaudio
from TTS.api import TTS
from pathlib import Path
from typing import Dict, Optional


class TTSHandler:
    """Handle TTS generation with XTTS-v2"""

    def __init__(self, config: Dict):
        self.config = config
        self.device = "cuda" if torch.cuda.is_available() else "cpu"

        # Initialize XTTS model
        self.tts = TTS(
            model_name="tts_models/multilingual/multi-dataset/xtts_v2",
            progress_bar=False,
        ).to(self.device)

    def generate_speech(
        self, text: str, output_path: str, speaker_wav: Optional[str] = None
    ) -> Path:
        """Generate speech from text"""
        output_path = Path(output_path)

        # Generate audio
        if speaker_wav:
            # Voice cloning mode
            self.tts.tts_to_file(
                text=text,
                file_path=str(output_path),
                speaker_wav=speaker_wav,
                language="en",
            )
        else:
            # Default voice
            self.tts.tts_to_file(text=text, file_path=str(output_path), language="en")

        return output_path
