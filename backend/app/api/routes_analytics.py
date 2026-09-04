"""YouTube channel analytics endpoints."""

from fastapi import APIRouter
from typing import Any

router = APIRouter(prefix="/analytics", tags=["analytics"])


@router.get("")
async def get_analytics() -> dict[str, Any]:
    """Return genuine YouTube channel analytics or NOT AVAILABLE indicators."""
    # When channel is not yet connected or API hasn't synced, report NOT AVAILABLE
    return {
        "channel_connected": False,
        "metrics": {
            "views_28d": "NOT AVAILABLE",
            "watch_time_hours_28d": "NOT AVAILABLE",
            "subscribers_net_28d": "NOT AVAILABLE",
            "average_percentage_viewed": "NOT AVAILABLE",
            "impressions_ctr": "NOT AVAILABLE"
        },
        "top_performing_shorts": [],
        "audience_retention_curve": "NOT AVAILABLE",
        "last_synced": None
    }
