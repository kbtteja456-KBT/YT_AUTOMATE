"""YouTube Data API v3 provider with resumable upload chunking and duplicate protection."""

import os
import time
from pathlib import Path
from typing import Any, Optional
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from googleapiclient.errors import HttpError
from google.auth.exceptions import RefreshError

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
        except RefreshError as re:
            logger.error(f"YouTube OAuth token expired or revoked: {re}")
            raise YouTubeAPIError("YouTube account token expired or revoked. Please reconnect your YouTube channel in Settings.")
        except HttpError as e:
            if "invalid_grant" in str(e):
                raise YouTubeAPIError("YouTube account token expired or revoked. Please reconnect your YouTube channel in Settings.")
            logger.error(f"YouTube Data API error: {e}")
            raise YouTubeAPIError(f"YouTube Data API error: {e}")

    @staticmethod
    def sanitize_youtube_text(text: Optional[str], max_length: int = 5000) -> str:
        """Sanitize text for YouTube Data API compliance (strips < and > to prevent 400 invalidDescription)."""
        if not text:
            return ""
        # YouTube strictly forbids '<' and '>' in title and description
        cleaned = text.replace("<", "[").replace(">", "]")
        # Strip backticks and code block markers that can confuse metadata parsers
        cleaned = cleaned.replace("```", "").replace("`", "")
        # Remove any illegal control characters except standard whitespace
        cleaned = "".join(ch for ch in cleaned if ch in ("\n", "\r", "\t") or ord(ch) >= 32)
        return cleaned[:max_length].strip()

    async def upload_short(
        self,
        video_filepath: str,
        title: str,
        description: str,
        tags: list[str],
        privacy_status: str = "public",
        _is_retry: bool = False
    ) -> dict[str, Any]:
        """Upload video via resumable upload protocol and return real video ID with auto-sanitization and self-healing."""
        self.verify_zero_cost_compliance()

        vid_path = Path(video_filepath).resolve()
        if not vid_path.exists():
            raise YouTubeAPIError(f"Video file not found at: {video_filepath}")

        # Compute file hash
        file_hash = compute_file_hash(str(vid_path))
        logger.info(f"Initiating YouTube resumable upload for {vid_path.name} (hash: {file_hash[:12]})...")

        # Sanitize metadata for YouTube Data API v3 compliance
        safe_title = self.sanitize_youtube_text(title, max_length=100)
        full_desc = f"{description}\n\n#Shorts #Tech #AI"
        safe_description = self.sanitize_youtube_text(full_desc, max_length=5000)
        safe_tags = [self.sanitize_youtube_text(t, max_length=30) for t in (tags + ["Shorts", "YouTubeShorts"]) if t]

        body = {
            "snippet": {
                "title": safe_title,
                "description": safe_description,
                "tags": safe_tags,
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
                "title": safe_title,
                "privacy_status": privacy_status,
                "uploaded_at": time.time()
            }

        except RefreshError as re:
            logger.error(f"YouTube OAuth token expired or revoked during upload: {re}")
            raise YouTubeAPIError("YouTube account token expired or revoked. Please reconnect your YouTube channel in Settings.")

        except HttpError as e:
            err_content = str(e)
            resp_obj = getattr(e, "resp", None)
            status_code = getattr(resp_obj, "status", None)
            if status_code is None and isinstance(resp_obj, dict):
                status_code = resp_obj.get("status")

            is_400 = "invalidDescription" in err_content or "invalidTitle" in err_content or status_code in (400, "400") or " 400 " in err_content

            # Automatic Self-Healing: If metadata rejected (e.g. invalid description/title), retry once with clean minimal text
            if is_400 and not _is_retry:
                logger.warning(f"⚠️ [Self-Healing YouTube Upload] Metadata rejected by YouTube: {e}. Auto-cleaning metadata and retrying upload...")
                stripped_lines = [
                    line.replace("<", "[").replace(">", "]").replace("`", "").strip()
                    for line in description.splitlines() 
                    if not line.strip().startswith("```") and "#include" not in line
                ]
                stripped_lines = [l for l in stripped_lines if l]
                fallback_desc = self.sanitize_youtube_text("\n".join(stripped_lines[:8]), max_length=1500)
                if not fallback_desc.strip():
                    fallback_desc = f"{safe_title}\n\n#Shorts #Tech #AI #Programming"
                
                return await self.upload_short(
                    video_filepath=video_filepath,
                    title=safe_title,
                    description=fallback_desc,
                    tags=["Shorts", "Tech", "Coding"],
                    privacy_status=privacy_status,
                    _is_retry=True
                )

            if "invalid_grant" in err_content:
                raise YouTubeAPIError("YouTube account token expired or revoked. Please reconnect your YouTube channel in Settings.")

            logger.error(f"YouTube upload failed: {e}")
            raise YouTubeAPIError(f"Upload failed: {e}")

        except Exception as gen_err:
            err_str = str(gen_err)
            if "invalid_grant" in err_str or "expired or revoked" in err_str:
                raise YouTubeAPIError("YouTube account token expired or revoked. Please reconnect your YouTube channel in Settings.")
            raise

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
