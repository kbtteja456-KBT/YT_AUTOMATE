"""Public and session authentication endpoints for multi-tenant registration and login."""

import re
from datetime import datetime, timezone
from typing import Any, Optional
from bson import ObjectId
from fastapi import APIRouter, HTTPException, Depends, status
from pydantic import BaseModel, EmailStr, Field

from backend.app.core.db import AsyncMongoDB, SyncMongoDB
from backend.app.core.auth import (
    hash_password, verify_password, create_access_token,
    get_current_user, get_current_workspace
)
from backend.app.core.migration import OWNER_EMAIL, get_or_create_legacy_workspace
from backend.app.core.logging import logger

router = APIRouter(prefix="/auth", tags=["auth"])


class RegisterRequest(BaseModel):
    email: str = Field(description="User email address")
    password: str = Field(min_length=6, description="Password with minimum 6 characters")
    full_name: Optional[str] = Field(default=None, description="Display name")


class LoginRequest(BaseModel):
    email: str
    password: str


class AuthResponse(BaseModel):
    access_token: str
    token_type: str = "Bearer"
    user: dict[str, Any]
    workspace: dict[str, Any]


def slugify(text: str) -> str:
    """Generate a clean URL-friendly slug."""
    text = text.lower().strip()
    text = re.sub(r"[^\w\s-]", "", text)
    text = re.sub(r"[\s_-]+", "-", text)
    return text.strip("-") or "workspace"


@router.post("/register", response_model=AuthResponse)
async def register(req: RegisterRequest) -> Any:
    """Public user registration endpoint with automatic owner migration hook."""
    clean_email = req.email.strip().lower()
    db = AsyncMongoDB.get_db()
    sync_db = SyncMongoDB.get_db()

    # 1. Check if user already exists
    existing = await db.users.find_one({"email": clean_email})
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="An account with this email already exists. Please log in."
        )

    # 2. Check if this is the designated platform owner
    is_owner = (clean_email == OWNER_EMAIL.lower())
    now = datetime.now(timezone.utc)

    # 3. Create user record
    hashed = hash_password(req.password)
    user_doc = {
        "email": clean_email,
        "password_hash": hashed,
        "full_name": req.full_name or (clean_email.split("@")[0].title()),
        "is_owner": is_owner,
        "is_active": True,
        "created_at": now,
        "updated_at": now,
    }
    user_res = await db.users.insert_one(user_doc)
    user_id = str(user_res.inserted_id)
    user_doc["_id"] = user_res.inserted_id
    user_doc["id"] = user_id

    # 4. Create or assign workspace
    if is_owner:
        # One-time migration for owner: bind existing channel, videos, and schedule
        logger.info(f"Owner registered ({clean_email}). Triggering legacy workspace binding...")
        legacy_ws = get_or_create_legacy_workspace(sync_db, owner_id=user_id)
        ws_id = str(legacy_ws["_id"])
        await db.users.update_one({"_id": user_res.inserted_id}, {"$set": {"default_workspace_id": ws_id}})
        workspace_data = {
            "id": ws_id,
            "name": legacy_ws.get("name"),
            "slug": legacy_ws.get("slug"),
            "is_legacy_default": True,
            "autopilot_enabled": legacy_ws.get("autopilot_enabled", True),
            "connected_channel_id": legacy_ws.get("connected_channel_id"),
            "trial_quota": legacy_ws.get("trial_quota"),
        }
    else:
        # Standard flow for a new tenant: clean slate with 3-video trial
        ws_name = f"{user_doc['full_name']}'s Channel"
        ws_slug = f"{slugify(user_doc['full_name'])}-{user_id[:6]}"
        ws_doc = {
            "name": ws_name,
            "slug": ws_slug,
            "owner_id": user_id,
            "is_legacy_default": False,
            "autopilot_enabled": False,
            "niche": "Python Programming",
            "content_template": "quiz_card",
            "visual_style": "hand_drawn_sketch",
            "voice_id": "en-US-ChristopherNeural",
            "schedule": {
                "slot_1_time": "07:00",
                "slot_2_time": "18:00",
                "timezone": "Asia/Kolkata",
                "videos_per_day": 2,
            },
            "trial_quota": {
                "max_videos": 3,
                "videos_generated": 0,
                "max_ai_tokens": 60000,
                "ai_tokens_used": 0,
                "max_tts_seconds": 360,
                "tts_seconds_used": 0,
                "is_exhausted": False,
            },
            "connected_channel_id": None,
            "created_at": now,
            "updated_at": now,
        }
        ws_res = await db.workspaces.insert_one(ws_doc)
        ws_id = str(ws_res.inserted_id)
        await db.users.update_one({"_id": user_res.inserted_id}, {"$set": {"default_workspace_id": ws_id}})
        workspace_data = {
            "id": ws_id,
            "name": ws_name,
            "slug": ws_slug,
            "is_legacy_default": False,
            "autopilot_enabled": False,
            "connected_channel_id": None,
            "trial_quota": ws_doc["trial_quota"],
        }

    # 5. Issue JWT
    token = create_access_token(user_id=user_id, email=clean_email, is_owner=is_owner, workspace_id=ws_id)
    return {
        "access_token": token,
        "token_type": "Bearer",
        "user": {
            "id": user_id,
            "email": clean_email,
            "full_name": user_doc["full_name"],
            "is_owner": is_owner,
        },
        "workspace": workspace_data,
    }


@router.post("/login", response_model=AuthResponse)
async def login(req: LoginRequest) -> Any:
    """Authenticate user with email and password."""
    clean_email = req.email.strip().lower()
    db = AsyncMongoDB.get_db()
    sync_db = SyncMongoDB.get_db()

    user = await db.users.find_one({"email": clean_email})
    if not user or not verify_password(req.password, user.get("password_hash", "")):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password."
        )

    user_id = str(user["_id"])
    is_owner = user.get("is_owner", False) or (clean_email == OWNER_EMAIL.lower())

    # Guarantee owner migration check on login as well
    if is_owner:
        legacy_ws = get_or_create_legacy_workspace(sync_db, owner_id=user_id)
        ws_id = str(legacy_ws["_id"])
        workspace_data = {
            "id": ws_id,
            "name": legacy_ws.get("name"),
            "slug": legacy_ws.get("slug"),
            "is_legacy_default": True,
            "autopilot_enabled": legacy_ws.get("autopilot_enabled", True),
            "connected_channel_id": legacy_ws.get("connected_channel_id"),
            "trial_quota": legacy_ws.get("trial_quota"),
        }
    else:
        ws_id = user.get("default_workspace_id")
        ws = None
        if ws_id:
            try:
                ws = await db.workspaces.find_one({"_id": ObjectId(ws_id)})
            except Exception:
                ws = await db.workspaces.find_one({"_id": ws_id})
        if not ws:
            ws = await db.workspaces.find_one({"owner_id": user_id})
        
        ws_id = str(ws["_id"]) if ws else "default"
        workspace_data = {
            "id": ws_id,
            "name": ws.get("name", "Workspace") if ws else "Workspace",
            "slug": ws.get("slug", "workspace") if ws else "workspace",
            "is_legacy_default": False,
            "autopilot_enabled": ws.get("autopilot_enabled", False) if ws else False,
            "connected_channel_id": ws.get("connected_channel_id") if ws else None,
            "trial_quota": ws.get("trial_quota") if ws else None,
        }

    token = create_access_token(user_id=user_id, email=clean_email, is_owner=is_owner, workspace_id=ws_id)
    return {
        "access_token": token,
        "token_type": "Bearer",
        "user": {
            "id": user_id,
            "email": clean_email,
            "full_name": user.get("full_name"),
            "is_owner": is_owner,
        },
        "workspace": workspace_data,
    }


@router.get("/me")
async def get_my_profile(
    user: dict[str, Any] = Depends(get_current_user),
    workspace: dict[str, Any] = Depends(get_current_workspace)
) -> dict[str, Any]:
    """Fetch profile of currently authenticated user along with their active workspace context."""
    db = AsyncMongoDB.get_db()
    
    # Check connected channel
    channel_info = None
    if workspace.get("connected_channel_id"):
        ch = await db.youtube_channels.find_one({"channel_id": workspace["connected_channel_id"]})
        if ch:
            channel_info = {
                "channel_id": ch["channel_id"],
                "title": ch.get("title"),
                "thumbnail_url": ch.get("thumbnail_url"),
                "subscriber_count": ch.get("subscriber_count"),
                "custom_url": ch.get("custom_url"),
            }

    return {
        "user": {
            "id": user["id"],
            "email": user["email"],
            "full_name": user.get("full_name"),
            "is_owner": user.get("is_owner", False),
        },
        "workspace": {
            "id": workspace["id"],
            "name": workspace["name"],
            "slug": workspace["slug"],
            "is_legacy_default": workspace.get("is_legacy_default", False),
            "autopilot_enabled": workspace.get("autopilot_enabled", False),
            "niche": workspace.get("niche", "Python Programming"),
            "schedule": workspace.get("schedule", {}),
            "trial_quota": workspace.get("trial_quota", {}),
            "connected_channel": channel_info,
        }
    }
