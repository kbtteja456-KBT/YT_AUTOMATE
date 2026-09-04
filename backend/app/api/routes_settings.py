"""System settings management endpoints."""

from fastapi import APIRouter
from typing import Any
from backend.app.models.settings import ChannelSettings

router = APIRouter(prefix="/settings", tags=["settings"])

_ACTIVE_SETTINGS = ChannelSettings()


@router.get("")
async def get_settings() -> dict[str, Any]:
    """Retrieve current channel and system configurations."""
    return _ACTIVE_SETTINGS.model_dump()


@router.put("")
async def update_settings(updated: ChannelSettings) -> dict[str, Any]:
    """Update runtime settings, preserving Zero-Cost constraints unless explicitly altered."""
    global _ACTIVE_SETTINGS
    _ACTIVE_SETTINGS = updated
    return {
        "status": "SUCCESS",
        "settings": _ACTIVE_SETTINGS.model_dump()
    }
