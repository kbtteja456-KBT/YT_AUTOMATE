"""Zero-downtime migration module ensuring the platform owner's existing channel,
OAuth tokens, videos, and job history are seamlessly mapped to their default workspace.
"""

from datetime import datetime, timezone
from typing import Any, Optional, Dict
from bson import ObjectId
from pymongo.database import Database

from backend.app.core.logging import logger
from backend.app.config import settings

OWNER_EMAIL = "kbtteja456@gmail.com"
LEGACY_WORKSPACE_SLUG = "legacy-owner-workspace"


def get_or_create_legacy_workspace(db: Database, owner_id: Optional[str] = None) -> Dict[str, Any]:
    """Find or initialize the protected owner workspace representing the current working channel."""
    ws = db.workspaces.find_one({"is_legacy_default": True})
    if not ws:
        ws = db.workspaces.find_one({"slug": LEGACY_WORKSPACE_SLUG})

    # Detect existing connected channel if available
    channel_doc = db.youtube_channels.find_one({"is_active": True}) or db.youtube_channels.find_one()
    channel_id = channel_doc.get("channel_id") if channel_doc else None
    channel_title = channel_doc.get("title") if channel_doc else "Bhanu Teja (Owner Channel)"

    now = datetime.now(timezone.utc)
    if not ws:
        doc = {
            "name": f"{channel_title} [Live Channel]",
            "slug": LEGACY_WORKSPACE_SLUG,
            "owner_id": owner_id or "pending_owner_registration",
            "is_legacy_default": True,
            "autopilot_enabled": True,
            "niche": "Python Programming",
            "content_template": "quiz_card",
            "visual_style": "hand_drawn_sketch",
            "voice_id": "en-US-ChristopherNeural",
            "schedule": {
                "slot_1_time": "07:00",
                "slot_2_time": "18:00",
                "timezone": settings.timezone,
                "videos_per_day": 2,
            },
            "trial_quota": {
                "max_videos": 999999,  # Owner has unrestricted access
                "videos_generated": 0,
                "max_ai_tokens": 99999999,
                "ai_tokens_used": 0,
                "max_tts_seconds": 99999999,
                "tts_seconds_used": 0,
                "is_exhausted": False,
            },
            "connected_channel_id": channel_id,
            "created_at": now,
            "updated_at": now,
        }
        res = db.workspaces.insert_one(doc)
        doc["_id"] = res.inserted_id
        ws = doc
        logger.info(f"Initialized Legacy Owner Workspace: {ws['_id']}")
    elif owner_id and ws.get("owner_id") != owner_id:
        db.workspaces.update_one(
            {"_id": ws["_id"]},
            {"$set": {"owner_id": owner_id, "updated_at": now}}
        )
        ws["owner_id"] = owner_id

    # Migration step: Associate unassigned historical assets to this legacy workspace
    ws_id_str = str(ws["_id"])

    # 1. Channels
    db.youtube_channels.update_many(
        {"$or": [{"workspace_id": None}, {"workspace_id": {"$exists": False}}]},
        {"$set": {"workspace_id": ws_id_str}}
    )

    # 2. OAuth Tokens
    db.oauth_tokens.update_many(
        {"$or": [{"workspace_id": None}, {"workspace_id": {"$exists": False}}]},
        {"$set": {"workspace_id": ws_id_str}}
    )

    # 3. Videos
    vids_updated = db.videos.update_many(
        {"$or": [{"workspace_id": None}, {"workspace_id": {"$exists": False}}]},
        {"$set": {"workspace_id": ws_id_str}}
    )
    if vids_updated.modified_count > 0:
        logger.info(f"Migrated {vids_updated.modified_count} existing videos to Owner Workspace {ws_id_str}.")

    # 4. Publishing Jobs
    jobs_updated = db.publishing_jobs.update_many(
        {"$or": [{"workspace_id": None}, {"workspace_id": {"$exists": False}}]},
        {"$set": {"workspace_id": ws_id_str}}
    )
    if jobs_updated.modified_count > 0:
        logger.info(f"Migrated {jobs_updated.modified_count} existing jobs to Owner Workspace {ws_id_str}.")

    # 5. Activity
    db.activity.update_many(
        {"$or": [{"workspace_id": None}, {"workspace_id": {"$exists": False}}]},
        {"$set": {"workspace_id": ws_id_str}}
    )

    return ws
