"""CaptionAgent generating ASS subtitles or functioning as a no-op for quiz card format."""

from pathlib import Path
from typing import Optional

from backend.app.agents.base import BaseAgent
from backend.app.core.logging import logger
from backend.app.models.video import CaptionSegment
from backend.app.models.style_profile import StyleProfile
from backend.app.providers.base import STTProvider, StorageProvider


class CaptionAgent(BaseAgent):
    """Generates word-synchronized, high-impact vertical Short subtitles (ASS format)."""

    name = "CaptionAgent"

    def __init__(self, stt_provider: STTProvider, storage_provider: StorageProvider):
        self.stt = stt_provider
        self.storage = storage_provider

    def _format_timestamp_ass(self, seconds: float) -> str:
        """Convert float seconds to ASS timestamp format: H:MM:SS.cc"""
        hrs = int(seconds // 3600)
        mins = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        centis = int(round((seconds - int(seconds)) * 100))
        if centis == 100:
            secs += 1
            centis = 0
        return f"{hrs}:{mins:02d}:{secs:02d}.{centis:02d}"

    def build_ass_subtitles(
        self,
        segments: list[CaptionSegment],
        output_file: str,
        style_profile: Optional[StyleProfile] = None
    ) -> str:
        """Generate ASS subtitle file with highlighted active word and safe margins."""
        profile = style_profile or StyleProfile()

        ass_header = f"""[Script Info]
Title: YouTube Shorts Synced Captions
ScriptType: v4.00+
WrapStyle: 0
ScaledBorderAndShadow: yes
YCbCr Matrix: TV.709
PlayResX: 1080
PlayResY: 1920
MarginV: 420

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Default,Impact,64,&H00FFFFFF,&H0000FFA3,&H00000000,&H80000000,-1,0,0,0,100,100,0,0,1,5,2,2,40,40,420,1
Style: Highlight,Impact,68,&H0000FFA3,&H00FFFFFF,&H00000000,&H80000000,-1,0,0,0,105,105,0,0,1,6,3,2,40,40,420,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""
        events = []
        for seg in segments:
            words = seg.words
            if not words:
                start_ts = self._format_timestamp_ass(seg.start)
                end_ts = self._format_timestamp_ass(seg.end)
                events.append(f"Dialogue: 0,{start_ts},{end_ts},Default,,0,0,0,,{seg.text.upper()}")
                continue

            chunk_size = profile.caption_words_per_segment
            for i in range(0, len(words), chunk_size):
                chunk = words[i:i + chunk_size]
                chunk_start = chunk[0].start
                chunk_end = chunk[-1].end

                start_ts = self._format_timestamp_ass(chunk_start)
                end_ts = self._format_timestamp_ass(chunk_end)
                chunk_text = " ".join(w.word.upper() for w in chunk)
                events.append(f"Dialogue: 0,{start_ts},{end_ts},Highlight,,0,0,0,,{chunk_text}")

        full_content = ass_header + "\n".join(events) + "\n"
        out_path = Path(output_file).resolve()
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(full_content, encoding="utf-8")
        self.log(f"Generated ASS subtitle file: {out_path} ({len(events)} dialog lines)")
        return str(out_path)

    async def generate_captions(
        self,
        audio_filepath: str,
        job_id: str,
        style_profile: Optional[StyleProfile] = None
    ) -> tuple[str, list[CaptionSegment]]:
        """Transcribe audio with Whisper or mark complete as a no-op for quiz_card format."""
        # Detect if this audio is background music for quiz card format
        is_quiz = "bg_music" in Path(audio_filepath).name.lower()
        if not is_quiz:
            try:
                from backend.app.core.db import SyncMongoDB
                db = SyncMongoDB.get_db()
                doc = db.publishing_jobs.find_one({"_id": job_id})
                if doc and doc.get("content_format") == "quiz_card":
                    is_quiz = True
            except Exception:
                pass

        if is_quiz:
            self.log("[CaptionAgent] content_format == 'quiz_card': Quiz card PNGs contain all on-screen code, options, and explanation. Marking stage complete immediately with no caption overlay (no-op).")
            return ("", [])

        # Standard Speech-to-Text Transcription for general format
        self.log(f"Transcribing narration for captions (job {job_id})...")
        segments = await self.stt.transcribe_audio(audio_filepath)
        output_file = self.storage.get_path("captions", f"captions_{job_id}.ass")
        ass_path = self.build_ass_subtitles(segments, output_file, style_profile)
        return (ass_path, segments)
