"""ElevenLabs Multi-Key Rotating TTS Provider with Edge-TTS Zero-Downtime Fallback.

Features:
- Rotates through a pool of ElevenLabs API keys automatically.
- Detects quota exhaustion (HTTP 401, 429, or quota_exceeded) and seamlessly switches to the next active key.
- If all ElevenLabs keys are exhausted, automatically falls back to Edge-TTS so video rendering never fails.
"""

import os
import requests
from pathlib import Path
from typing import List, Optional
from backend.app.core.logging import logger

DEFAULT_KEYS = [
    k.strip() for k in os.getenv(
        "ELEVENLABS_API_KEYS",
        ""
    ).split(";") if k.strip()
]


class ElevenLabsRotatingProvider:
    def __init__(self, api_keys: Optional[List[str]] = None):
        env_keys = os.getenv("ELEVENLABS_API_KEYS", "")
        if env_keys:
            self.keys = [k.strip() for k in env_keys.split(";") if k.strip()]
        elif api_keys:
            self.keys = api_keys
        else:
            self.keys = DEFAULT_KEYS

        self.current_idx = 0
        self.model_id = "eleven_multilingual_v2"
        self.default_voice_id = "IKne3meq5aSn9XLyUdCD"  # Charlie (or Liam: TX3LPaxmHKxFdv7VOQHJ)

    def synthesize(
        self,
        text: str,
        output_filepath: str,
        voice_id: Optional[str] = None
    ) -> bool:
        """Synthesizes speech using rotating ElevenLabs keys, with fallback to Edge-TTS."""
        v_id = voice_id or self.default_voice_id
        out_path = Path(output_filepath)
        out_path.parent.mkdir(parents=True, exist_ok=True)

        for attempt in range(len(self.keys)):
            key = self.keys[self.current_idx]
            logger.info(f"[ElevenLabs] Attempting synthesis with Key #{self.current_idx + 1}...")

            payload = {
                "text": text,
                "model_id": self.model_id,
                "voice_settings": {
                    "stability": 0.5,
                    "similarity_boost": 0.75,
                    "style": 0.0,
                    "use_speaker_boost": True
                }
            }

            try:
                r = requests.post(
                    f"https://api.elevenlabs.io/v1/text-to-speech/{v_id}",
                    headers={"xi-api-key": key, "Content-Type": "application/json"},
                    json=payload,
                    timeout=30
                )
                if r.status_code == 200:
                    with open(out_path, "wb") as f:
                        f.write(r.content)
                    logger.info(f"[ElevenLabs] Synthesis successful using Key #{self.current_idx + 1}!")
                    return True

                elif r.status_code in [401, 429] or "quota" in r.text.lower():
                    logger.warning(
                        f"[ElevenLabs] Key #{self.current_idx + 1} exhausted or unauthorized (Status {r.status_code}). Rotating to next key..."
                    )
                    self.current_idx = (self.current_idx + 1) % len(self.keys)
                else:
                    logger.warning(f"[ElevenLabs] API returned status {r.status_code}: {r.text[:120]}")
                    self.current_idx = (self.current_idx + 1) % len(self.keys)

            except Exception as e:
                logger.warning(f"[ElevenLabs] Request failed with Key #{self.current_idx + 1}: {e}")
                self.current_idx = (self.current_idx + 1) % len(self.keys)

        # Fallback to Edge-TTS if all ElevenLabs keys are exhausted
        logger.warning("[ElevenLabs] All ElevenLabs keys exhausted! Falling back to native Edge-TTS...")
        import asyncio
        import edge_tts

        async def fallback_edge():
            c = edge_tts.Communicate(text, "te-IN-MohanNeural")
            await c.save(str(out_path))

        try:
            asyncio.run(fallback_edge())
            logger.info("[ElevenLabs Fallback] Successfully synthesized with Edge-TTS!")
            return True
        except Exception as e:
            logger.error(f"[ElevenLabs Fallback] Edge-TTS fallback also failed: {e}")
            return False

