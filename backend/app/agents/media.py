"""MediaAgent acquiring or procedurally generating 1080x1920 scene assets."""

from pathlib import Path
from typing import Any
from backend.app.agents.base import BaseAgent
from backend.app.models.video import Storyboard, Scene
from backend.app.providers.base import StockMediaProvider, StorageProvider


class MediaAgent(BaseAgent):
    """Acquires licensed stock assets or procedural graphics for every storyboard scene."""

    name = "MediaAgent"

    def __init__(self, stock_provider: StockMediaProvider, storage_provider: StorageProvider):
        self.stock = stock_provider
        self.storage = storage_provider

    async def collect_scene_assets(self, storyboard: Storyboard, job_id: str) -> Storyboard:
        """Process each scene in storyboard, acquiring 1080x1920 assets with license tracking."""
        self.log(f"Collecting visual assets for {len(storyboard.scenes)} scenes (job: {job_id})...")

        target_dir = self.storage.get_path("assets", f"job_{job_id}")
        Path(target_dir).mkdir(parents=True, exist_ok=True)

        updated_scenes: list[Scene] = []

        for scene in storyboard.scenes:
            duration = scene.end - scene.start
            acquired_scene = await self.stock.search_and_acquire(
                query=scene.visual_prompt,
                duration_sec=duration,
                target_dir=target_dir,
                visual_type=scene.visual_type.value
            )

            # Preserve storyboard timing and narration while attaching acquired asset path
            scene.asset_local_path = acquired_scene.asset_local_path
            scene.license_info = acquired_scene.license_info
            scene.attribution = acquired_scene.attribution
            updated_scenes.append(scene)

        storyboard.scenes = updated_scenes
        self.log(f"All {len(storyboard.scenes)} scene assets acquired successfully.")
        return storyboard
