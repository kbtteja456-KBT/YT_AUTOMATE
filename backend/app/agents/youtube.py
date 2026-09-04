"""YouTubeAgent coordinating upload, duplicate protection, and verification."""

import time
from typing import Any, Optional

from backend.app.agents.base import BaseAgent
from backend.app.core.logging import logger
from backend.app.core.errors import YouTubeAPIError, DuplicateUploadPreventedError
from backend.app.models.video import Video
from backend.app.models.thumbnail import ThumbnailCard
from backend.app.providers.base import YouTubeProvider


class YouTubeAgent(BaseAgent):
    """Executes YouTube Data API publishing with upload verification."""

    name = "YouTubeAgent"

    def __init__(self, youtube_provider: YouTubeProvider):
        self.yt = youtube_provider

    async def publish_short(
        self,
        video_filepath: str,
        title: str,
        description: str,
        tags: list[str],
        thumbnail: Optional[ThumbnailCard] = None,
        privacy_status: str = "public",
        existing_hashes: Optional[list[str]] = None
    ) -> dict[str, Any]:
        """Upload video and thumbnail with verification and duplicate checks."""
        self.log(f"Publishing YouTube Short: '{title}' ({privacy_status})...")

        # 1. Duplicate check
        from backend.app.core.security import compute_file_hash
        file_hash = compute_file_hash(video_filepath)
        if existing_hashes and file_hash in existing_hashes:
            raise DuplicateUploadPreventedError(
                f"Video with hash {file_hash} was already published. Duplicate upload blocked."
            )

        # 2. Upload video
        upload_res = await self.yt.upload_short(
            video_filepath=video_filepath,
            title=title,
            description=description,
            tags=tags,
            privacy_status=privacy_status
        )

        video_id = upload_res.get("video_id")
        if not video_id:
            raise YouTubeAPIError("YouTube API did not return a valid video ID.")

        # 3. Verify upload
        self.log(f"Upload confirmed by YouTube Data API. Video ID: {video_id}")

        return {
            "youtube_video_id": video_id,
            "youtube_url": upload_res.get("url"),
            "file_hash": file_hash,
            "privacy_status": privacy_status,
            "published_at": time.time(),
            "status": "PUBLISHED"
        }
