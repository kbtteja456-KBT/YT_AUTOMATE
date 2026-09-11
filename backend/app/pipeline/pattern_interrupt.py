"""PatternInterruptEngine ensuring high-retention visual pacing and scene switching."""

from typing import Any
from backend.app.models.style_profile import StyleProfile
from backend.app.models.video import VisualType


class PatternInterruptEngine:
    """Calculates dynamic cut points and alternates visual types for maximum viewer retention."""

    def __init__(self, style_profile: StyleProfile):
        self.profile = style_profile

    def plan_scene_rhythm(self, total_duration: float) -> list[dict[str, Any]]:
        """Compute time slots and alternating visual styles (photos + videos) for maximum viewer retention."""
        slots: list[dict[str, Any]] = []

        # Hook scene: opening 0.0 to ~4.5s with dynamic video clip
        hook_end = min(max(self.profile.hook_duration_sec, 4.0), 5.5)
        slots.append({
            "scene_id": 1,
            "start": 0.0,
            "end": hook_end,
            "visual_type": VisualType.STOCK_FOOTAGE,
            "is_hook": True
        })

        current_time = hook_end
        scene_counter = 2

        # Pacing: 5.0 to 6.5 seconds per scene (ideal for narrative Shorts)
        cut_interval = max(self.profile.cut_frequency_sec, 5.2)

        while current_time < total_duration:
            next_time = min(round(current_time + cut_interval, 2), total_duration)
            if next_time - current_time < 2.0 and slots:
                # Merge tiny trailing segment into previous slot
                slots[-1]["end"] = total_duration
                break

            # Alternating hybrid rhythm: Video -> Photo (Ken Burns) -> Video -> Photo (Ken Burns)...
            # Even scene_counter -> STOCK_PHOTO, Odd scene_counter -> STOCK_FOOTAGE
            v_type = VisualType.STOCK_PHOTO if scene_counter % 2 == 0 else VisualType.STOCK_FOOTAGE

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
