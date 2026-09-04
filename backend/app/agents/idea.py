"""IdeaAgent generating candidate concepts and enforcing duplicate prevention."""

from typing import Any, Optional
from backend.app.agents.base import BaseAgent
from backend.app.providers.base import AIProvider, SearchProvider
from backend.app.core.security import compute_content_hash


class IdeaAgent(BaseAgent):
    """Generates viral, high-retention video ideas tailored to channel niche and history."""

    name = "IdeaAgent"

    def _calculate_similarity(self, text_a: str, text_b: str) -> float:
        """Calculate token-based Jaccard similarity between two topic titles."""
        set_a = set(text_a.lower().split())
        set_b = set(text_b.lower().split())
        if not set_a or not set_b:
            return 0.0
        intersection = len(set_a.intersection(set_b))
        union = len(set_a.union(set_b))
        return intersection / union

    async def generate_daily_topic(
        self,
        niche: str,
        target_audience: str,
        past_topics: list[str],
        slot_index: int = 1
    ) -> dict[str, Any]:
        """Generate multiple candidate ideas, run similarity checks, and pick winner."""
        self.log(f"Generating ideas for slot {slot_index} in niche '{niche}'...")

        slot_theme = "cutting-edge tool, fast hack, or breaking workflow" if slot_index == 1 else "in-depth breakdown, counter-intuitive insight, or secret technique"

        prompt = (
            f"Generate 3 distinct, high-CTR YouTube Shorts ideas for niche: '{niche}'.\n"
            f"Target audience: '{target_audience}'.\n"
            f"Slot theme: {slot_theme}.\n"
            f"Recently covered topics to AVOID repeating: {past_topics[-10:] if past_topics else 'None'}.\n"
            f"Every idea must be highly specific, practical, and factual."
        )

        schema = {
            "type": "object",
            "properties": {
                "candidates": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "topic": {"type": "string"},
                            "angle": {"type": "string"},
                            "why_viral": {"type": "string"},
                            "estimated_interest_score": {"type": "number"}
                        },
                        "required": ["topic", "angle", "why_viral", "estimated_interest_score"]
                    }
                }
            },
            "required": ["candidates"]
        }

        response = await self.ai.generate_structured(
            prompt=prompt,
            response_schema=schema,
            system_prompt="You are an expert YouTube Shorts content strategist focused on retention and originality."
        )

        candidates = response.get("candidates", [])
        if not candidates:
            # Fallback robust topic if LLM returned empty list
            fallback_topic = f"5 Breakthrough {niche} Tools You Never Knew Existed"
            return {
                "topic": fallback_topic,
                "angle": "Comprehensive utility review",
                "similarity_score": 0.0,
                "hash": compute_content_hash(fallback_topic)
            }

        # Filter against past topics for duplicate prevention
        best_candidate = None
        lowest_similarity = 1.0

        for cand in candidates:
            topic_str = cand.get("topic", "")
            max_sim = 0.0
            for past in past_topics:
                sim = self._calculate_similarity(topic_str, past)
                if sim > max_sim:
                    max_sim = sim

            if max_sim < 0.60:
                best_candidate = cand
                lowest_similarity = max_sim
                break
            elif max_sim < lowest_similarity:
                lowest_similarity = max_sim
                best_candidate = cand

        chosen = best_candidate or candidates[0]
        chosen_topic = chosen.get("topic", "")
        self.log(f"Selected Topic: '{chosen_topic}' (max similarity to history: {lowest_similarity:.2f})")

        return {
            "topic": chosen_topic,
            "angle": chosen.get("angle", ""),
            "why_viral": chosen.get("why_viral", ""),
            "similarity_score": round(lowest_similarity, 3),
            "hash": compute_content_hash(chosen_topic)
        }
