"""LearningAgent extracting channel retention patterns to guide future ideation."""

from typing import Any
from backend.app.agents.base import BaseAgent
from backend.app.providers.base import AIProvider


class LearningAgent(BaseAgent):
    """Evaluates video retention patterns to refine future topic and hook generation."""

    name = "LearningAgent"

    async def extract_retention_insights(
        self,
        historical_videos: list[dict[str, Any]],
        channel_niche: str
    ) -> dict[str, Any]:
        """Synthesize channel-specific patterns from performance history."""
        self.log(f"Extracting learning patterns from {len(historical_videos)} past videos...")

        if not historical_videos:
            return {
                "high_retention_topics": [channel_niche],
                "recommended_hook_style": "High curiosity + fast pacing",
                "recommended_duration_sec": 44.0,
                "notes": "Insufficient historical data. Operating on baseline style profile."
            }

        prompt = (
            f"Channel Niche: '{channel_niche}'.\n"
            f"Performance History of Published Shorts:\n"
            f"{historical_videos}\n\n"
            f"Analyze which topics, hook styles, and video durations generated the highest watch retention.\n"
            f"Rules:\n"
            f"- Never promise virality.\n"
            f"- Report only channel-specific observed patterns.\n"
            f"- Provide actionable guidance for the next video's IdeaAgent."
        )

        schema = {
            "type": "object",
            "properties": {
                "high_retention_topics": {"type": "array", "items": {"type": "string"}},
                "recommended_hook_style": {"type": "string"},
                "recommended_duration_sec": {"type": "number"},
                "notes": {"type": "string"}
            },
            "required": ["high_retention_topics", "recommended_hook_style", "recommended_duration_sec", "notes"]
        }

        try:
            insights = await self.ai.generate_structured(prompt=prompt, response_schema=schema)
            self.log(f"Learning insights updated: Best topics: {insights.get('high_retention_topics')}")
            return insights
        except Exception as e:
            self.log(f"Learning extraction fallback: {e}", "WARNING")
            return {
                "high_retention_topics": [channel_niche],
                "recommended_hook_style": "High curiosity",
                "recommended_duration_sec": 44.0,
                "notes": "Operating on default template."
            }
