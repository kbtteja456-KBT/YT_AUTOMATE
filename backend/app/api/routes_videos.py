"""Video generation, status, and listing endpoints backed by MongoDB."""

import threading
import time

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field
from typing import Any, Optional
from datetime import datetime, timezone

from backend.app.celery_app.tasks import run_pipeline_task
from backend.app.core.db import SyncMongoDB
from backend.app.core.logging import logger
from backend.app.core.security import compute_content_hash
from backend.app.models.job import JobState, PublishingJob

router = APIRouter(prefix="/videos", tags=["videos"])


class GenerateVideoRequest(BaseModel):
    topic: Optional[str] = Field(default=None, description="Optional custom topic")
    target_duration_sec: float = Field(default=45.0, ge=30.0, le=60.0)
    slot_index: int = Field(default=1, ge=1, le=2)


def _serialize_doc(doc: dict[str, Any]) -> dict[str, Any]:
    """Convert BSON-style docs to JSON-serializable dictionaries with web URLs."""
    payload = dict(doc)
    if "_id" in payload:
        payload["id"] = str(payload.pop("_id"))

    # Map filesystem paths to web accessible /media URLs
    if payload.get("thumbnail_path"):
        norm = str(payload["thumbnail_path"]).replace("\\", "/")
        if "media_storage/" in norm:
            rel = norm.split("media_storage/")[-1]
            payload["thumbnail_url"] = f"/media/{rel}"
        else:
            payload["thumbnail_url"] = payload["thumbnail_path"]
    else:
        payload["thumbnail_url"] = None

    if payload.get("file_path"):
        norm = str(payload["file_path"]).replace("\\", "/")
        if "media_storage/" in norm:
            rel = norm.split("media_storage/")[-1]
            payload["video_url"] = f"/media/{rel}"
        else:
            payload["video_url"] = payload["file_path"]
    else:
        payload["video_url"] = None

    return payload


def _dispatch_pipeline_job(job_id: str, topic: Optional[str] = None, slot_index: int = 1) -> None:
    """Dispatch the real autopilot pipeline asynchronously in a background thread."""
    import asyncio
    from backend.app.api.routes_autopilot import run_autopilot_pipeline
    from backend.app.models.job import JobState

    db = SyncMongoDB.get_db()
    db.publishing_jobs.update_one(
        {"_id": job_id},
        {"$set": {"state": JobState.RENDERING.value, "updated_at": datetime.now(timezone.utc)}}
    )

    try:
        res = asyncio.run(run_autopilot_pipeline(slot_index=slot_index, custom_topic=topic))
        db.publishing_jobs.update_one(
            {"_id": job_id},
            {"$set": {"state": JobState.PUBLISHED.value, "details": res, "updated_at": datetime.now(timezone.utc)}}
        )
        logger.info(f"Manual video generation job {job_id} completed successfully!")
    except Exception as exc:
        logger.exception(f"Manual video generation failed for job {job_id}: {exc}")
        db.publishing_jobs.update_one(
            {"_id": job_id},
            {"$set": {"state": JobState.FAILED.value, "error_message": str(exc), "updated_at": datetime.now(timezone.utc)}}
        )


@router.post("/generate")
async def trigger_video_generation(request: GenerateVideoRequest) -> dict[str, Any]:
    """Manually queue a real video generation pipeline job in MongoDB."""
    db = SyncMongoDB.get_db()
    now = datetime.now(timezone.utc)
    topic = request.topic or "Autonomous Tech Discovery"
    job_id = f"job_{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S%f')}_{request.slot_index}"
    idempotency_key = compute_content_hash(f"manual_{topic}_{job_id}")

    existing = db.publishing_jobs.find_one({"idempotency_key": idempotency_key})
    if existing:
        return {
            "status": "QUEUED",
            "job_id": str(existing["_id"]),
            "idempotency_key": idempotency_key,
            "message": "Video generation job already exists."
        }

    job = PublishingJob(
        id=job_id,
        slot_index=request.slot_index,
        scheduled_at=now,
        state=JobState.CREATED,
        idempotency_key=idempotency_key,
        topic=topic,
        niche="AI & Productivity",
        is_buffered=False,
        created_at=now,
        updated_at=now,
    )
    job_doc = job.to_mongo_dict()
    job_doc["_id"] = job_id
    db.publishing_jobs.insert_one(job_doc)

    threading.Thread(target=_dispatch_pipeline_job, args=(job_id, request.topic, request.slot_index), daemon=True).start()
    queue_message = "Video generation job created and queued."

    return {
        "status": "QUEUED",
        "job_id": job_id,
        "idempotency_key": idempotency_key,
        "message": queue_message
    }


@router.get("")
async def list_videos(limit: int = Query(default=20, ge=1, le=100)) -> list[dict[str, Any]]:
    """List recent rendered and published videos from MongoDB."""
    db = SyncMongoDB.get_db()
    cursor = db.videos.find({}).sort("created_at", -1).limit(limit)
    return [_serialize_doc(v) for v in cursor]


@router.get("/{video_id}")
async def get_video(video_id: str) -> dict[str, Any]:
    """Retrieve details for a specific video."""
    db = SyncMongoDB.get_db()
    doc = db.videos.find_one({"_id": video_id})
    if not doc:
        from bson import ObjectId
        if ObjectId.is_valid(video_id):
            doc = db.videos.find_one({"_id": ObjectId(video_id)})
    if not doc:
        raise HTTPException(status_code=404, detail="Video not found")
    return _serialize_doc(doc)


@router.get("/{job_id}/status")
async def get_job_status(job_id: str) -> dict[str, Any]:
    """Check live status of an in-flight video pipeline job."""
    db = SyncMongoDB.get_db()
    doc = db.publishing_jobs.find_one({"_id": job_id})
    if not doc:
        from bson import ObjectId
        if ObjectId.is_valid(job_id):
            doc = db.publishing_jobs.find_one({"_id": ObjectId(job_id)})
    if not doc:
        raise HTTPException(status_code=404, detail="Job not found")
    return _serialize_doc(doc)
