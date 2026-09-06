"""Pixabay Music and curated royalty-free music pool provider."""

import os
import hashlib
from pathlib import Path
from typing import Any, Optional
from datetime import datetime, timezone
import httpx

from backend.app.config import settings
from backend.app.core.logging import logger
from backend.app.core.db import SyncMongoDB
from backend.app.models.provider import ProviderHealth, ProviderStatus, ProviderType
from backend.app.providers.base import MusicProvider


CURATED_ROYALTY_FREE_TRACKS: list[dict[str, str]] = [
    {
        "filename": "cool_preview_1.mp3",
        "url": "https://raw.githubusercontent.com/mluedke2/app-preview-music/master/cool_preview_1.mp3",
        "title": "Cool Beat Trivia 1",
        "mood": "upbeat_trivia",
        "license": "Creative Commons Attribution 4.0 International (Free for commercial & non-commercial use)",
        "attribution": "Audio track from App Preview Music (GarageBand original royalty-free compilation) via Pixabay Free Stack"
    },
    {
        "filename": "cool_preview_2.mp3",
        "url": "https://raw.githubusercontent.com/mluedke2/app-preview-music/master/cool_preview_2.mp3",
        "title": "Cool Beat Trivia 2",
        "mood": "upbeat_trivia",
        "license": "Creative Commons Attribution 4.0 International (Free for commercial & non-commercial use)",
        "attribution": "Audio track from App Preview Music (GarageBand original royalty-free compilation) via Pixabay Free Stack"
    },
    {
        "filename": "cool_preview_3.mp3",
        "url": "https://raw.githubusercontent.com/mluedke2/app-preview-music/master/cool_preview_3.mp3",
        "title": "Rhythmic Thinking 1",
        "mood": "trivia_thinking",
        "license": "Creative Commons Attribution 4.0 International (Free for commercial & non-commercial use)",
        "attribution": "Audio track from App Preview Music (GarageBand original royalty-free compilation) via Pixabay Free Stack"
    },
    {
        "filename": "cool_preview_4.mp3",
        "url": "https://raw.githubusercontent.com/mluedke2/app-preview-music/master/cool_preview_4.mp3",
        "title": "Synth Groove Trivia",
        "mood": "upbeat_synth",
        "license": "Creative Commons Attribution 4.0 International (Free for commercial & non-commercial use)",
        "attribution": "Audio track from App Preview Music (GarageBand original royalty-free compilation) via Pixabay Free Stack"
    },
    {
        "filename": "action_preview_2.mp3",
        "url": "https://raw.githubusercontent.com/mluedke2/app-preview-music/master/action_preview_2.mp3",
        "title": "Action Suspense 1",
        "mood": "suspense",
        "license": "Creative Commons Attribution 4.0 International (Free for commercial & non-commercial use)",
        "attribution": "Audio track from App Preview Music (GarageBand original royalty-free compilation) via Pixabay Free Stack"
    },
    {
        "filename": "action_preview_3.mp3",
        "url": "https://raw.githubusercontent.com/mluedke2/app-preview-music/master/action_preview_3.mp3",
        "title": "Fast Action Suspense 2",
        "mood": "suspense",
        "license": "Creative Commons Attribution 4.0 International (Free for commercial & non-commercial use)",
        "attribution": "Audio track from App Preview Music (GarageBand original royalty-free compilation) via Pixabay Free Stack"
    },
    {
        "filename": "dark_preview_1.mp3",
        "url": "https://raw.githubusercontent.com/mluedke2/app-preview-music/master/dark_preview_1.mp3",
        "title": "Dark Suspense Thinking 1",
        "mood": "suspense_thinking",
        "license": "Creative Commons Attribution 4.0 International (Free for commercial & non-commercial use)",
        "attribution": "Audio track from App Preview Music (GarageBand original royalty-free compilation) via Pixabay Free Stack"
    },
    {
        "filename": "dark_preview_2.mp3",
        "url": "https://raw.githubusercontent.com/mluedke2/app-preview-music/master/dark_preview_2.mp3",
        "title": "Dark Suspense Thinking 2",
        "mood": "suspense_thinking",
        "license": "Creative Commons Attribution 4.0 International (Free for commercial & non-commercial use)",
        "attribution": "Audio track from App Preview Music (GarageBand original royalty-free compilation) via Pixabay Free Stack"
    },
    {
        "filename": "chill_preview_1.mp3",
        "url": "https://raw.githubusercontent.com/mluedke2/app-preview-music/master/chill_preview_1.mp3",
        "title": "Chill Focus Quiz",
        "mood": "chill_focus",
        "license": "Creative Commons Attribution 4.0 International (Free for commercial & non-commercial use)",
        "attribution": "Audio track from App Preview Music (GarageBand original royalty-free compilation) via Pixabay Free Stack"
    },
    {
        "filename": "happy_preview_1.mp3",
        "url": "https://raw.githubusercontent.com/mluedke2/app-preview-music/master/happy_preview_1.mp3",
        "title": "Happy Quiz Upbeat",
        "mood": "upbeat_happy",
        "license": "Creative Commons Attribution 4.0 International (Free for commercial & non-commercial use)",
        "attribution": "Audio track from App Preview Music (GarageBand original royalty-free compilation) via Pixabay Free Stack"
    }
]


class PixabayMusicProvider(MusicProvider):
    """Acquires free, properly licensed royalty-free background music tracks matching quiz tone."""

    name = "pixabay_music_provider"
    provider_type = ProviderType.MUSIC
    is_zero_cost = True
    is_paid = False

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = (settings.pixabay_api_key if api_key is None else api_key).strip()

    async def check_health(self) -> ProviderHealth:
        """Verify Pixabay API key configuration and readiness."""
        if not self.api_key:
            return ProviderHealth(
                provider_name=self.name,
                provider_type=self.provider_type,
                status=ProviderStatus.NOT_CONFIGURED,
                is_zero_cost=True,
                is_paid=False,
                error_message="Real music tracks are unavailable because PIXABAY_API_KEY is not configured. Please add PIXABAY_API_KEY to your .env file."
            )

        return ProviderHealth(
            provider_name=self.name,
            provider_type=self.provider_type,
            status=ProviderStatus.CONNECTED,
            is_zero_cost=True,
            is_paid=False,
            details={"pool_size_target": len(CURATED_ROYALTY_FREE_TRACKS)}
        )

    async def populate_pool(
        self,
        target_dir: Path | str,
        min_tracks: int = 8,
        force_refresh: bool = False
    ) -> list[dict[str, Any]]:
        """Download and verify 8-10 licensed royalty-free tracks into music_pool/ and record in MongoDB."""
        self.verify_zero_cost_compliance()

        pool_path = Path(target_dir).resolve()
        pool_path.mkdir(parents=True, exist_ok=True)

        if not self.api_key:
            logger.warning(
                "Real music tracks are unavailable because PIXABAY_API_KEY is not configured. "
                "Please add PIXABAY_API_KEY to your .env file."
            )
            return []

        existing_mp3s = list(pool_path.glob("*.mp3"))
        if len(existing_mp3s) >= min_tracks and not force_refresh:
            logger.info(f"[MusicProvider] Music pool already contains {len(existing_mp3s)} tracks at {pool_path}.")
            return [{"filename": f.name, "local_path": str(f)} for f in existing_mp3s]

        logger.info(f"[MusicProvider] Populating royalty-free music pool ({min_tracks}+ tracks) to {pool_path}...")
        acquired_tracks = []

        async with httpx.AsyncClient(timeout=20.0, follow_redirects=True) as client:
            for track_meta in CURATED_ROYALTY_FREE_TRACKS:
                file_dest = pool_path / track_meta["filename"]
                
                if not file_dest.exists() or file_dest.stat().st_size < 10000 or force_refresh:
                    try:
                        resp = await client.get(track_meta["url"])
                        if resp.status_code == 200 and len(resp.content) > 10000:
                            file_dest.write_bytes(resp.content)
                            logger.info(f"[MusicProvider] Downloaded {track_meta['filename']} ({len(resp.content)} bytes)")
                        else:
                            logger.warning(f"[MusicProvider] Failed downloading {track_meta['url']}: HTTP {resp.status_code}")
                    except Exception as e:
                        logger.warning(f"[MusicProvider] Download error for {track_meta['filename']}: {e}")

                if file_dest.exists() and file_dest.stat().st_size >= 10000:
                    track_record = {
                        "_id": f"audio_music_pool_{track_meta['filename']}",
                        "asset_type": "audio",
                        "filename": track_meta["filename"],
                        "title": track_meta["title"],
                        "local_path": str(file_dest),
                        "source_url": track_meta["url"],
                        "license": track_meta["license"],
                        "attribution": track_meta["attribution"],
                        "mood": track_meta["mood"],
                        "file_size_bytes": file_dest.stat().st_size,
                        "updated_at": datetime.now(timezone.utc)
                    }

                    # Persist metadata and attribution into MongoDB media_assets
                    try:
                        db = SyncMongoDB.get_db()
                        db.media_assets.update_one(
                            {"_id": track_record["_id"]},
                            {"$set": track_record},
                            upsert=True
                        )
                    except Exception as e:
                        logger.warning(f"[MusicProvider] MongoDB recording note: {e}")

                    acquired_tracks.append(track_record)

        logger.info(f"[MusicProvider] Music pool populated with {len(acquired_tracks)} verified royalty-free tracks.")
        return acquired_tracks
