"""HookAgent generating and scoring high-retention opening hooks."""

from typing import Any
from backend.app.agents.base import BaseAgent
from backend.app.models.video import Hook


class HookAgent(BaseAgent):
    """Generates >= 5 hook variations and scores them for viral retention."""

    name = "HookAgent"

    async def generate_and_score_hooks(self, topic: str, key_takeaway: str) -> list[Hook]:
        """Generate at least 5 hooks, evaluate their retention potential, and select the top hook."""
        self.log(f"Generating and scoring hook candidates for topic: '{topic}'...")

        prompt = (
            f"Topic: '{topic}'.\n"
            f"Core takeaway: '{key_takeaway}'.\n\n"
            f"Generate 5 distinct hook sentences designed for the critical 0 to 3 second window of YouTube Shorts.\n"
            f"Rules:\n"
            f"1. No filler words ('Hey guys', 'Did you know', 'Check this out').\n"
            f"2. Under 15 words spoken fast.\n"
            f"3. Score each hook from 1.0 to 10.0 across 6 metrics:\n"
            f"   - curiosity\n"
            f"   - clarity\n"
            f"   - specificity\n"
            f"   - emotional_impact\n"
            f"   - retention_potential\n"
            f"   - speed"
        )

        schema = {
            "type": "object",
            "properties": {
                "hooks": {
                    "type": "array",
                    "minItems": 5,
                    "items": {
                        "type": "object",
                        "properties": {
                            "text": {"type": "string"},
                            "curiosity": {"type": "number"},
                            "clarity": {"type": "number"},
                            "specificity": {"type": "number"},
                            "emotional_impact": {"type": "number"},
                            "retention_potential": {"type": "number"},
                            "speed": {"type": "number"}
                        },
                        "required": [
                            "text", "curiosity", "clarity",
                            "specificity", "emotional_impact",
                            "retention_potential", "speed"
                        ]
                    }
                }
            },
            "required": ["hooks"]
        }

        response = await self.ai.generate_structured(
            prompt=prompt,
            response_schema=schema,
            system_prompt="You are a YouTube Shorts hook specialist obsessed with the first 3 seconds retention."
        )

        hook_objs: list[Hook] = []
        raw_hooks = response.get("hooks", [])

        # Default fallback hooks if LLM returned fewer than 5
        if len(raw_hooks) < 5:
            raw_hooks = [
                {"text": f"Stop using ChatGPT until you see this {topic} breakthrough.", "curiosity": 9.2, "clarity": 9.0, "specificity": 8.5, "emotional_impact": 8.0, "retention_potential": 9.1, "speed": 9.4},
                {"text": f"This free tool replaces 4 hours of work in 30 seconds.", "curiosity": 9.0, "clarity": 9.2, "specificity": 8.8, "emotional_impact": 8.5, "retention_potential": 9.0, "speed": 9.2},
                {"text": f"90% of students have no idea this feature exists.", "curiosity": 8.8, "clarity": 9.1, "specificity": 8.0, "emotional_impact": 8.2, "retention_potential": 8.9, "speed": 9.0},
                {"text": f"If you use this tool wrong, you're wasting hours.", "curiosity": 8.5, "clarity": 8.9, "specificity": 8.2, "emotional_impact": 8.0, "retention_potential": 8.6, "speed": 9.1},
                {"text": f"Here's the exact workflow professionals use in 2026.", "curiosity": 8.6, "clarity": 9.3, "specificity": 8.7, "emotional_impact": 8.1, "retention_potential": 8.8, "speed": 8.9},
            ]

        for h in raw_hooks:
            curiosity = float(h.get("curiosity", 8.0))
            clarity = float(h.get("clarity", 8.0))
            specificity = float(h.get("specificity", 8.0))
            emotional = float(h.get("emotional_impact", 8.0))
            retention = float(h.get("retention_potential", 8.0))
            speed = float(h.get("speed", 8.0))

            # Weighted composite score
            total = (
                curiosity * 0.25 +
                retention * 0.25 +
                speed * 0.15 +
                specificity * 0.15 +
                clarity * 0.10 +
                emotional * 0.10
            )

            hook_objs.append(Hook(
                text=h.get("text", "").strip(),
                curiosity_score=curiosity,
                clarity_score=clarity,
                specificity_score=specificity,
                emotional_impact_score=emotional,
                retention_score=retention,
                speed_score=speed,
                total_score=round(total, 2)
            ))

        # Select highest scoring hook
        hook_objs.sort(key=lambda x: x.total_score, reverse=True)
        hook_objs[0].selected = True

        self.log(f"Selected Winning Hook ({hook_objs[0].total_score:.2f}/10): '{hook_objs[0].text}'")
        return hook_objs
