"""Kenpath Labs Svara TTS Provider for Multilingual & Indic Speech Synthesis.

Features:
- Connects directly to Kenpath Labs Svara TTS Turbo API (https://api.kenpathlabs.com/v1).
- Supports hyper-natural Indian regional voices (Telugu, Hindi, Tamil, Kannada, Bengali, etc.).
- Default Telugu voice: Vamsi (`sv_2fqanvcj`) - calm, polished teacher/sir delivery.
- Alternate Telugu voices: Charan (`sv_pqkyc6r7`), Teja (`sv_wh3km6ce`), Aarav (`sv_r22w7pwe`).
"""

import os
import requests
from pathlib import Path
from typing import Optional
from backend.app.core.logging import logger

DEFAULT_SVARA_KEY = os.getenv("SVARA_API_KEY", "sk_live_FKo9_jVoQ092GXUol_yg7PFxsuxSpnMSh7ynnm5aW5o")
DEFAULT_TELUGU_VOICE = "sv_2fqanvcj"  # Vamsi


class SvaraTTSProvider:
    """Production provider for Kenpath Labs Svara TTS API."""

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv("SVARA_API_KEY") or DEFAULT_SVARA_KEY
        self.base_url = "https://api.kenpathlabs.com/v1"
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

    def synthesize(
        self,
        text: str,
        output_filepath: str,
        voice_id: str = DEFAULT_TELUGU_VOICE,
        language: str = "te"
    ) -> bool:
        """Synthesizes text into high-quality speech and writes MP3 file."""
        out_path = Path(output_filepath)
        out_path.parent.mkdir(parents=True, exist_ok=True)

        payload = {
            "model": "svara-tts-turbo",
            "input": text,
            "voice": voice_id,
            "lang": language,
            "response_format": "mp3"
        }

        try:
            logger.info(f"[SvaraTTS] Synthesizing speech with voice '{voice_id}' (lang='{language}')...")
            resp = requests.post(
                f"{self.base_url}/audio/speech",
                headers=self.headers,
                json=payload,
                timeout=30
            )
            if resp.status_code == 200:
                with open(out_path, "wb") as f:
                    f.write(resp.content)
                logger.info(f"[SvaraTTS] Successfully generated audio at {out_path} ({len(resp.content)} bytes)")
                return True
            else:
                logger.error(f"[SvaraTTS] Synthesis failed: {resp.status_code} - {resp.text}")
                return False
        except Exception as e:
            logger.error(f"[SvaraTTS] Exception during synthesis: {e}")
            return False

