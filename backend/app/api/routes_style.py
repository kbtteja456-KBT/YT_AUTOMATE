"""Reference video style analysis and profile endpoints."""

from fastapi import APIRouter, UploadFile, File, HTTPException
from typing import Any
from backend.app.models.style_profile import StyleProfile

router = APIRouter(prefix="/style", tags=["style"])

_ACTIVE_PROFILE = StyleProfile()


@router.get("/profile")
async def get_active_style_profile() -> dict[str, Any]:
    """Retrieve current reference video editing rhythm parameters."""
    return _ACTIVE_PROFILE.model_dump()


@router.post("/analyze")
async def analyze_reference_video(file: UploadFile = File(...)) -> dict[str, Any]:
    """Upload a reference vertical Short (~44s) to extract dual-segment pacing."""
    if not file.filename.lower().endswith((".mp4", ".mov", ".mkv")):
        raise HTTPException(status_code=400, detail="Only video files (.mp4, .mov, .mkv) supported.")

    # In Phase 2 skeleton, we confirm upload acceptance; full OpenCV/FFprobe analysis implemented in Agent phase
    return {
        "status": "ANALYSIS_QUEUED",
        "filename": file.filename,
        "message": "Reference video uploaded for pacing analysis."
    }
