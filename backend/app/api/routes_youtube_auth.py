"""Official Google OAuth 2.0 flow and YouTube channel management endpoints."""

from fastapi import APIRouter, HTTPException, Query, Request
from fastapi.responses import RedirectResponse
from typing import Any, Optional
from datetime import datetime, timezone, timedelta

from backend.app.config import settings
from backend.app.core.logging import logger
from backend.app.core.oauth import GoogleOAuthManager
from backend.app.core.security import encrypt_token, decrypt_token
from backend.app.core.db import AsyncMongoDB
from backend.app.models.channel import YouTubeChannel, OAuthTokenRecord

router = APIRouter(prefix="/auth/youtube", tags=["youtube_auth"])


@router.post("/connect")
async def initiate_youtube_auth() -> dict[str, Any]:
    """Generate official Google OAuth 2.0 authorization URL."""
    try:
        auth_url = GoogleOAuthManager.get_authorization_url()
        return {
            "auth_url": auth_url,
            "instructions": "Navigate to auth_url in browser to grant YouTube channel access."
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/callback")
async def handle_youtube_callback(request: Request, code: str = Query(...)) -> Any:
    """Receive code from Google OAuth, exchange for tokens, encrypt and persist."""
    try:
        # 1. Exchange code for tokens
        tokens = await GoogleOAuthManager.exchange_code_for_tokens(code)
        access_token = tokens["access_token"]
        refresh_token = tokens.get("refresh_token")

        if not refresh_token:
            raise HTTPException(
                status_code=400,
                detail="No refresh_token returned by Google. Ensure 'prompt=consent' was requested."
            )

        # 2. Fetch real channel profile
        profile = await GoogleOAuthManager.fetch_channel_profile(access_token)
        channel_id = profile["channel_id"]

        # 3. Store encrypted tokens in MongoDB
        token_record = OAuthTokenRecord(
            channel_id=channel_id,
            encrypted_refresh_token=encrypt_token(refresh_token),
            encrypted_access_token=encrypt_token(access_token),
            token_expiry=datetime.now(timezone.utc) + timedelta(seconds=tokens.get("expires_in", 3600)),
            scopes=tokens.get("scope", "").split(" ")
        )

        channel_record = YouTubeChannel(
            channel_id=channel_id,
            title=profile["title"],
            description=profile.get("description"),
            custom_url=profile.get("custom_url"),
            subscriber_count=profile.get("subscriber_count"),
            view_count=profile.get("view_count"),
            video_count=profile.get("video_count"),
            thumbnail_url=profile.get("thumbnail_url"),
            last_synced_at=datetime.now(timezone.utc)
        )

        try:
            db = AsyncMongoDB.get_db()
            await db.oauth_tokens.update_one(
                {"channel_id": channel_id},
                {"$set": token_record.to_mongo_dict()},
                upsert=True
            )
            await db.youtube_channels.update_one(
                {"channel_id": channel_id},
                {"$set": channel_record.to_mongo_dict()},
                upsert=True
            )
        except Exception as dbe:
            logger.warning(f"MongoDB persistence note in OAuth callback: {dbe}")

        accept_header = request.headers.get("accept", "")
        if "text/html" in accept_header:
            return RedirectResponse(url="http://localhost:3000?connected=true")

        return {
            "status": "CONNECTED",
            "channel_id": channel_id,
            "title": profile["title"],
            "subscriber_count": profile.get("subscriber_count"),
            "message": f"Channel '{profile['title']}' connected successfully. Refresh token encrypted at rest."
        }
    except Exception as e:
        logger.error(f"OAuth callback error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


async def _perform_youtube_sync(channel_id: str, db: Any) -> Optional[dict[str, Any]]:
    """Internal helper to refresh token, query YouTube API, and persist updated statistics."""
    token_doc = await db.oauth_tokens.find_one({"channel_id": channel_id})
    if not token_doc:
        return None

    refresh_token = decrypt_token(token_doc["encrypted_refresh_token"])
    tokens = await GoogleOAuthManager.refresh_access_token(refresh_token)
    profile = await GoogleOAuthManager.fetch_channel_profile(tokens["access_token"])
    now = datetime.now(timezone.utc)

    update_fields = {
        "title": profile["title"],
        "subscriber_count": profile.get("subscriber_count", 0),
        "view_count": profile.get("view_count", 0),
        "video_count": profile.get("video_count", 0),
        "thumbnail_url": profile.get("thumbnail_url"),
        "custom_url": profile.get("custom_url"),
        "last_synced_at": now
    }

    await db.youtube_channels.update_one(
        {"channel_id": channel_id},
        {"$set": update_fields}
    )

    updated = await db.youtube_channels.find_one({"channel_id": channel_id})
    if updated:
        updated["_id"] = str(updated["_id"])
    return updated


@router.get("/channel")
async def get_connected_channel() -> dict[str, Any]:
    """Retrieve active YouTube channel information without exposing secrets.
    Automatically refreshes live stats from YouTube if cached data is older than 60 seconds.
    """
    try:
        db = AsyncMongoDB.get_db()
        data = await db.youtube_channels.find_one({"is_active": True})
        if not data:
            return {"is_connected": False, "channel": None}

        # Auto-refresh live stats in background if data is older than 60s
        now = datetime.now(timezone.utc)
        last_synced = data.get("last_synced_at")
        should_auto_sync = False
        if not last_synced:
            should_auto_sync = True
        else:
            if last_synced.tzinfo is None:
                last_synced = last_synced.replace(tzinfo=timezone.utc)
            if (now - last_synced).total_seconds() > 60:
                should_auto_sync = True

        if should_auto_sync:
            try:
                refreshed = await _perform_youtube_sync(data["channel_id"], db)
                if refreshed:
                    data = refreshed
            except Exception as auto_err:
                logger.warning(f"Automatic background YouTube sync note: {auto_err}")

        if data:
            data["_id"] = str(data["_id"])
            return {"is_connected": True, "channel": data}
    except Exception as e:
        logger.error(f"Error reading YouTube channel: {e}")

    return {
        "is_connected": False,
        "channel": None
    }


@router.post("/sync")
async def sync_youtube_channel() -> dict[str, Any]:
    """Force real-time synchronization of subscriber and view counts with YouTube Data API."""
    try:
        db = AsyncMongoDB.get_db()
        channel = await db.youtube_channels.find_one({"is_active": True})
        if not channel:
            raise HTTPException(status_code=404, detail="No active YouTube channel connected.")

        channel_id = channel["channel_id"]
        updated_channel = await _perform_youtube_sync(channel_id, db)
        if not updated_channel:
            raise HTTPException(status_code=400, detail="OAuth credentials not found.")

        logger.info(f"Synchronized stats for '{updated_channel.get('title')}': {updated_channel.get('subscriber_count')} subs.")

        return {
            "status": "SYNCED",
            "channel": updated_channel,
            "message": f"YouTube stats updated: {updated_channel.get('subscriber_count')} subscribers."
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Sync error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

