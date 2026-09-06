"""VoiceAgent synthesizing spoken narration or selecting normalized background music for quiz format."""

import os
import subprocess
from pathlib import Path
from typing import Any, Optional

from backend.app.config import settings
from backend.app.agents.base import BaseAgent
from backend.app.core.logging import logger
from backend.app.core.ffmpeg_utils import get_ffmpeg_binary
from backend.app.models.video import Script
from backend.app.models.settings import VoiceConfig
from backend.app.providers.base import TTSProvider, StorageProvider


class VoiceAgent(BaseAgent):
    """Synthesizes high-fidelity narration audio, or selects and normalizes trivia music for quiz format."""

    name = "VoiceAgent"
    _last_music_index: int = -1

    def __init__(self, tts_provider: TTSProvider, storage_provider: StorageProvider):
        self.tts = tts_provider
        self.storage = storage_provider
        # Set by _select_and_normalize_bg_music() after each selection.
        # The orchestrator reads this to pass the attribution credit line to DescriptionAgent.
        # None = CC0 / no attribution required; str = full CC BY credit line to append.
        self.last_music_attribution: Optional[str] = None
        self.last_music_record: Optional[dict] = None

    async def _select_and_normalize_bg_music(
        self, duration_sec: float, output_file: str, job_id: str
    ) -> str:
        """Select, loop/trim, and normalize an upbeat trivia background music track to -14 LUFS.

        After selection, sets self.last_music_attribution to the CC BY credit line
        (or None for CC0/public-domain tracks). The caller (orchestrator) must pass this
        to DescriptionAgent so it appears in the real YouTube description.
        """
        ffmpeg_bin = get_ffmpeg_binary()
        pool_dir = Path(self.storage.get_path("audio", "music_pool"))
        pool_dir.mkdir(parents=True, exist_ok=True)

        # Lazy-populate the pool using the real FreeMusicArchiveProvider
        pool_mp3s = list(pool_dir.glob("*.mp3"))
        if len(pool_mp3s) < 5:
            try:
                from backend.app.providers.music.pixabay_music import FreeMusicArchiveProvider
                from backend.app.config import settings as cfg
                # FMA API key (optional — falls back to Incompetech automatically)
                fma_key = getattr(cfg, "fma_api_key", "").strip() if hasattr(cfg, "fma_api_key") else ""
                provider = FreeMusicArchiveProvider(fma_api_key=fma_key)
                await provider.populate_pool(pool_dir, min_tracks=5)
                pool_mp3s = list(pool_dir.glob("*.mp3"))
            except Exception as e:
                self.log(f"Music pool population note: {e}", "WARNING")

        candidate_tracks = [str(f) for f in sorted(pool_dir.glob("*.mp3"))]
        if not candidate_tracks:
            # Absolute fallback: single legacy bg_music.mp3 if it exists
            existing_bg = Path(self.storage.get_path("audio", "bg_music.mp3"))
            if existing_bg.exists():
                candidate_tracks.append(str(existing_bg))

        # Rotate track index to prevent consecutive repetition across jobs
        VoiceAgent._last_music_index = VoiceAgent._last_music_index + 1
        selected_track = (
            candidate_tracks[VoiceAgent._last_music_index % len(candidate_tracks)]
            if candidate_tracks
            else None
        )

        # Look up the attribution record for the selected track
        self.last_music_attribution = None
        self.last_music_record = None
        if selected_track:
            selected_filename = Path(selected_track).name
            try:
                from backend.app.core.db import SyncMongoDB
                from backend.app.providers.music.pixabay_music import build_attribution_credit
                db = SyncMongoDB.get_db()
                record = db.media_assets.find_one({"filename": selected_filename})
                if record:
                    self.last_music_record = dict(record)
                    if record.get("requires_attribution") == "true":
                        self.last_music_attribution = build_attribution_credit(record)
                        self.log(
                            f"Selected CC BY track '{record.get('title')}' — "
                            f"attribution credit will be appended to YouTube description."
                        )
                    else:
                        self.log(
                            f"Selected CC0 track '{record.get('title')}' — "
                            f"no attribution required."
                        )
                else:
                    # Track not in DB: treat as UNVERIFIED — still play it, flag it
                    self.log(
                        f"Track '{selected_filename}' has no DB record. "
                        f"Treating as UNVERIFIED_LICENSE — attribution appended as safety measure.",
                        "WARNING",
                    )
                    # Conservative: assume attribution required for unverified files
                    self.last_music_attribution = (
                        f"Background music: '{selected_filename}' — "
                        f"license UNVERIFIED. Please replace with a verified CC0 track."
                    )
            except Exception as e:
                self.log(f"Attribution lookup note: {e}", "WARNING")

        Path(output_file).parent.mkdir(parents=True, exist_ok=True)

        if selected_track and Path(selected_track).exists():
            self.log(
                f"Selected music track: {Path(selected_track).name} "
                f"(pool index {VoiceAgent._last_music_index})"
            )
            cmd = [
                ffmpeg_bin, "-y",
                "-stream_loop", "-1",
                "-i", selected_track,
                "-t", str(duration_sec),
                "-af", "loudnorm=I=-14:LRA=11:TP=-1.5",
                "-c:a", "libmp3lame",
                "-b:a", "192k",
                output_file,
            ]
        else:
            self.log(
                "No licensed music track available — "
                "using procedural rhythmic tone (zero-cost, no license risk)."
            )
            # CC0 by construction — synthesized by FFmpeg, no third-party content
            self.last_music_attribution = None
            cmd = [
                ffmpeg_bin, "-y",
                "-f", "lavfi",
                "-i", "aevalsrc=sin(440*2*PI*t)*exp(-3*mod(t\\,0.5)) + 0.5*sin(880*2*PI*t)*exp(-6*mod(t\\,0.25)):s=44100",
                "-t", str(duration_sec),
                "-af", "loudnorm=I=-14:LRA=11:TP=-1.5",
                "-c:a", "libmp3lame",
                "-b:a", "192k",
                output_file,
            ]

        subprocess.run(cmd, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        self.log(
            f"Background music prepared at {output_file} "
            f"({duration_sec:.1f}s, normalized to -14 LUFS)."
        )
        return output_file

    async def generate_voiceover(
        self,
        script: Script,
        job_id: str,
        voice_config: Optional[VoiceConfig] = None,
    ) -> str:
        """Synthesize script full_narration, or select background music if format is quiz_card.

        After this call, self.last_music_attribution holds the CC BY credit line to append
        to the YouTube description (None if track is CC0 or TTS narration was used).
        """
        is_quiz = getattr(script, "content_format", "general") == "quiz_card"

        if is_quiz:
            self.log(
                "[VoiceAgent] content_format == 'quiz_card': "
                "Skipping TTS narration. Selecting licensed background music..."
            )
            output_file = self.storage.get_path("audio", f"bg_music_{job_id}.mp3")
            target_dur = getattr(script, "target_duration_sec", 24.0)
            return await self._select_and_normalize_bg_music(
                duration_sec=target_dur, output_file=output_file, job_id=job_id
            )

        # Standard TTS synthesis — no music attribution needed
        self.last_music_attribution = None
        self.last_music_record = None
        v_cfg = voice_config or VoiceConfig()
        self.log(f"Synthesizing voiceover for job {job_id} using voice '{v_cfg.voice_id}'...")
        output_file = self.storage.get_path("audio", f"voice_{job_id}.mp3")

        audio_path = await self.tts.synthesize_speech(
            text=script.full_narration,
            output_filepath=output_file,
            voice_id=v_cfg.voice_id,
            rate=v_cfg.rate,
            pitch=v_cfg.pitch,
            volume=v_cfg.volume,
        )

        file_size = Path(audio_path).stat().st_size
        self.log(f"Voiceover generated successfully at {audio_path} ({file_size} bytes).")
        return audio_path
