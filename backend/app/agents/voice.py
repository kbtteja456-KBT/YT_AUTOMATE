"""VoiceAgent synthesizing spoken narration or selecting normalized background music for quiz format."""

import os
import subprocess
from pathlib import Path
from typing import Any, Optional

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

    async def _select_and_normalize_bg_music(self, duration_sec: float, output_file: str, job_id: str) -> str:
        """Select, loop/trim, and normalize an upbeat trivia background music track to -14 LUFS."""
        ffmpeg_bin = get_ffmpeg_binary()
        pool_dir = Path(self.storage.get_path("audio", "music_pool"))
        pool_dir.mkdir(parents=True, exist_ok=True)

        # Existing candidate tracks
        existing_bg = Path(self.storage.get_path("audio", "bg_music.mp3"))
        candidate_tracks = []
        if existing_bg.exists():
            candidate_tracks.append(str(existing_bg))

        # Check pool_dir for any other .mp3 files
        for f in pool_dir.glob("*.mp3"):
            if str(f) not in candidate_tracks:
                candidate_tracks.append(str(f))

        # Rotate track index to prevent consecutive repetition
        VoiceAgent._last_music_index = (VoiceAgent._last_music_index + 1)
        selected_track = candidate_tracks[VoiceAgent._last_music_index % len(candidate_tracks)] if candidate_tracks else None

        Path(output_file).parent.mkdir(parents=True, exist_ok=True)

        if selected_track and Path(selected_track).exists():
            self.log(f"Selected royalty-free music track: {selected_track} (rotating pool index {VoiceAgent._last_music_index})")
            # Loop/trim and normalize to -14 LUFS
            cmd = [
                ffmpeg_bin, "-y",
                "-stream_loop", "-1",
                "-i", selected_track,
                "-t", str(duration_sec),
                "-af", "loudnorm=I=-14:LRA=11:TP=-1.5",
                "-c:a", "libmp3lame",
                "-b:a", "192k",
                output_file
            ]
        else:
            self.log("Synthesizing procedural rhythmic thinking groove (zero-cost royalty-free) normalized to -14 LUFS...")
            cmd = [
                ffmpeg_bin, "-y",
                "-f", "lavfi",
                "-i", "aevalsrc=sin(440*2*PI*t)*exp(-3*mod(t\\,0.5)) + 0.5*sin(880*2*PI*t)*exp(-6*mod(t\\,0.25)):s=44100",
                "-t", str(duration_sec),
                "-af", "loudnorm=I=-14:LRA=11:TP=-1.5",
                "-c:a", "libmp3lame",
                "-b:a", "192k",
                output_file
            ]

        subprocess.run(cmd, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        self.log(f"Background music track prepared at {output_file} ({duration_sec:.1f}s, normalized to -14 LUFS).")
        return output_file

    async def generate_voiceover(
        self,
        script: Script,
        job_id: str,
        voice_config: Optional[VoiceConfig] = None
    ) -> str:
        """Synthesize script full_narration, or select background music if format is quiz_card."""
        is_quiz = (getattr(script, "content_format", "general") == "quiz_card")

        if is_quiz:
            self.log(f"[VoiceAgent] content_format == 'quiz_card': Skipping TTS narration. Selecting background music...")
            output_file = self.storage.get_path("audio", f"bg_music_{job_id}.mp3")
            target_dur = getattr(script, "target_duration_sec", 24.0)
            return await self._select_and_normalize_bg_music(duration_sec=target_dur, output_file=output_file, job_id=job_id)

        # Standard TTS Synthesis
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
