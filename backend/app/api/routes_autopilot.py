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

from fastapi import APIRouter, HTTPException, Header, Query, BackgroundTasks
from pydantic import BaseModel, Field

from backend.app.config import settings
from backend.app.core.logging import logger

router = APIRouter(prefix="/autopilot", tags=["autopilot"])


class TriggerSlotRequest(BaseModel):
    custom_topic: Optional[str] = Field(default=None, description="Optional custom topic for this Short")


@router.get("/status")
async def get_autopilot_status_endpoint() -> dict[str, Any]:
    """Retrieve live status of the autonomous publishing engine."""
    from backend.app.core.cron_scheduler import get_autopilot_status
    return get_autopilot_status()


@router.post("/start")
async def start_autopilot_endpoint() -> dict[str, Any]:
    """Resume autonomous publishing."""
    from backend.app.core.cron_scheduler import set_autopilot_enabled
    set_autopilot_enabled(True)
    return {"is_enabled": True, "message": "Autonomous publishing scheduler active."}


@router.post("/stop")
async def stop_autopilot_endpoint() -> dict[str, Any]:
    """Pause autonomous publishing."""
    from backend.app.core.cron_scheduler import set_autopilot_enabled
    set_autopilot_enabled(False)
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
