"""Activity feed routes for live pipeline audit stream."""

from fastapi import APIRouter
from typing import Any
from datetime import datetime, timezone

router = APIRouter(prefix="/activity", tags=["activity"])

# Initial in-memory event buffer; linked to Mongo in Phase 3
_RECENT_EVENTS: list[dict[str, Any]] = [
    {
        "id": "act_init_1",
        "event_type": "SYSTEM_STARTUP",
        "level": "INFO",
        "agent_name": "SystemReconciler",
        "message": "AI YouTube Shorts Autopilot daemon started. Zero-Cost Mode active.",
        "timestamp": datetime.now(timezone.utc).isoformat()
    }
]


@router.get("")
async def get_activity(limit: int = 50) -> list[dict[str, Any]]:
    """Fetch timestamped agent activity events."""
    return _RECENT_EVENTS[:limit]


def emit_activity(event: dict[str, Any]) -> None:
    """Internal helper to append genuine event to feed."""
    if "timestamp" not in event:
        event["timestamp"] = datetime.now(timezone.utc).isoformat()
    _RECENT_EVENTS.insert(0, event)
    if len(_RECENT_EVENTS) > 500:
        _RECENT_EVENTS.pop()
