"""Platform owner administration endpoints for cost monitoring, usage ledger analytics,
and tenant quota enforcement controls.
"""

import os
from datetime import datetime, timezone, timedelta
from typing import Any, Optional
from bson import ObjectId
from fastapi import APIRouter, HTTPException, Depends, status
from pydantic import BaseModel

from backend.app.core.db import AsyncMongoDB
from backend.app.core.auth import get_current_user
from backend.app.core.ledger import is_platform_trial_disabled

router = APIRouter(prefix="/admin", tags=["admin"])


def verify_owner(user: dict[str, Any] = Depends(get_current_user)) -> dict[str, Any]:
    """Dependency verifying that caller is the platform owner."""
    if not user.get("is_owner", False):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access restricted to platform owner."
        )
    return user


@router.get("/overview")
async def get_admin_overview(owner: dict[str, Any] = Depends(verify_owner)) -> dict[str, Any]:
    """Summary of platform health, total workspaces, videos published, and trial status."""
    db = AsyncMongoDB.get_db()

    total_users = await db.users.count_documents({})
    total_workspaces = await db.workspaces.count_documents({})
    total_videos = await db.videos.count_documents({})

    # Calculate total platform cost incurred in ledger
    pipeline = [
        {"$match": {"used_platform_key": True}},
        {"$group": {"_id": None, "total_cost": {"$sum": "$estimated_cost_usd"}, "total_calls": {"$sum": 1}}}
    ]
    cursor = db.usage_ledger.aggregate(pipeline)
    cost_summary = await cursor.to_list(length=1)
    platform_cost = cost_summary[0]["total_cost"] if cost_summary else 0.0
    platform_calls = cost_summary[0]["total_calls"] if cost_summary else 0

    return {
        "total_users": total_users,
        "total_workspaces": total_workspaces,
        "total_videos": total_videos,
        "platform_key_total_cost_usd": round(platform_cost, 4),
        "platform_key_total_calls": platform_calls,
        "kill_switch_active": is_platform_trial_disabled(),
    }


@router.get("/usage")
async def get_admin_usage_ledger(
    limit: int = 50,
    owner: dict[str, Any] = Depends(verify_owner)
) -> dict[str, Any]:
    """Detailed breakdown of costs per workspace, top spenders, and recent ledger entries."""
    db = AsyncMongoDB.get_db()

    # Aggregate by workspace
    pipeline = [
        {
            "$group": {
                "_id": "$workspace_id",
                "total_cost": {"$sum": "$estimated_cost_usd"},
                "total_units": {"$sum": "$units"},
                "platform_calls": {"$sum": {"$cond": ["$used_platform_key", 1, 0]}},
                "byok_calls": {"$sum": {"$cond": ["$used_platform_key", 0, 1]}},
                "last_active": {"$max": "$timestamp"}
            }
        },
        {"$sort": {"total_cost": -1}},
        {"$limit": 20}
    ]
    cursor = db.usage_ledger.aggregate(pipeline)
    spenders = await cursor.to_list(length=20)

    # Enrich with workspace names
    spenders_enriched = []
    for s in spenders:
        ws_id = s["_id"]
        ws_name = "Unknown Workspace"
        is_legacy = False
        try:
            ws = await db.workspaces.find_one({"_id": ObjectId(ws_id)})
            if ws:
                ws_name = ws.get("name", ws_name)
                is_legacy = ws.get("is_legacy_default", False)
        except Exception:
            pass

        spenders_enriched.append({
            "workspace_id": ws_id,
            "workspace_name": ws_name,
            "is_legacy": is_legacy,
            "total_cost_usd": round(s.get("total_cost", 0.0), 4),
            "total_units": s.get("total_units", 0),
            "platform_calls": s.get("platform_calls", 0),
            "byok_calls": s.get("byok_calls", 0),
            "last_active": s.get("last_active"),
        })

    # Recent ledger logs
    recent_cursor = db.usage_ledger.find().sort("timestamp", -1).limit(limit)
    recent_logs = await recent_cursor.to_list(length=limit)
    for l in recent_logs:
        l["id"] = str(l["_id"])
        del l["_id"]

    return {
        "top_spenders": spenders_enriched,
        "recent_ledger_records": recent_logs,
    }


class ToggleWorkspaceStatusRequest(BaseModel):
    workspace_id: str
    autopilot_enabled: bool


@router.post("/toggle-workspace")
async def toggle_workspace(
    req: ToggleWorkspaceStatusRequest,
    owner: dict[str, Any] = Depends(verify_owner)
) -> dict[str, Any]:
    """Owner override to pause or resume an individual tenant's autopilot."""
    db = AsyncMongoDB.get_db()
    try:
        oid = ObjectId(req.workspace_id)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid workspace ID")

    res = await db.workspaces.update_one(
        {"_id": oid},
        {"$set": {"autopilot_enabled": req.autopilot_enabled, "updated_at": datetime.now(timezone.utc)}}
    )
    if res.matched_count == 0:
        raise HTTPException(status_code=404, detail="Workspace not found.")

    action = "resumed" if req.autopilot_enabled else "paused"
    return {"status": "SUCCESS", "message": f"Workspace {req.workspace_id} autopilot {action}."}
