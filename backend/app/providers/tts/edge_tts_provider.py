"""Microsoft Edge Neural TTS provider (100% Free, Zero-Cost, Natural Voices)."""

import os
import time
import edge_tts
from typing import Any, Optional
from pathlib import Path

from backend.app.core.logging import logger
from backend.app.core.errors import ProviderError
from backend.app.models.provider import ProviderHealth, ProviderStatus, ProviderType
from backend.app.providers.base import TTSProvider

DEFAULT_EDGE_VOICES = [
    {"voice_id": "en-US-ChristopherNeural", "gender": "Male", "locale": "en-US", "name": "Christopher (US)"},
    {"voice_id": "en-US-JennyNeural", "gender": "Female", "locale": "en-US", "name": "Jenny (US)"},
    {"voice_id": "en-US-GuyNeural", "gender": "Male", "locale": "en-US", "name": "Guy (US)"},
    {"voice_id": "en-IN-PrabhatNeural", "gender": "Male", "locale": "en-IN", "name": "Prabhat (India)"},
    {"voice_id": "en-IN-NeerjaNeural", "gender": "Female", "locale": "en-IN", "name": "Neerja (India)"},
    {"voice_id": "en-GB-RyanNeural", "gender": "Male", "locale": "en-GB", "name": "Ryan (UK)"},
]


class EdgeTTSProvider(TTSProvider):
    """Zero-cost Microsoft Edge Neural speech synthesis."""

    name = "edge_tts"
    provider_type = ProviderType.TTS
    is_zero_cost = True
    is_paid = False

    async def synthesize_speech(
        self,
        text: str,
        output_filepath: str,
        voice_id: str = "en-US-ChristopherNeural",
        rate: str = "+0%",
        pitch: str = "+0Hz",
        volume: str = "+0%"
    ) -> str:
        """Synthesize spoken narration audio file directly to disk."""
        self.verify_zero_cost_compliance()

        # Ensure parent directory exists
        out_path = Path(output_filepath).resolve()
        out_path.parent.mkdir(parents=True, exist_ok=True)

        clean_text = text.strip()
        if not clean_text:
            raise ProviderError("Cannot synthesize empty text narration.")

        try:
            communicate = edge_tts.Communicate(
                text=clean_text,
                voice=voice_id,
                rate=rate,
                pitch=pitch,
                volume=volume
            )
            await communicate.save(str(out_path))

            if not out_path.exists() or out_path.stat().st_size == 0:
                raise ProviderError(f"Edge TTS produced empty audio file at {output_filepath}")

            logger.info(f"Synthesized voice ({voice_id}) -> {out_path} ({out_path.stat().st_size} bytes)")
            return str(out_path)

        except Exception as e:
            logger.error(f"Edge TTS synthesis error: {e}")
            raise ProviderError(f"Edge TTS failed: {e}")

    async def get_available_voices(self) -> list[dict[str, Any]]:
        """List default high-quality English neural voices."""
        return DEFAULT_EDGE_VOICES

    async def check_health(self) -> ProviderHealth:
        """Verify Edge TTS library and connection."""
        start = time.time()
        try:
            # Test ping communicate with single syllable
            voices = await edge_tts.list_voices()
            latency = (time.time() - start) * 1000

            return ProviderHealth(
                provider_name=self.name,
                provider_type=self.provider_type,
                status=ProviderStatus.CONNECTED,
                is_zero_cost=True,
                is_paid=False,
                latency_ms=round(latency, 1),
                details={"voices_available": len(voices)}
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
