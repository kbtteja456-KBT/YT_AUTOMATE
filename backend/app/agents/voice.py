"""VoiceAgent synthesizing spoken narration using local/free neural TTS."""

import os
from pathlib import Path
from typing import Any, Optional

from backend.app.agents.base import BaseAgent
from backend.app.core.logging import logger
from backend.app.core.errors import ProviderError
from backend.app.models.video import Script
from backend.app.models.settings import VoiceConfig
from backend.app.providers.base import TTSProvider, StorageProvider


class VoiceAgent(BaseAgent):
    """Synthesizes high-fidelity narration audio using zero-cost neural TTS."""

    name = "VoiceAgent"

    def __init__(self, tts_provider: TTSProvider, storage_provider: StorageProvider):
        self.tts = tts_provider
        self.storage = storage_provider

    async def generate_voiceover(
        self,
        script: Script,
        job_id: str,
        voice_config: Optional[VoiceConfig] = None
    ) -> str:
        """Synthesize script full_narration into an audio track on disk."""
        v_cfg = voice_config or VoiceConfig()
        self.log(f"Synthesizing voiceover for job {job_id} using voice '{v_cfg.voice_id}'...")

        output_file = self.storage.get_path("audio", f"voice_{job_id}.mp3")

        audio_path = await self.tts.synthesize_speech(
            text=script.full_narration,
            output_filepath=output_file,
            voice_id=v_cfg.voice_id,
            rate=v_cfg.rate,
            pitch=v_cfg.pitch,
            volume=v_cfg.volume
        )

        file_size = Path(audio_path).stat().st_size
        self.log(f"Voiceover generated successfully at {audio_path} ({file_size} bytes).")
        return audio_path
