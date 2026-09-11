"""System settings management endpoints backed by MongoDB per workspace."""

from fastapi import APIRouter, Depends
from typing import Any, Optional
from bson import ObjectId
from backend.app.models.settings import ChannelSettings
from backend.app.core.auth import get_optional_current_user
from backend.app.core.db import SyncMongoDB

router = APIRouter(prefix="/settings", tags=["settings"])

_DEFAULT_SETTINGS = ChannelSettings()


@router.get("")
async def get_settings(user: Optional[dict[str, Any]] = Depends(get_optional_current_user)) -> dict[str, Any]:
    """Retrieve current channel and system configurations for active workspace."""
    db = SyncMongoDB.get_db()
    ws = None
    if user:
        target_ws_id = user.get("default_workspace_id")
        if target_ws_id:
            try:
                ws = db.workspaces.find_one({"_id": ObjectId(target_ws_id)})
            except Exception:
                ws = db.workspaces.find_one({"_id": target_ws_id})
        if not ws:
            user_id_str = str(user.get("_id") or user.get("id"))
            ws = db.workspaces.find_one({"owner_id": user_id_str})

    if not ws:
        ws = db.workspaces.find_one({"is_legacy_default": True}) or db.workspaces.find_one()

    if ws and "settings" in ws:
        return ws["settings"]
    elif ws:
        settings_dict = _DEFAULT_SETTINGS.model_dump()
        settings_dict["niche"] = ws.get("niche", settings_dict["niche"])
        settings_dict["autopilot_enabled"] = ws.get("autopilot_enabled", False)
        return settings_dict

    return _DEFAULT_SETTINGS.model_dump()


@router.put("")
async def update_settings(
    updated: ChannelSettings,
    user: Optional[dict[str, Any]] = Depends(get_optional_current_user)
) -> dict[str, Any]:
    """Update runtime settings for active workspace in MongoDB."""
    db = SyncMongoDB.get_db()
    ws = None
    if user:
        target_ws_id = user.get("default_workspace_id")
        if target_ws_id:
            try:
                ws = db.workspaces.find_one({"_id": ObjectId(target_ws_id)})
            except Exception:
                ws = db.workspaces.find_one({"_id": target_ws_id})
        if not ws:
            user_id_str = str(user.get("_id") or user.get("id"))
            ws = db.workspaces.find_one({"owner_id": user_id_str})

    if not ws:
        ws = db.workspaces.find_one({"is_legacy_default": True}) or db.workspaces.find_one()

    dump = updated.model_dump()
    if ws:
        db.workspaces.update_one(
            {"_id": ws["_id"]},
            {"$set": {
                "niche": updated.niche,
                "autopilot_enabled": updated.autopilot_enabled,
                "custom_content_prompt": updated.custom_content_prompt,
                "default_duration_sec": updated.default_duration_sec,
                "preferred_format": updated.preferred_format,
                "settings": dump
            }}
        )

    return {
        "status": "SUCCESS",
        "settings": dump
    }
