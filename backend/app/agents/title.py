"""TitleAgent and DescriptionAgent generating high-CTR metadata."""

from typing import Any
from backend.app.agents.base import BaseAgent
from backend.app.models.video import Script


class TitleAgent(BaseAgent):
    """Generates punchy, high-CTR titles and relevant viral hashtags."""

    name = "TitleAgent"

    async def generate_title_and_tags(self, script: Script) -> dict[str, Any]:
        """Generate optimized title (<60 characters) and tags."""
        self.log(f"Generating title and hashtags for '{script.topic}'...")

        prompt = (
            f"Topic: '{script.topic}'.\n"
            f"Narration Script:\n'{script.full_narration}'\n\n"
            f"Generate:\n"
            f"1. 'title': High-CTR YouTube Short title under 60 characters. Must be urgent, curiosity-inducing, and truthful.\n"
            f"2. 'hashtags': 3 to 5 trending tags (e.g. #Shorts, #AI, #Tech).\n"
            f"3. 'tags': 5 to 8 search keyword tags."
        )

        schema = {
            "type": "object",
            "properties": {
                "title": {"type": "string"},
                "hashtags": {"type": "array", "items": {"type": "string"}},
                "tags": {"type": "array", "items": {"type": "string"}}
            },
            "required": ["title", "hashtags", "tags"]
        }

        response = await self.ai.generate_structured(
            prompt=prompt,
            response_schema=schema,
            system_prompt="You are a YouTube SEO and algorithm optimization expert."
        )

        title = response.get("title", f"{script.topic} in 60 Seconds").strip()
        hashtags = response.get("hashtags", ["#Shorts", "#AI", "#Productivity"])
        tags = response.get("tags", [script.topic, "AI", "Tech Tools", "Productivity"])

        self.log(f"Title generated: '{title}' ({len(title)} chars)")
        return {
            "title": title,
            "hashtags": hashtags,
            "tags": tags
        }


class DescriptionAgent(BaseAgent):
    """Generates clean YouTube description with timestamps and links."""

    name = "DescriptionAgent"

    async def generate_description(self, script: Script, title: str, hashtags: list[str]) -> str:
        """Construct full YouTube Shorts description."""
        self.log(f"Generating description for '{title}'...")

        tag_str = " ".join(hashtags) if hashtags else "#Shorts #Tech #AI"

        description = (
            f"{title}\n\n"
            f"{script.value}\n\n"
            f"🔔 Follow for daily autonomous tech and AI discoveries.\n\n"
            f"{tag_str}"
        )
        return description
