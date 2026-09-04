"""Calendar and scheduled slots view endpoints."""

from fastapi import APIRouter
from typing import Any
from datetime import datetime, timezone, timedelta

router = APIRouter(prefix="/calendar", tags=["calendar"])


@router.get("")
async def get_calendar_slots() -> dict[str, Any]:
    """Retrieve today and upcoming scheduled slots from database state."""
    now = datetime.now(timezone.utc)
    # Default scheduled slots at 07:00 and 18:00
    today_slot1 = now.replace(hour=1, minute=30, second=0, microsecond=0)  # 07:00 IST in UTC is 01:30 UTC
    today_slot2 = now.replace(hour=12, minute=30, second=0, microsecond=0) # 18:00 IST in UTC is 12:30 UTC

    return {
        "timezone": "Asia/Kolkata",
        "slots_today": [
            {
                "slot_index": 1,
                "publish_time_local": "07:00",
                "status": "SCHEDULED" if now < today_slot1 else "MISSED",
                "video_id": None
            },
            {
                "slot_index": 2,
                "publish_time_local": "18:00",
                "status": "SCHEDULED" if now < today_slot2 else "MISSED",
                "video_id": None
            }
        ],
        "history": []
    }
