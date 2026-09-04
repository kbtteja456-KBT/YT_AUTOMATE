"""ThumbnailAgent orchestrating custom high-CTR thumbnail creation per video."""

from typing import Optional
from backend.app.agents.base import BaseAgent
from backend.app.models.video import Script
from backend.app.models.thumbnail import ThumbnailCard, ThumbnailSpec
from backend.app.providers.base import ThumbnailProvider, StorageProvider, AIProvider


class ThumbnailAgent(BaseAgent):
    """Generates custom text-overlay cards for YouTube Shorts shelf CTR."""

    name = "ThumbnailAgent"

    def __init__(
        self,
        ai_provider: AIProvider,
        thumbnail_provider: ThumbnailProvider,
        storage_provider: StorageProvider
    ):
        super().__init__(ai_provider=ai_provider)
        self.thumbnail_engine = thumbnail_provider
        self.storage = storage_provider

    async def generate_custom_thumbnail(
        self,
        video_filepath: str,
        script: Script,
        job_id: str
    ) -> ThumbnailCard:
        """Create custom 1080x1920 thumbnail card with bold hook words."""
        self.log(f"Generating custom thumbnail card for job {job_id}...")

        # Generate 3-4 punchy high-contrast words for overlay
        prompt = (
            f"Topic: '{script.topic}'.\n"
            f"Hook: '{script.hook}'.\n\n"
            f"Create a 3 to 4 word bold phrase for a YouTube Shorts thumbnail card.\n"
            f"Examples: 'NEVER USE THIS', '5 SECRET TOOLS', 'DO THIS INSTEAD', 'GAME CHANGER'.\n"
            f"Must be under 4 words, high curiosity, maximum contrast."
        )

        schema = {
            "type": "object",
            "properties": {
                "overlay_text": {"type": "string"}
            },
            "required": ["overlay_text"]
        }

        try:
            resp = await self.ai.generate_structured(prompt=prompt, response_schema=schema)
            overlay_words = resp.get("overlay_text", "DON'T MISS THIS").strip()
        except Exception:
            overlay_words = "SECRET AI TOOL"

        spec = ThumbnailSpec(
            source_frame_timestamp=2.0,
            overlay_text=overlay_words,
            font_size=78,
            text_color="#FFFF00",
            output_width=1080,
            output_height=1920
        )

        output_file = self.storage.get_path("thumbnails", f"thumb_{job_id}.jpg")

        card = await self.thumbnail_engine.generate_thumbnail(
            video_filepath=video_filepath,
            spec=spec,
            output_filepath=output_file
        )

        self.log(f"Thumbnail card generated: {card.file_path} ('{overlay_words}')")
        return card
