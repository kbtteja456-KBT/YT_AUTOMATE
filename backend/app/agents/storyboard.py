"""StoryboardAgent breaking narration into multi-scene storyboard with pacing templates."""

from typing import Any, Optional
from backend.app.agents.base import BaseAgent
from backend.app.models.video import Script, Storyboard, Scene, VisualType
from backend.app.models.style_profile import StyleProfile
from backend.app.pipeline.pattern_interrupt import PatternInterruptEngine


class StoryboardAgent(BaseAgent):
    """Orchestrates scene breakdown, visual descriptions, and cut intervals."""

    name = "StoryboardAgent"

    async def create_storyboard(
        self,
        script: Script,
        style_profile: Optional[StyleProfile] = None,
        total_duration: float = 45.0
    ) -> Storyboard:
        """Break narration script into scenes aligned with style pacing blueprint."""
        profile = style_profile or StyleProfile()
        self.log(f"Creating storyboard for '{script.topic}' using style '{profile.name}'...")

        engine = PatternInterruptEngine(profile)
        rhythm_slots = engine.plan_scene_rhythm(total_duration)

        prompt = (
            f"Topic: '{script.topic}'.\n"
            f"Full Script Narration:\n'{script.full_narration}'\n\n"
            f"Break this narration into {len(rhythm_slots)} sequential scenes matching these timing slots:\n"
            f"{[(s['scene_id'], s['start'], s['end']) for s in rhythm_slots]}\n\n"
            f"For each scene, provide:\n"
            f"- 'scene_id': integer matching slot\n"
            f"- 'narration': the spoken sentences for this segment\n"
            f"- 'visual_type': one of ['motion_graphic', 'screen_recording', 'stock_footage', 'generated_image']\n"
            f"- 'visual_prompt': detailed description of the on-screen visual\n"
            f"- 'caption': short punchy on-screen caption (max 4-5 words)\n"
            f"- 'transition': 'cut', 'fade', or 'zoom'"
        )

        schema = {
            "type": "object",
            "properties": {
                "scenes": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "scene_id": {"type": "integer"},
                            "narration": {"type": "string"},
                            "visual_type": {"type": "string"},
                            "visual_prompt": {"type": "string"},
                            "caption": {"type": "string"},
                            "transition": {"type": "string"}
                        },
                        "required": ["scene_id", "narration", "visual_prompt", "caption"]
                    }
                }
            },
            "required": ["scenes"]
        }

        response = await self.ai.generate_structured(
            prompt=prompt,
            response_schema=schema,
            system_prompt="You are a professional video editor and storyboard director for YouTube Shorts."
        )

        raw_scenes = response.get("scenes", [])
        scenes: list[Scene] = []

        for slot in rhythm_slots:
            sid = slot["scene_id"]
            matched_raw = next((r for r in raw_scenes if r.get("scene_id") == sid), None)
            if matched_raw:
                v_prompt = matched_raw.get("visual_prompt", f"Dynamic visual for scene {sid}")
                v_type_str = matched_raw.get("visual_type", slot["visual_type"].value)
                caption_text = matched_raw.get("caption", "")
                narration_sub = matched_raw.get("narration", "")
                trans = matched_raw.get("transition", "cut")
            else:
                v_prompt = f"High energy graphics showing {script.topic} scene {sid}"
                v_type_str = slot["visual_type"].value
                caption_text = f"Tool #{sid}" if sid > 1 else script.hook[:20]
                narration_sub = ""
                trans = "cut"

            try:
                v_type = VisualType(v_type_str)
            except ValueError:
                v_type = VisualType.MOTION_GRAPHIC

            scenes.append(Scene(
                scene_id=sid,
                start=slot["start"],
                end=slot["end"],
                narration=narration_sub,
                visual_type=v_type,
                visual_prompt=v_prompt,
                caption=caption_text,
                transition=trans
            ))

        storyboard = Storyboard(
            scenes=scenes,
            total_duration=total_duration,
            real_footage_ratio=profile.real_footage_ratio,
            screen_record_ratio=profile.screen_recording_ratio,
            cut_frequency=profile.cut_frequency_sec
        )

        self.log(f"Storyboard finalized with {len(scenes)} scenes over {total_duration}s.")
        return storyboard
