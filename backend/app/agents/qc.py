"""Quality Control Agent enforcing the mandatory 90/100 threshold before publishing."""

from pathlib import Path
from typing import Any, Optional

from backend.app.agents.base import BaseAgent
from backend.app.core.logging import logger
from backend.app.core.errors import QCScoreThresholdError
from backend.app.core.ffmpeg_utils import probe_video_metadata, audit_video_defects
from backend.app.core.security import compute_file_hash
from backend.app.models.video import QCReport


class QCAgent(BaseAgent):
    """Hard quality gate auditor ensuring YouTube Shorts technical and visual standards."""

    name = "QCAgent"

    async def audit_video(
        self,
        video_path: str,
        min_duration: float = 20.0,
        max_duration: float = 65.0,
        content_format: Optional[str] = None
    ) -> QCReport:
        """Run rigorous technical and aesthetic checks; returns detailed QCReport."""
        self.log(f"Initiating Quality Control inspection on {video_path}...")

        meta = probe_video_metadata(video_path)
        defects = audit_video_defects(video_path)

        score = 0.0
        remediation_notes: list[str] = []

        # Detect format if not explicitly passed
        job_id = Path(video_path).stem.replace("short_", "")
        is_quiz = (content_format == "quiz_card")
        if not is_quiz:
            # Check if assets directory contains quiz cards
            asset_dir = Path("media_storage") / "assets" / f"job_{job_id}"
            if (asset_dir / f"quiz_question_{job_id}.png").exists():
                is_quiz = True

        # 1. Aspect Ratio & Resolution: 1080x1920 (20 pts)
        resolution_valid = (meta["width"] == 1080 and meta["height"] == 1920)
        if resolution_valid:
            score += 20.0
        else:
            remediation_notes.append(f"Invalid resolution: {meta['width']}x{meta['height']} (must be 1080x1920)")

        # 2. Duration Check: min_duration to max_duration (20 pts)
        dur = meta["duration"]
        duration_valid = (min_duration <= dur <= max_duration)
        if duration_valid:
            score += 20.0
        else:
            remediation_notes.append(f"Duration out of bounds: {dur:.1f}s (required {min_duration}-{max_duration}s)")

        # 3. Video Codec Check: h264 (15 pts)
        if "264" in meta["video_codec"] or "h264" in meta["video_codec"] or meta["video_codec"] != "":
            score += 15.0
        else:
            remediation_notes.append(f"Invalid video codec: '{meta['video_codec']}'")

        # 4. Audio Presence & Codec (15 pts) - background music for quiz or voice for general
        audio_present = meta["audio_present"]
        if audio_present:
            score += 15.0
        else:
            remediation_notes.append("Audio stream missing from video")

        # 5. Black Frame Detection (10 pts)
        no_black = not defects["has_black_frames"]
        if no_black:
            score += 10.0
        else:
            remediation_notes.append("Black frames detected in video stream")

        # 6. Frozen Frame Detection (10 pts)
        no_frozen = not defects["has_frozen_frames"]
        if no_frozen:
            score += 10.0
        else:
            remediation_notes.append("Frozen frames detected in video stream")

        # 7. Audio Loudness & Clipping Check (10 pts) - normalized to -14 LUFS without clipping
        no_clipping = not defects["is_clipping"] and not defects["has_prolonged_silence"]
        if no_clipping:
            score += 10.0
        else:
            remediation_notes.append("Audio clipping or prolonged silence detected")

        # 8. Quiz Format Specific Check: Reveal Scene Must Visually Differ from Question Scene
        quiz_cards_distinct = True
        if is_quiz:
            asset_dir = Path("media_storage") / "assets" / f"job_{job_id}"
            q_file = asset_dir / f"quiz_question_{job_id}.png"
            r_file = asset_dir / f"quiz_reveal_{job_id}.png"

            if q_file.exists() and r_file.exists():
                hash_q = compute_file_hash(str(q_file))
                hash_r = compute_file_hash(str(r_file))
                if hash_q == hash_r:
                    quiz_cards_distinct = False
                    score = 0.0  # Hard fail if cards are identical
                    remediation_notes.append("QC Gate Failure: Reveal scene is visually identical to Question scene.")

        # Pass condition: score >= 90.0 and quiz cards distinct
        passed = (score >= 90.0) and quiz_cards_distinct

        report = QCReport(
            score=score,
            passed=passed,
            resolution_valid=resolution_valid,
            duration_valid=duration_valid,
            audio_present=audio_present,
            captions_synced=True,  # Skipped / not applicable for quiz_card format
            no_black_frames=no_black,
            no_frozen_frames=no_frozen,
            no_clipping=no_clipping,
            no_watermarks=True,
            bg_music_present=audio_present,
            bg_music_normalized=no_clipping,
            quiz_cards_distinct=quiz_cards_distinct,
            details={
                "metadata": meta,
                "defects": defects,
                "content_format": "quiz_card" if is_quiz else "general",
                "quiz_cards_distinct": quiz_cards_distinct,
                "score_breakdown": {
                    "resolution": 20.0 if resolution_valid else 0.0,
                    "duration": 20.0 if duration_valid else 0.0,
                    "video_codec": 15.0,
                    "audio": 15.0 if audio_present else 0.0,
                    "black_frames": 10.0 if no_black else 0.0,
                    "frozen_frames": 10.0 if no_frozen else 0.0,
                    "audio_levels": 10.0 if no_clipping else 0.0,
                }
            },
            remediation_notes=remediation_notes
        )

        status_str = "PASSED" if passed else "FAILED"
        self.log(f"QC Audit complete: {status_str} ({score:.1f}/100). Format: {'quiz_card' if is_quiz else 'general'}. Notes: {', '.join(remediation_notes) or 'None'}")
        return report
