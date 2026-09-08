"""Autopilot HTTP control endpoints.

NOTE: run_autopilot_pipeline() and TOPIC_POOL have been permanently removed.
They were a disconnected legacy implementation (hardcoded quality_score=98.0,
generic tech topics, no PipelineOrchestrator, no IdeaAgent quiz pool).

The real pipeline is now always called via PipelineOrchestrator — both in
GitHub Actions (run_slot_cli.py → _build_orchestrator()) and in the in-process
FastAPI scheduler (cron_scheduler.py → execute_slot_pipeline()).

The /run-slot/{slot_index} endpoint below dispatches to the same real path.
"""

from typing import Any, Optional

from fastapi import APIRouter, HTTPException, Header, Query, BackgroundTasks, Depends
from pydantic import BaseModel, Field
from bson import ObjectId
from datetime import datetime, timezone

from backend.app.config import settings
from backend.app.core.logging import logger
from backend.app.core.db import SyncMongoDB
from backend.app.core.auth import get_optional_current_user
from backend.app.core.ledger import can_workspace_generate_sync

router = APIRouter(prefix="/autopilot", tags=["autopilot"])


class TriggerSlotRequest(BaseModel):
    custom_topic: Optional[str] = Field(default=None, description="Optional custom topic for this Short")


@router.get("/status")
async def get_autopilot_status_endpoint(
    user: Optional[dict[str, Any]] = Depends(get_optional_current_user)
) -> dict[str, Any]:
    """Retrieve live status of the autonomous publishing engine, scoped to tenant workspace if authenticated."""
    from backend.app.core.cron_scheduler import get_autopilot_status, get_slot_status_today
    import zoneinfo
    tz = zoneinfo.ZoneInfo(settings.timezone)
    now = datetime.now(tz)
    today_str = now.strftime("%Y-%m-%d")

    db = SyncMongoDB.get_db()
    ws = None
    if user and not user.get("is_owner"):
        target_ws_id = user.get("default_workspace_id")
        if target_ws_id:
            try:
                ws = db.workspaces.find_one({"_id": ObjectId(target_ws_id)})
            except Exception:
                ws = db.workspaces.find_one({"_id": target_ws_id})
        if not ws:
            user_id_str = str(user.get("_id") or user.get("id"))
            ws = db.workspaces.find_one({"owner_id": user_id_str})

    if ws:
        ws_id = str(ws["_id"])
        base_status = get_autopilot_status()
        base_status["is_enabled"] = ws.get("autopilot_enabled", False)
        base_status["workspace_id"] = ws_id
        base_status["workspace_name"] = ws.get("name")
        base_status["niche"] = ws.get("niche")
        base_status["trial_quota"] = ws.get("trial_quota")
        base_status["status_today"] = {
            "slot_1": get_slot_status_today(1, today_str, workspace_id=ws_id),
            "slot_2": get_slot_status_today(2, today_str, workspace_id=ws_id)
        }
        return base_status

    return get_autopilot_status()


@router.post("/start")
async def start_autopilot_endpoint(
    user: Optional[dict[str, Any]] = Depends(get_optional_current_user)
) -> dict[str, Any]:
    """Resume autonomous publishing for workspace or platform."""
    from backend.app.core.cron_scheduler import set_autopilot_enabled, start_autopilot_scheduler
    db = SyncMongoDB.get_db()

    ws = None
    if user and not user.get("is_owner"):
        target_ws_id = user.get("default_workspace_id")
        if target_ws_id:
            try:
                ws = db.workspaces.find_one({"_id": ObjectId(target_ws_id)})
            except Exception:
                ws = db.workspaces.find_one({"_id": target_ws_id})
        if not ws:
            user_id_str = str(user.get("_id") or user.get("id"))
            ws = db.workspaces.find_one({"owner_id": user_id_str})

        if ws:
            ws_id = str(ws["_id"])
            # Verify YouTube channel connected
            chan = db.youtube_channels.find_one({"workspace_id": ws_id, "is_active": True}) or db.youtube_channels.find_one({"workspace_id": ws_id})
            if not chan:
                raise HTTPException(
                    status_code=400,
                    detail="Please connect your YouTube channel in Settings before starting Autopilot."
                )
            # Verify trial quota or BYOK key
            can_gen, reason = can_workspace_generate_sync(ws_id)
            if not can_gen:
                raise HTTPException(status_code=403, detail=reason)

            db.workspaces.update_one(
                {"_id": ws["_id"]},
                {"$set": {"autopilot_enabled": True, "updated_at": datetime.now(timezone.utc)}}
            )
            # Ensure scheduler loop is running
            start_autopilot_scheduler()
            return {
                "is_enabled": True,
                "workspace_id": ws_id,
                "message": f"Autonomous publishing activated for {ws.get('name', 'your channel')}!"
            }

    # Owner / Global
    set_autopilot_enabled(True)
    db.workspaces.update_one(
        {"is_legacy_default": True},
        {"$set": {"autopilot_enabled": True, "updated_at": datetime.now(timezone.utc)}}
    )
    return {"is_enabled": True, "message": "Autonomous publishing scheduler active."}


@router.post("/stop")
async def stop_autopilot_endpoint(
    user: Optional[dict[str, Any]] = Depends(get_optional_current_user)
) -> dict[str, Any]:
    """Pause autonomous publishing for workspace or platform."""
    from backend.app.core.cron_scheduler import set_autopilot_enabled
    db = SyncMongoDB.get_db()

    ws = None
    if user and not user.get("is_owner"):
        target_ws_id = user.get("default_workspace_id")
        if target_ws_id:
            try:
                ws = db.workspaces.find_one({"_id": ObjectId(target_ws_id)})
            except Exception:
                ws = db.workspaces.find_one({"_id": target_ws_id})
        if not ws:
            user_id_str = str(user.get("_id") or user.get("id"))
            ws = db.workspaces.find_one({"owner_id": user_id_str})

        if ws:
            ws_id = str(ws["_id"])
            db.workspaces.update_one(
                {"_id": ws["_id"]},
                {"$set": {"autopilot_enabled": False, "updated_at": datetime.now(timezone.utc)}}
            )
            return {
                "is_enabled": False,
                "workspace_id": ws_id,
                "message": f"Autonomous publishing paused for {ws.get('name', 'your channel')}."
            }

    # Owner / Global
    set_autopilot_enabled(False)
    db.workspaces.update_one(
        {"is_legacy_default": True},
        {"$set": {"autopilot_enabled": False, "updated_at": datetime.now(timezone.utc)}}
    )
    return {"is_enabled": False, "message": "Autonomous publishing scheduler paused."}


@router.post("/run-slot/{slot_index}")
async def trigger_autopilot_slot(
    slot_index: int,
    background_tasks: BackgroundTasks,
    request: Optional[TriggerSlotRequest] = None,
    x_autopilot_secret: Optional[str] = Header(default=None),
    async_mode: bool = Query(default=True, description="Execute in background to avoid cloud gateway timeouts")
) -> dict[str, Any]:
    """Trigger morning (slot 1 = 07:00 IST) or evening (slot 2 = 18:00 IST) publishing immediately.

    Routes to the REAL PipelineOrchestrator via cron_scheduler.execute_slot_pipeline().
    """
    if slot_index not in (1, 2):
        raise HTTPException(status_code=400, detail="Slot index must be 1 (Morning 7 AM) or 2 (Evening 6 PM).")

    if settings.autopilot_cron_secret:
        if x_autopilot_secret != settings.autopilot_cron_secret:
            raise HTTPException(status_code=401, detail="Invalid x-autopilot-secret header.")

    custom_topic = request.custom_topic if request else None
    from backend.app.core.cron_scheduler import run_slot_with_lock

    if async_mode:
        background_tasks.add_task(run_slot_with_lock, slot_index=slot_index, custom_topic=custom_topic)
        return {
            "status": "QUEUED",
            "slot_index": slot_index,
            "message": f"Slot {slot_index} execution launched asynchronously. Check /api/autopilot/status for live progress."
        }

    result = await run_slot_with_lock(slot_index=slot_index, custom_topic=custom_topic)
    return result


@router.get("/topics")
async def list_autopilot_topics() -> list[dict[str, Any]]:
    """Preview the IdeaAgent's Python quiz concept pool (38 concepts with anti-repetition memory)."""
    try:
        from backend.app.agents.idea import IdeaAgent
        agent = IdeaAgent(ai_provider=None)  # type: ignore[arg-type]
        concepts = getattr(agent, "CONCEPT_POOL", [])
        return [{"concept": c, "type": "python_quiz"} for c in concepts]
    except Exception as e:
        logger.warning(f"Could not load concept pool: {e}")
        return []
