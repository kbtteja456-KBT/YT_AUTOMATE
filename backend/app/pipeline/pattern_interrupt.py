"""PatternInterruptEngine ensuring high-retention visual pacing and scene switching."""

from typing import Any
from backend.app.models.style_profile import StyleProfile
from backend.app.models.video import VisualType


class PatternInterruptEngine:
    """Calculates dynamic cut points and alternates visual types for maximum viewer retention."""

    def __init__(self, style_profile: StyleProfile):
        self.profile = style_profile

    def plan_scene_rhythm(self, total_duration: float) -> list[dict[str, Any]]:
        """Compute time slots and alternating visual styles based on style profile."""
        slots: list[dict[str, Any]] = []

        # Hook scene: opening 0.0 to hook_duration_sec
        hook_end = min(self.profile.hook_duration_sec, total_duration * 0.1)
        slots.append({
            "scene_id": 1,
            "start": 0.0,
            "end": hook_end,
            "visual_type": VisualType.MOTION_GRAPHIC,
            "is_hook": True
        })

        current_time = hook_end
        scene_counter = 2

        # Split remaining duration into segments alternating between demo and screen walkthrough
        cut_interval = self.profile.cut_frequency_sec
        split_mark = total_duration * self.profile.real_footage_ratio

        while current_time < total_duration:
            next_time = min(round(current_time + cut_interval, 2), total_duration)
            if next_time - current_time < 1.0 and slots:
                # Merge tiny trailing segment into previous slot
                slots[-1]["end"] = total_duration
                break

            # Dual-segment rhythm
            if current_time < split_mark:
                v_type = VisualType.MOTION_GRAPHIC if scene_counter % 2 == 0 else VisualType.STOCK_FOOTAGE
            else:
                v_type = VisualType.SCREEN_RECORDING if scene_counter % 2 == 0 else VisualType.MOTION_GRAPHIC

            slots.append({
                "scene_id": scene_counter,
                "start": current_time,
                "end": next_time,
                "visual_type": v_type,
                "is_hook": False
            })

            current_time = next_time
            scene_counter += 1

        return slots
