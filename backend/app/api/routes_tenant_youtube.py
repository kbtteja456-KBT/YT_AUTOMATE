"""Per-tenant YouTube OAuth 2.0 flow securely associating channels to specific workspaces."""

import hmac
import hashlib
import time
from datetime import datetime, timezone, timedelta
from typing import Any, Optional
from bson import ObjectId
from fastapi import APIRouter, HTTPException, Query, Request, Depends, status
from fastapi.responses import RedirectResponse

from backend.app.config import settings
from backend.app.core.db import AsyncMongoDB
from backend.app.core.auth import get_current_user, get_current_workspace, get_jwt_secret
from backend.app.core.oauth import GoogleOAuthManager
from backend.app.core.security import encrypt_token
from backend.app.core.logging import logger
from backend.app.models.channel import YouTubeChannel, OAuthTokenRecord

router = APIRouter(prefix="/tenant/youtube", tags=["tenant_youtube"])


def sign_oauth_state(workspace_id: str, user_id: str) -> str:
    """Generate tamper-proof HMAC-signed state payload holding workspace context."""
    timestamp = str(int(time.time()))
    payload = f"{workspace_id}:{user_id}:{timestamp}"
    secret = get_jwt_secret().encode("utf-8")
    signature = hmac.new(secret, payload.encode("utf-8"), hashlib.sha256).hexdigest()
    return f"{payload}:{signature}"


def verify_oauth_state(state_str: str) -> Optional[tuple[str, str]]:
    """Verify state token integrity and extract (workspace_id, user_id)."""
    try:
        parts = state_str.split(":")
        if len(parts) != 4:
            return None
        workspace_id, user_id, timestamp_str, received_sig = parts
        
        # Check age (expire state after 30 minutes)
        if time.time() - int(timestamp_str) > 1800:
            return None

        payload = f"{workspace_id}:{user_id}:{timestamp_str}"
        secret = get_jwt_secret().encode("utf-8")
        expected_sig = hmac.new(secret, payload.encode("utf-8"), hashlib.sha256).hexdigest()

        if hmac.compare_digest(expected_sig, received_sig):
            return workspace_id, user_id
        return None
    except Exception:
        return None


@router.post("/connect")
async def initiate_tenant_youtube_auth(
    user: dict[str, Any] = Depends(get_current_user),
    workspace: dict[str, Any] = Depends(get_current_workspace)
) -> dict[str, Any]:
    """Generate Google OAuth consent URL carrying signed tenant context in the state parameter."""
    ws_id = str(workspace["_id"])
    user_id = str(user["_id"])
    state = sign_oauth_state(ws_id, user_id)

    # Note: Redirect URI points to the tenant callback route
    auth_url = GoogleOAuthManager.get_authorization_url(state=state)
    return {
        "auth_url": auth_url,
        "instructions": "Navigate to auth_url to authorize your own YouTube channel."
    }


@router.get("/callback")
async def handle_tenant_youtube_callback(
    request: Request,
    code: str = Query(...),
    state: str = Query(...)
) -> Any:
    """Handle Google OAuth callback, verify state signature, and securely bind tokens to workspace."""
    parsed = verify_oauth_state(state)
    if not parsed:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired OAuth state token. Please initiate connection again."
        )

    workspace_id, user_id = parsed

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

        # 3. Store encrypted tokens scoped to this workspace
        token_record = OAuthTokenRecord(
            workspace_id=workspace_id,
            channel_id=channel_id,
            encrypted_refresh_token=encrypt_token(refresh_token),
            encrypted_access_token=encrypt_token(access_token),
            token_expiry=datetime.now(timezone.utc) + timedelta(seconds=tokens.get("expires_in", 3600)),
            scopes=tokens.get("scope", "").split(" ")
        )

        channel_record = YouTubeChannel(
            workspace_id=workspace_id,
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

        db = AsyncMongoDB.get_db()
        await db.oauth_tokens.update_one(
            {"workspace_id": workspace_id, "channel_id": channel_id},
            {"$set": token_record.to_mongo_dict()},
            upsert=True
        )
        await db.youtube_channels.update_one(
            {"workspace_id": workspace_id, "channel_id": channel_id},
            {"$set": channel_record.to_mongo_dict()},
            upsert=True
        )

        # Update active workspace document with connected channel reference
        try:
            ws_oid = ObjectId(workspace_id)
            await db.workspaces.update_one(
                {"_id": ws_oid},
                {"$set": {"connected_channel_id": channel_id, "updated_at": datetime.now(timezone.utc)}}
            )
        except Exception:
            pass

        accept_header = request.headers.get("accept", "")
        # If user opened directly in browser or redirect flow
        frontend_url = request.headers.get("origin") or "http://localhost:3000"
        if "text/html" in accept_header:
            return RedirectResponse(url=f"{frontend_url}?youtube_connected=true")

        return {
            "status": "CONNECTED",
            "workspace_id": workspace_id,
            "channel_id": channel_id,
            "channel_title": profile["title"],
            "message": f"Channel '{profile['title']}' connected successfully to workspace."
        }

    except Exception as e:
        logger.error(f"Tenant OAuth callback error: {e}")
        raise HTTPException(status_code=500, detail=str(e))
