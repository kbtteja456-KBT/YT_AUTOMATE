"""StyleAnalyzerAgent extracting pacing, dual-segment split, and cut frequency from reference video."""

import json
import cv2
from pathlib import Path
from typing import Any, Optional

from backend.app.agents.base import BaseAgent
from backend.app.core.logging import logger
from backend.app.core.ffmpeg_utils import probe_video_metadata
from backend.app.models.style_profile import StyleProfile


class StyleAnalyzerAgent(BaseAgent):
    """Analyzes reference vertical Short to extract dual-segment editing rhythm."""

    name = "StyleAnalyzerAgent"

    def analyze_video_structure(self, video_path: str) -> StyleProfile:
        """Analyze shot cuts and pacing from reference video without saving any copyrighted media."""
        self.log(f"Analyzing reference video structure from {video_path}...")

        meta = probe_video_metadata(video_path)
        total_duration = meta["duration"] if meta["duration"] > 0 else 44.0

        # Run scene change detection using OpenCV frame difference analysis
        cap = cv2.VideoCapture(video_path)
        fps = cap.get(cv2.CAP_PROP_FPS) or 30.0
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))

        cut_timestamps: list[float] = [0.0]
        prev_gray = None
        frame_idx = 0

        # Sample every 5 frames for fast, accurate shot boundary detection
        sample_step = 5
        threshold = 32.0  # Mean pixel difference threshold indicating a cut

        while cap.isOpened() and frame_idx < total_frames:
            ret, frame = cap.read()
            if not ret:
                break

            if frame_idx % sample_step == 0:
                gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                # Resize for lightning-fast comparison
                small_gray = cv2.resize(gray, (160, 280))

                if prev_gray is not None:
                    diff = cv2.absdiff(small_gray, prev_gray)
                    mean_diff = float(diff.mean())
                    if mean_diff > threshold:
                        timestamp = round(frame_idx / fps, 2)
                        # Avoid micro-cuts less than 0.8s
                        if timestamp - cut_timestamps[-1] >= 0.8:
                            cut_timestamps.append(timestamp)

                prev_gray = small_gray

            frame_idx += 1

        cap.release()

        segment_count = max(len(cut_timestamps), 8)
        cut_freq = round(total_duration / segment_count, 2)

        # Detect the transition point between demo footage and screen walkthrough
        # Typically around 25-30% mark of the runtime
        expected_split_time = total_duration * 0.28
        # Find nearest cut point to the 28% mark
        nearest_cut = min(cut_timestamps, key=lambda t: abs(t - expected_split_time)) if cut_timestamps else expected_split_time
        real_footage_ratio = round(nearest_cut / total_duration, 2)
        if real_footage_ratio < 0.15 or real_footage_ratio > 0.45:
            real_footage_ratio = 0.28
        screen_record_ratio = round(1.0 - real_footage_ratio, 2)

        hook_dur = round(cut_timestamps[1], 2) if len(cut_timestamps) > 1 and cut_timestamps[1] < 4.0 else 2.8

        profile = StyleProfile(
            name="extracted_reference_pacing",
            reference_video_path=str(Path(video_path).resolve()),
            total_duration_sec=total_duration,
            segment_count=segment_count,
            real_footage_ratio=real_footage_ratio,
            screen_recording_ratio=screen_record_ratio,
            cut_frequency_sec=cut_freq,
            hook_duration_sec=hook_dur,
            caption_words_per_segment=3,
            caption_highlight_color="#00FFA3",
            is_active=True
        )

        # Save result to style_profile.json as baseline editing blueprint
        out_json = Path("style_profile.json").resolve()
        out_json.write_text(profile.model_dump_json(indent=2), encoding="utf-8")

        self.log(
            f"Style analysis complete: Duration={total_duration}s, Cuts={segment_count}, "
            f"Split={int(real_footage_ratio*100)}% Real / {int(screen_record_ratio*100)}% Screen, "
            f"Cut every {cut_freq}s. Saved to style_profile.json."
        )

        return profile
