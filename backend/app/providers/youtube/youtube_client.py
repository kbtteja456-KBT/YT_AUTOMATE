"""YouTube Data API v3 provider with resumable upload chunking and duplicate protection."""

import os
import time
from pathlib import Path
from typing import Any, Optional
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from googleapiclient.errors import HttpError

from backend.app.config import settings
from backend.app.core.logging import logger
from backend.app.core.errors import YouTubeAPIError, DuplicateUploadPreventedError
from backend.app.core.oauth import GoogleOAuthManager
from backend.app.core.security import compute_file_hash
from backend.app.models.provider import ProviderHealth, ProviderStatus, ProviderType
from backend.app.providers.base import YouTubeProvider


class YouTubeClientProvider(YouTubeProvider):
    """Production client for YouTube Data API v3 and resumable Shorts uploads."""

    name = "youtube_api_v3"
    provider_type = ProviderType.YOUTUBE
    is_zero_cost = True
    is_paid = False

    def __init__(self, credentials: Optional[Any] = None):
        self.credentials = credentials
        self._service: Optional[Any] = None

    def _get_service(self):
        """Lazy load authenticated Google API client service."""
        if self._service is None:
            if not self.credentials:
                raise YouTubeAPIError("Google OAuth credentials are required for YouTube API operations.")
            self._service = build("youtube", "v3", credentials=self.credentials, cache_discovery=False)
        return self._service

    async def get_channel_info(self, channel_id: Optional[str] = None) -> dict[str, Any]:
        """Retrieve real channel statistics from YouTube API."""
        self.verify_zero_cost_compliance()
        try:
            service = self._get_service()
            request = service.channels().list(part="snippet,statistics", mine=True)
            response = request.execute()

            items = response.get("items", [])
            if not items:
                raise YouTubeAPIError("No YouTube channel found for authenticated account.")

            item = items[0]
            stats = item.get("statistics", {})
            snippet = item.get("snippet", {})

            return {
                "channel_id": item.get("id"),
                "title": snippet.get("title"),
                "subscriber_count": int(stats.get("subscriberCount", 0)) if "subscriberCount" in stats else "NOT AVAILABLE",
                "view_count": int(stats.get("viewCount", 0)) if "viewCount" in stats else "NOT AVAILABLE",
                "video_count": int(stats.get("videoCount", 0)) if "videoCount" in stats else "NOT AVAILABLE",
                "custom_url": snippet.get("customUrl"),
                "thumbnail_url": snippet.get("thumbnails", {}).get("default", {}).get("url")
            }
        except HttpError as e:
            logger.error(f"YouTube Data API error: {e}")
            raise YouTubeAPIError(f"YouTube Data API error: {e}")

    async def upload_short(
        self,
        video_filepath: str,
        title: str,
        description: str,
        tags: list[str],
        privacy_status: str = "public"
    ) -> dict[str, Any]:
        """Upload video via resumable upload protocol and return real video ID."""
        self.verify_zero_cost_compliance()

        vid_path = Path(video_filepath).resolve()
        if not vid_path.exists():
            raise YouTubeAPIError(f"Video file not found at: {video_filepath}")

        # Compute file hash
        file_hash = compute_file_hash(str(vid_path))
        logger.info(f"Initiating YouTube resumable upload for {vid_path.name} (hash: {file_hash[:12]})...")

        body = {
            "snippet": {
                "title": title,
                "description": f"{description}\n\n#Shorts #Tech #AI",
                "tags": tags + ["Shorts", "YouTubeShorts"],
                "categoryId": "28"  # Science & Technology
            },
            "status": {
                "privacyStatus": privacy_status,
                "selfDeclaredMadeForKids": False
            }
        }

        service = self._get_service()

        # Resumable upload chunked at 4MB
        media = MediaFileUpload(
            str(vid_path),
            mimetype="video/mp4",
            chunksize=4 * 1024 * 1024,
            resumable=True
        )

        try:
            insert_request = service.videos().insert(
                part="snippet,status",
                body=body,
                media_body=media
            )

            response = None
            while response is None:
                status, response = insert_request.next_chunk()
                if status:
                    progress_pct = int(status.progress() * 100)
                    logger.info(f"YouTube Upload Progress: {progress_pct}%")

            video_id = response.get("id")
            if not video_id:
                raise YouTubeAPIError("YouTube API did not return a valid video ID after upload.")

            youtube_url = f"https://www.youtube.com/shorts/{video_id}"
            logger.info(f"Successfully uploaded YouTube Short! ID: {video_id} -> {youtube_url}")

            return {
                "video_id": video_id,
                "url": youtube_url,
                "file_hash": file_hash,
                "title": title,
                "privacy_status": privacy_status,
                "uploaded_at": time.time()
            }

        except HttpError as e:
            logger.error(f"YouTube upload failed: {e}")
            raise YouTubeAPIError(f"Upload failed: {e}")

    async def get_video_analytics(self, youtube_video_id: str) -> dict[str, Any]:
        """Query real analytics for a video. Missing metrics return NOT AVAILABLE."""
        self.verify_zero_cost_compliance()
        try:
            service = self._get_service()
            request = service.videos().list(part="statistics", id=youtube_video_id)
            response = request.execute()

            items = response.get("items", [])
            if not items:
                return {
                    "video_id": youtube_video_id,
                    "views": "NOT AVAILABLE",
                    "likes": "NOT AVAILABLE",
                    "comments": "NOT AVAILABLE"
                }

            stats = items[0].get("statistics", {})
            return {
                "video_id": youtube_video_id,
                "views": int(stats["viewCount"]) if "viewCount" in stats else "NOT AVAILABLE",
                "likes": int(stats["likeCount"]) if "likeCount" in stats else "NOT AVAILABLE",
                "comments": int(stats["commentCount"]) if "commentCount" in stats else "NOT AVAILABLE"
            }
        except Exception as e:
            logger.warning(f"Error fetching analytics for {youtube_video_id}: {e}")
            return {
                "video_id": youtube_video_id,
                "views": "NOT AVAILABLE",
                "likes": "NOT AVAILABLE",
                "comments": "NOT AVAILABLE"
            }

    async def check_health(self) -> ProviderHealth:
        """Verify YouTube API configuration."""
        if not self.credentials:
            return ProviderHealth(
                provider_name=self.name,
                provider_type=self.provider_type,
                status=ProviderStatus.NOT_CONFIGURED,
                is_zero_cost=True,
                is_paid=False,
                error_message="OAuth credentials not provided."
            )
        try:
            service = self._get_service()
            return ProviderHealth(
                provider_name=self.name,
                provider_type=self.provider_type,
                status=ProviderStatus.CONNECTED,
                is_zero_cost=True,
                is_paid=False,
                details={"authenticated": True}
            )
        except Exception as e:
            return ProviderHealth(
                provider_name=self.name,
                provider_type=self.provider_type,
                status=ProviderStatus.OFFLINE,
                is_zero_cost=True,
                is_paid=False,
                error_message=str(e)
            )
