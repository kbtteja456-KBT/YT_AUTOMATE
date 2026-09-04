"""Offline TTS provider using pyttsx3 (Windows SAPI5 / Linux eSpeak)."""

import os
import time
import pyttsx3
from typing import Any, Optional
from pathlib import Path

from backend.app.core.logging import logger
from backend.app.core.errors import ProviderError
from backend.app.models.provider import ProviderHealth, ProviderStatus, ProviderType
from backend.app.providers.base import TTSProvider


class PyTTSx3Provider(TTSProvider):
    """100% offline local TTS engine."""

    name = "pyttsx3"
    provider_type = ProviderType.TTS
    is_zero_cost = True
    is_paid = False

    async def synthesize_speech(
        self,
        text: str,
        output_filepath: str,
        voice_id: str = "default",
        rate: str = "+0%",
        pitch: str = "+0Hz",
        volume: str = "+0%"
    ) -> str:
        """Synthesize speech using local system voices."""
        self.verify_zero_cost_compliance()

        out_path = Path(output_filepath).resolve()
        out_path.parent.mkdir(parents=True, exist_ok=True)

        try:
            engine = pyttsx3.init()
            # Set speech rate
            engine.setProperty("rate", 185)  # Natural Shorts pacing
            engine.save_to_file(text, str(out_path))
            engine.runAndWait()

            if not out_path.exists() or out_path.stat().st_size == 0:
                raise ProviderError(f"pyttsx3 produced empty audio file at {output_filepath}")

            return str(out_path)
        except Exception as e:
            logger.error(f"pyttsx3 synthesis error: {e}")
            raise ProviderError(f"pyttsx3 failed: {e}")

    async def get_available_voices(self) -> list[dict[str, Any]]:
        """Retrieve local system voices."""
        try:
            engine = pyttsx3.init()
            voices = engine.getProperty("voices")
            return [{"voice_id": v.id, "name": v.name, "gender": getattr(v, "gender", "unknown")} for v in voices]
        except Exception:
            return [{"voice_id": "default", "name": "System Default Voice"}]

    async def check_health(self) -> ProviderHealth:
        """Verify pyttsx3 engine initialization."""
        try:
            engine = pyttsx3.init()
            return ProviderHealth(
                provider_name=self.name,
                provider_type=self.provider_type,
                status=ProviderStatus.CONNECTED,
                is_zero_cost=True,
                is_paid=False,
                details={"engine": "Local SAPI5 / eSpeak"}
            )
        except Exception as e:
            return ProviderHealth(
                provider_name=self.name,
                provider_type=self.provider_type,
                status=ProviderStatus.OFFLINE,
                is_zero_cost=True,
                is_paid=False,
                error_message=str(e)
            )
