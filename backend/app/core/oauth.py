"""Official Google OAuth 2.0 flow and credentials manager for YouTube Data API v3."""

import httpx
from datetime import datetime, timezone, timedelta
from typing import Any, Optional
from google.oauth2.credentials import Credentials

from backend.app.config import settings
from backend.app.core.logging import logger
from backend.app.core.security import encrypt_token, decrypt_token
from backend.app.core.errors import YouTubeAPIError

GOOGLE_TOKEN_URI = "https://oauth2.googleapis.com/token"
GOOGLE_AUTH_URI = "https://accounts.google.com/o/oauth2/v2/auth"
YOUTUBE_CHANNELS_API = "https://www.googleapis.com/youtube/v3/channels"

DEFAULT_SCOPES = [
    "https://www.googleapis.com/auth/youtube.upload",
    "https://www.googleapis.com/auth/youtube.readonly",
    "https://www.googleapis.com/auth/yt-analytics.readonly"
]


class GoogleOAuthManager:
    """Manages Google OAuth 2.0 authentication, token exchange, and encrypted persistence."""

    @staticmethod
    def get_authorization_url(
        client_id: Optional[str] = None,
        redirect_uri: Optional[str] = None,
        state: Optional[str] = None
    ) -> str:
        """Construct the official Google OAuth 2.0 consent screen URL."""
        cid = client_id or settings.google_client_id
        ruri = redirect_uri or settings.youtube_redirect_uri

        if not cid:
            raise YouTubeAPIError("GOOGLE_CLIENT_ID is not configured.")

        params = {
            "client_id": cid,
            "redirect_uri": ruri,
            "response_type": "code",
            "scope": " ".join(DEFAULT_SCOPES),
            "access_type": "offline",
            "prompt": "consent"
        }
        if state:
            params["state"] = state

        return str(httpx.URL(GOOGLE_AUTH_URI, params=params))

    @staticmethod
    async def exchange_code_for_tokens(
        code: str,
        client_id: Optional[str] = None,
        client_secret: Optional[str] = None,
        redirect_uri: Optional[str] = None
    ) -> dict[str, Any]:
        """Exchange authorization code for access and refresh tokens."""
        cid = client_id or settings.google_client_id
        csec = client_secret or settings.google_client_secret
        ruri = redirect_uri or settings.youtube_redirect_uri

        if not cid or not csec:
            raise YouTubeAPIError("GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET are required.")

        payload = {
            "code": code,
            "client_id": cid,
            "client_secret": csec,
            "redirect_uri": ruri,
            "grant_type": "authorization_code"
        }

        async with httpx.AsyncClient() as client:
            resp = await client.post(GOOGLE_TOKEN_URI, data=payload)
            if resp.status_code != 200:
                logger.error(f"Google token exchange failed: {resp.text}")
                raise YouTubeAPIError(f"Failed to exchange code for tokens: {resp.text}")
            data = resp.json()

        return {
            "access_token": data.get("access_token"),
            "refresh_token": data.get("refresh_token"),
            "expires_in": data.get("expires_in", 3600),
            "token_type": data.get("token_type", "Bearer"),
            "scope": data.get("scope", "")
        }

    @staticmethod
    async def refresh_access_token(
        refresh_token: str,
        client_id: Optional[str] = None,
        client_secret: Optional[str] = None
    ) -> dict[str, Any]:
        """Use refresh token to acquire a new short-lived access token."""
        cid = client_id or settings.google_client_id
        csec = client_secret or settings.google_client_secret

        payload = {
            "refresh_token": refresh_token,
            "client_id": cid,
            "client_secret": csec,
            "grant_type": "refresh_token"
        }

        async with httpx.AsyncClient() as client:
            resp = await client.post(GOOGLE_TOKEN_URI, data=payload)
            if resp.status_code != 200:
                logger.error(f"Token refresh failed: {resp.text}")
                raise YouTubeAPIError(f"Failed to refresh access token: {resp.text}")
            return resp.json()

    @staticmethod
    async def fetch_channel_profile(access_token: str) -> dict[str, Any]:
        """Query real YouTube channel statistics for the authenticated user."""
        headers = {"Authorization": f"Bearer {access_token}"}
        params = {
            "part": "snippet,statistics",
            "mine": "true"
        }

        async with httpx.AsyncClient() as client:
            resp = await client.get(YOUTUBE_CHANNELS_API, headers=headers, params=params)
            if resp.status_code != 200:
                logger.error(f"Failed to fetch YouTube channel profile: {resp.text}")
                raise YouTubeAPIError(f"YouTube Data API error: {resp.text}")
            data = resp.json()

        items = data.get("items", [])
        if not items:
            raise YouTubeAPIError("No YouTube channel found for authenticated Google account.")

        item = items[0]
        snippet = item.get("snippet", {})
        statistics = item.get("statistics", {})

        return {
            "channel_id": item.get("id"),
            "title": snippet.get("title", "YouTube Channel"),
            "description": snippet.get("description", ""),
            "custom_url": snippet.get("customUrl"),
            "thumbnail_url": snippet.get("thumbnails", {}).get("default", {}).get("url"),
            "subscriber_count": int(statistics.get("subscriberCount", 0)) if "subscriberCount" in statistics else None,
            "view_count": int(statistics.get("viewCount", 0)) if "viewCount" in statistics else None,
            "video_count": int(statistics.get("videoCount", 0)) if "videoCount" in statistics else None,
        }

    @staticmethod
    def get_google_credentials(
        access_token: str,
        refresh_token: str,
        client_id: Optional[str] = None,
        client_secret: Optional[str] = None
    ) -> Credentials:
        """Construct Google oauth2 Credentials object for googleapiclient."""
        return Credentials(
            token=access_token,
            refresh_token=refresh_token,
            token_uri=GOOGLE_TOKEN_URI,
            client_id=client_id or settings.google_client_id,
            client_secret=client_secret or settings.google_client_secret,
            scopes=DEFAULT_SCOPES
        )
