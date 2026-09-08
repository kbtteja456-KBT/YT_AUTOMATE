"""Usage ledger accounting and atomic trial quota enforcement preventing race conditions."""

import os
from datetime import datetime, timezone
from typing import Any, Optional, Tuple, Dict
from bson import ObjectId
from pymongo import ReturnDocument
from pymongo.database import Database

from backend.app.config import settings
from backend.app.core.db import SyncMongoDB, AsyncMongoDB
from backend.app.core.logging import logger
from backend.app.models.tenant import UsageLedgerRecord


def is_platform_trial_disabled() -> bool:
    """Check global kill-switch environment variable."""
    val = os.getenv("DISABLE_PLATFORM_KEY_TRIALS", "false").strip().lower()
    return val in ["true", "1", "yes"]


def record_usage_sync(
    db: Database,
    workspace_id: str,
    provider: str,
    operation: str,
    units: int = 0,
    unit_type: str = "tokens",
    estimated_cost_usd: float = 0.0,
    used_platform_key: bool = False,
    job_id: Optional[str] = None
) -> None:
    """Synchronous usage logging for Celery workers and pipeline stages."""
    try:
        doc = {
            "workspace_id": workspace_id,
            "job_id": job_id,
            "provider": provider,
            "operation": operation,
            "units": units,
            "unit_type": unit_type,
            "estimated_cost_usd": estimated_cost_usd,
            "used_platform_key": used_platform_key,
            "timestamp": datetime.now(timezone.utc),
        }
        db.usage_ledger.insert_one(doc)
    except Exception as e:
        logger.warning(f"Could not record usage ledger entry: {e}")


async def check_and_acquire_trial_quota_atomic(
    workspace_id: str,
    is_video_generation: bool = True
) -> Tuple[bool, str]:
    """Atomically verify and decrement available trial quota in MongoDB.
    
    Prevents race conditions from concurrent execution requests.
    Returns (allowed: bool, reason: str).
    """
    if is_platform_trial_disabled():
        return False, "Platform key trials are currently disabled platform-wide. Please add your own API keys in Settings."

    db = AsyncMongoDB.get_db()
    
    # 1. Fetch workspace to check if legacy/exempt
    try:
        ws = await db.workspaces.find_one({"_id": ObjectId(workspace_id)})
    except Exception:
        ws = await db.workspaces.find_one({"_id": workspace_id})

    if not ws:
        return False, "Workspace not found."

    # Owner's default legacy workspace has unlimited quota
    if ws.get("is_legacy_default", False):
        return True, "Legacy owner workspace"

    # Check if workspace already has their own BYOK key configured
    custom_ai_key = await db.workspace_api_keys.find_one({
        "workspace_id": workspace_id,
        "provider": "openrouter",
        "is_valid": True
    })
    if custom_ai_key:
        return True, "Using tenant's own API key (BYOK)"

    # 2. Atomic find_one_and_update to claim a trial video slot
    inc_query: Dict[str, Any] = {}
    if is_video_generation:
        inc_query["trial_quota.videos_generated"] = 1

    try:
        updated = await db.workspaces.find_one_and_update(
            {
                "_id": ws["_id"],
                "trial_quota.is_exhausted": False,
                "trial_quota.videos_generated": {"$lt": ws.get("trial_quota", {}).get("max_videos", 3)}
            },
            {
                "$inc": inc_query,
                "$set": {"updated_at": datetime.now(timezone.utc)}
            },
            return_document=ReturnDocument.AFTER
        )

        if not updated:
            # Mark exhausted and auto-pause autopilot to prevent runaway errors
            await db.workspaces.update_one(
                {"_id": ws["_id"]},
                {
                    "$set": {
                        "trial_quota.is_exhausted": True,
                        "autopilot_enabled": False,
                        "updated_at": datetime.now(timezone.utc)
                    }
                }
            )
            return False, "Free trial limit reached (3/3 videos generated). Autopilot has been paused. Add your own API keys in Settings to continue."

        # Check if the new state hit the cap
        current_videos = updated.get("trial_quota", {}).get("videos_generated", 0)
        max_videos = updated.get("trial_quota", {}).get("max_videos", 3)
        if current_videos >= max_videos:
            await db.workspaces.update_one(
                {"_id": ws["_id"]},
                {"$set": {"trial_quota.is_exhausted": True}}
            )

        return True, f"Trial video approved ({current_videos}/{max_videos} used)"

    except Exception as e:
        logger.error(f"Error checking trial quota: {e}")
        return False, f"Trial validation error: {str(e)}"


def check_and_acquire_trial_quota_atomic_sync(
    workspace_id: str,
    is_video_generation: bool = True
) -> Tuple[bool, str]:
    """Synchronously and atomically verify and decrement available trial quota in MongoDB.
    
    Prevents race conditions from concurrent execution requests.
    Returns (allowed: bool, reason: str).
    """
    if is_platform_trial_disabled():
        return False, "Platform key trials are currently disabled platform-wide. Please add your own API keys in Settings."

    db = SyncMongoDB.get_db()
    
    # 1. Fetch workspace to check if legacy/exempt
    try:
        ws = db.workspaces.find_one({"_id": ObjectId(workspace_id)}) if ObjectId.is_valid(workspace_id) else db.workspaces.find_one({"_id": workspace_id})
    except Exception:
        ws = db.workspaces.find_one({"_id": workspace_id})

    if not ws:
        return False, "Workspace not found."

    # Owner's default legacy workspace has unlimited quota
    if ws.get("is_legacy_default", False):
        return True, "Legacy owner workspace"

    # Check if workspace already has their own BYOK key configured
    ws_id_str = str(ws["_id"])
    custom_ai_key = db.workspace_api_keys.find_one({
        "workspace_id": ws_id_str,
        "provider": "openrouter",
        "is_valid": True
    })
    if custom_ai_key:
        return True, "Using tenant's own API key (BYOK)"

    # 2. Atomic find_one_and_update to claim a trial video slot
    inc_query: Dict[str, Any] = {}
    if is_video_generation:
        inc_query["trial_quota.videos_generated"] = 1

    try:
        updated = db.workspaces.find_one_and_update(
            {
                "_id": ws["_id"],
                "trial_quota.is_exhausted": False,
                "trial_quota.videos_generated": {"$lt": ws.get("trial_quota", {}).get("max_videos", 3)}
            },
            {
                "$inc": inc_query,
                "$set": {"updated_at": datetime.now(timezone.utc)}
            },
            return_document=ReturnDocument.AFTER
        )

        if not updated:
            # Mark exhausted and auto-pause autopilot to prevent runaway errors
            db.workspaces.update_one(
                {"_id": ws["_id"]},
                {
                    "$set": {
                        "trial_quota.is_exhausted": True,
                        "autopilot_enabled": False,
                        "updated_at": datetime.now(timezone.utc)
                    }
                }
            )
            return False, "Free trial limit reached (3/3 videos generated). Autopilot has been paused. Add your own API keys in Settings to continue."

        # Check if the new state hit the cap
        current_videos = updated.get("trial_quota", {}).get("videos_generated", 0)
        max_videos = updated.get("trial_quota", {}).get("max_videos", 3)
        if current_videos >= max_videos:
            db.workspaces.update_one(
                {"_id": ws["_id"]},
                {"$set": {"trial_quota.is_exhausted": True}}
            )

        return True, f"Trial video approved ({current_videos}/{max_videos} used)"

    except Exception as e:
        logger.error(f"Error checking trial quota: {e}")
        return False, f"Trial validation error: {str(e)}"


def can_workspace_generate_sync(workspace_id: str) -> Tuple[bool, str]:
    """Check if workspace is eligible to generate a video without consuming quota yet."""
    db = SyncMongoDB.get_db()
    try:
        ws = db.workspaces.find_one({"_id": ObjectId(workspace_id)}) if ObjectId.is_valid(workspace_id) else db.workspaces.find_one({"_id": workspace_id})
    except Exception:
        ws = db.workspaces.find_one({"_id": workspace_id})

    if not ws:
        return False, "Workspace not found."

    if ws.get("is_legacy_default", False):
        return True, "Legacy owner workspace"

    ws_id_str = str(ws["_id"])
    custom_ai_key = db.workspace_api_keys.find_one({
        "workspace_id": ws_id_str,
        "provider": "openrouter",
        "is_valid": True
    })
    if custom_ai_key:
        return True, "Using tenant's own API key (BYOK)"

    if is_platform_trial_disabled():
        return False, "Platform trials disabled platform-wide."

    tq = ws.get("trial_quota", {})
    if tq.get("is_exhausted", False):
        return False, "Trial exhausted (3/3 videos generated). Add your own API keys in Settings."

    v_gen = tq.get("videos_generated", 0)
    v_max = tq.get("max_videos", 3)
    if v_gen >= v_max:
        return False, f"Trial limit reached ({v_gen}/{v_max} videos). Add your own API keys in Settings."

    return True, f"Trial active ({v_gen}/{v_max} videos used)"


def refund_trial_quota_atomic_sync(workspace_id: str) -> bool:
    """Refund a previously acquired trial video quota if a pipeline was cancelled before rendering."""
    try:
        db = SyncMongoDB.get_db()
        ws = db.workspaces.find_one({"_id": ObjectId(workspace_id)}) if ObjectId.is_valid(workspace_id) else db.workspaces.find_one({"_id": workspace_id})
        if not ws or ws.get("is_legacy_default", False):
            return True
        db.workspaces.update_one(
            {"_id": ws["_id"], "trial_quota.videos_generated": {"$gt": 0}},
            {
                "$inc": {"trial_quota.videos_generated": -1},
                "$set": {"trial_quota.is_exhausted": False, "updated_at": datetime.now(timezone.utc)}
            }
        )
        return True
    except Exception as e:
        logger.error(f"Error refunding trial quota for workspace {workspace_id}: {e}")
        return False


