"""Video generation, status, and listing endpoints backed by MongoDB."""

import threading
import time

from fastapi import APIRouter, HTTPException, Query, Depends
from pydantic import BaseModel, Field
from typing import Any, Optional
from datetime import datetime, timezone
from bson import ObjectId

from backend.app.celery_app.tasks import run_pipeline_task
from backend.app.core.db import SyncMongoDB
from backend.app.core.logging import logger
from backend.app.core.security import compute_content_hash
from backend.app.core.auth import get_optional_current_user
from backend.app.models.job import JobState, PublishingJob

router = APIRouter(prefix="/videos", tags=["videos"])


class GenerateVideoRequest(BaseModel):
    topic: Optional[str] = Field(default=None, description="Optional custom topic or title")
    prompt: Optional[str] = Field(default=None, description="User prompt, text idea, concept, or instructions")
    content_format: Optional[str] = Field(default="auto", description="Format: auto, documentary, quiz_card, quote_card, trivia_quiz")
    target_duration_sec: float = Field(default=45.0, ge=30.0, le=60.0)
    slot_index: int = Field(default=1, ge=1, le=2)
    auto_publish: bool = Field(default=False, description="Post directly to connected YouTube channel once generated")


class UpdateVideoRequest(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    tags: Optional[list[str]] = None


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


def _dispatch_pipeline_job(
    job_id: str,
    topic: Optional[str],
    slot_index: int,
    workspace_id: Optional[str],
    auto_publish: bool,
    niche: Optional[str] = None,
    prompt: Optional[str] = None,
    content_format: Optional[str] = "auto",
    target_duration_sec: Optional[float] = None
) -> None:
    """Dispatch the real PipelineOrchestrator in a background thread with workspace niche awareness."""
    import asyncio
    from backend.app.celery_app.tasks import _build_orchestrator
    from backend.app.core.repositories import JobRepository, VideoRepository
    from backend.app.models.job import JobState

    db = SyncMongoDB.get_db()
    workspace_niche = niche
    if not workspace_niche and workspace_id:
        try:
            ws_obj = db.workspaces.find_one({"_id": ObjectId(workspace_id)}) if ObjectId.is_valid(workspace_id) else db.workspaces.find_one({"_id": workspace_id})
            if ws_obj:
                workspace_niche = ws_obj.get("niche") or ws_obj.get("settings", {}).get("niche")
        except Exception:
            pass
    if not workspace_niche:
        job_doc = db.publishing_jobs.find_one({"_id": job_id})
        if job_doc:
            workspace_niche = job_doc.get("niche")
    if not workspace_niche:
        workspace_niche = "Python Programming"

    db.publishing_jobs.update_one(
        {"_id": job_id},
        {"$set": {"state": JobState.RENDERING.value, "niche": workspace_niche, "updated_at": datetime.now(timezone.utc)}}
    )

    try:
        async def _run():
            orchestrator = _build_orchestrator(db, workspace_id=workspace_id)
            orchestrator.job_repo = JobRepository(db)
            orchestrator.video_repo = VideoRepository(db)
            return await orchestrator.execute_job(
                job_id=job_id,
                niche=workspace_niche,
                custom_topic=topic,
                publish_immediately=auto_publish,
                slot_index=slot_index,
                custom_prompt=prompt,
                content_format=content_format,
                target_duration_sec=target_duration_sec
            )

        res = asyncio.run(_run())
        final_state = JobState.PUBLISHED.value if res.get("status") == "PUBLISHED" else JobState.READY.value
        db.publishing_jobs.update_one(
            {"_id": job_id},
            {"$set": {"state": final_state, "details": res, "updated_at": datetime.now(timezone.utc)}}
        )
        logger.info(f"Manual video generation job {job_id} completed — state {final_state}.")
    except Exception as exc:
        logger.exception(f"Manual video generation failed for job {job_id}: {exc}")
        db.publishing_jobs.update_one(
            {"_id": job_id},
            {"$set": {"state": JobState.FAILED.value, "error_message": str(exc), "updated_at": datetime.now(timezone.utc)}}
        )




@router.post("/generate")
async def trigger_video_generation(
    request: GenerateVideoRequest,
    user: Optional[dict[str, Any]] = Depends(get_optional_current_user)
) -> dict[str, Any]:
    """Manually queue a real video generation pipeline job in MongoDB scoped to caller's workspace."""
    db = SyncMongoDB.get_db()
    now = datetime.now(timezone.utc)
    topic = request.topic or "Autonomous Tech Discovery"
    job_id = f"job_{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S%f')}_{request.slot_index}"
    idempotency_key = compute_content_hash(f"manual_{topic}_{job_id}")

    # Resolve workspace_id from authenticated user
    workspace_id = None
    if user:
        if not user.get("is_owner"):
            target_ws_id = user.get("default_workspace_id")
            ws = None
            if target_ws_id:
                try:
                    ws = db.workspaces.find_one({"_id": ObjectId(target_ws_id)})
                except Exception:
                    ws = db.workspaces.find_one({"_id": target_ws_id})
            if not ws:
                user_id_str = str(user.get("_id") or user.get("id"))
                ws = db.workspaces.find_one({"owner_id": user_id_str})
            if ws:
                workspace_id = str(ws["_id"])
        else:
            legacy_ws = db.workspaces.find_one({"is_legacy_default": True}) or db.workspaces.find_one()
            if legacy_ws:
                workspace_id = str(legacy_ws["_id"])

    # Fallback to legacy default workspace if anonymous caller
    if not workspace_id:
        legacy_ws = db.workspaces.find_one({"is_legacy_default": True})
        if legacy_ws:
            workspace_id = str(legacy_ws["_id"])

    # Resolve niche from workspace if set
    workspace_niche = "AI & Productivity"
    ws_obj = None
    if workspace_id:
        try:
            ws_obj = db.workspaces.find_one({"_id": ObjectId(workspace_id)}) if ObjectId.is_valid(workspace_id) else db.workspaces.find_one({"_id": workspace_id})
            if ws_obj:
                workspace_niche = ws_obj.get("niche") or ws_obj.get("settings", {}).get("niche", "AI & Productivity")
        except Exception:
            pass

    # Extract user custom prompt, duration, format from settings if not passed explicitly in request
    effective_prompt = request.prompt
    if not effective_prompt and ws_obj:
        effective_prompt = ws_obj.get("custom_content_prompt") or ws_obj.get("settings", {}).get("custom_content_prompt")

    effective_format = request.content_format or "auto"
    if (not effective_format or effective_format == "auto") and ws_obj:
        saved_fmt = ws_obj.get("preferred_format") or ws_obj.get("settings", {}).get("preferred_format")
        if saved_fmt:
            effective_format = saved_fmt

    effective_duration = getattr(request, "target_duration_sec", None)
    if (not effective_duration or effective_duration == 45.0) and ws_obj:
        saved_dur = ws_obj.get("default_duration_sec") or ws_obj.get("settings", {}).get("default_duration_sec")
        if saved_dur:
            try:
                effective_duration = float(saved_dur)
            except Exception:
                pass
    if not effective_duration:
        effective_duration = 45.0

    topic = request.topic or (effective_prompt[:60] if effective_prompt else workspace_niche)

    # Check if this workspace has an active connected YouTube channel
    has_yt = False
    if workspace_id:
        chan = db.youtube_channels.find_one({"workspace_id": workspace_id, "is_active": True}) or db.youtube_channels.find_one({"workspace_id": workspace_id})
        if chan:
            tok = db.oauth_tokens.find_one({"workspace_id": workspace_id}) or db.oauth_tokens.find_one({"channel_id": chan["channel_id"]})
            has_yt = bool(tok)

    should_auto_publish = request.auto_publish and has_yt

    # Enforce 3-video trial quota for non-owner tenants (quota is only consumed after YouTube upload)
    if workspace_id:
        from backend.app.core.ledger import can_workspace_generate_sync
        allowed, reason = can_workspace_generate_sync(workspace_id)
        if not allowed:
            raise HTTPException(status_code=403, detail=reason)

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
        niche=workspace_niche,
        is_buffered=False,
        created_at=now,
        updated_at=now,
    )
    job_doc = job.to_mongo_dict()
    job_doc["_id"] = job_id
    if workspace_id:
        job_doc["workspace_id"] = workspace_id
    if user:
        job_doc["user_id"] = str(user.get("_id") or user.get("id"))

    db.publishing_jobs.insert_one(job_doc)

    threading.Thread(
        target=_dispatch_pipeline_job,
        args=(job_id, request.topic, request.slot_index, workspace_id, should_auto_publish, workspace_niche, effective_prompt, effective_format, effective_duration),
        daemon=True
    ).start()

    pub_note = " and will auto-publish to your connected YouTube channel" if should_auto_publish else " (ready for preview and review)"
    queue_message = f"Video generation job created and queued{pub_note}."

    return {
        "status": "QUEUED",
        "job_id": job_id,
        "workspace_id": workspace_id,
        "auto_publish": should_auto_publish,
        "idempotency_key": idempotency_key,
        "message": queue_message
    }


@router.put("/{video_id}")
async def update_video_details(
    video_id: str,
    payload: UpdateVideoRequest,
    user: Optional[dict[str, Any]] = Depends(get_optional_current_user)
) -> dict[str, Any]:
    """Allow updating video metadata (title, description, tags) before or after publishing."""
    db = SyncMongoDB.get_db()
    query = {"_id": ObjectId(video_id)} if ObjectId.is_valid(video_id) else {"_id": video_id}
    video_doc = db.videos.find_one(query)
    if not video_doc:
        video_doc = db.videos.find_one({"_id": video_id})
    if not video_doc:
        raise HTTPException(status_code=404, detail="Video not found")

    update_fields: dict[str, Any] = {"updated_at": datetime.now(timezone.utc)}
    if payload.title is not None:
        update_fields["title"] = payload.title.strip()
    if payload.description is not None:
        update_fields["description"] = payload.description.strip()
    if payload.tags is not None:
        update_fields["tags"] = payload.tags

    db.videos.update_one(query, {"$set": update_fields})
    updated = db.videos.find_one(query)
    return _serialize_doc(updated)


@router.post("/{video_id}/publish")
async def publish_video_now(
    video_id: str,
    user: Optional[dict[str, Any]] = Depends(get_optional_current_user)
) -> dict[str, Any]:
    """Manually publish an existing rendered video to the workspace's connected YouTube channel."""
    db = SyncMongoDB.get_db()
    query = {"_id": ObjectId(video_id)} if ObjectId.is_valid(video_id) else {"_id": video_id}
    video_doc = db.videos.find_one(query)
    if not video_doc:
        video_doc = db.videos.find_one({"_id": video_id})
    if not video_doc:
        raise HTTPException(status_code=404, detail="Video not found")

    if video_doc.get("status") == "PUBLISHED" and video_doc.get("youtube_video_id"):
        return {
            "status": "ALREADY_PUBLISHED",
            "youtube_video_id": video_doc.get("youtube_video_id"),
            "youtube_url": video_doc.get("youtube_url")
        }

    ws_id = video_doc.get("workspace_id")
    if user and not ws_id:
        target_ws_id = user.get("default_workspace_id")
        if target_ws_id:
            ws_id = str(target_ws_id)

    from backend.app.celery_app.tasks import _get_authenticated_youtube_provider
    from backend.app.agents.youtube import YouTubeAgent
    from backend.app.models.thumbnail import ThumbnailCard, ThumbnailSpec

    youtube_provider = _get_authenticated_youtube_provider(db, workspace_id=ws_id)
    if not getattr(youtube_provider, "credentials", None):
        raise HTTPException(
            status_code=400,
            detail="No connected YouTube channel found for this workspace. Please connect your YouTube account in the dashboard."
        )

    youtube_agent = YouTubeAgent(youtube_provider=youtube_provider)

    thumb_card = None
    if video_doc.get("thumbnail_path"):
        thumb_card = ThumbnailCard(
            file_path=str(video_doc["thumbnail_path"]),
            file_hash="thumb",
            spec=ThumbnailSpec(source_frame_timestamp=0.0, overlay_text="")
        )

    import asyncio
    try:
        upload_res = asyncio.run(youtube_agent.publish_short(
            video_filepath=str(video_doc["file_path"]),
            title=str(video_doc.get("title", "Python Quiz #Shorts")),
            description=str(video_doc.get("description", "")),
            tags=list(video_doc.get("tags") or ["Shorts", "Python"]),
            thumbnail=thumb_card,
            privacy_status="public"
        ))

        now_utc = datetime.now(timezone.utc)
        db.videos.update_one(
            {"_id": video_doc["_id"]},
            {
                "$set": {
                    "status": "PUBLISHED",
                    "youtube_video_id": upload_res.get("youtube_video_id"),
                    "youtube_url": upload_res.get("youtube_url"),
                    "youtube_published_at": now_utc,
                    "updated_at": now_utc
                }
            }
        )

        job_id = video_doc.get("job_id")
        if job_id:
            from bson import ObjectId
            j_q = {"_id": ObjectId(job_id)} if ObjectId.is_valid(job_id) else {"_id": job_id}
            db.publishing_jobs.update_one(
                j_q,
                {
                    "$set": {
                        "state": JobState.PUBLISHED.value,
                        "youtube_video_id": upload_res.get("youtube_video_id"),
                        "youtube_url": upload_res.get("youtube_url"),
                        "published_at": now_utc,
                        "updated_at": now_utc
                    }
                }
            )

        return {
            "status": "PUBLISHED",
            "youtube_video_id": upload_res.get("youtube_video_id"),
            "youtube_url": upload_res.get("youtube_url"),
            "message": "Video successfully uploaded and published to your YouTube channel!"
        }
    except Exception as e:
        logger.error(f"Manual video publishing failed: {e}")
        raise HTTPException(status_code=500, detail=f"YouTube upload failed: {str(e)}")


@router.get("")
async def list_videos(
    limit: int = Query(default=20, ge=1, le=100),
    user: Optional[dict[str, Any]] = Depends(get_optional_current_user)
) -> list[dict[str, Any]]:
    """List recent rendered and published videos from MongoDB, strictly isolated to caller workspace."""
    db = SyncMongoDB.get_db()

    query: dict[str, Any] = {}
    if user:
        if not user.get("is_owner"):
            # Tenant workspace isolation
            target_ws_id = user.get("default_workspace_id")
            ws = None
            if target_ws_id:
                try:
                    ws = db.workspaces.find_one({"_id": ObjectId(target_ws_id)})
                except Exception:
                    ws = db.workspaces.find_one({"_id": target_ws_id})
            if not ws:
                user_id_str = str(user.get("_id") or user.get("id"))
                ws = db.workspaces.find_one({"owner_id": user_id_str})

            if ws:
                query["workspace_id"] = str(ws["_id"])
            else:
                return []
        else:
            # Owner: owner's workspace videos + unassigned legacy videos
            legacy_ws = db.workspaces.find_one({"is_legacy_default": True})
            ws_id = str(legacy_ws["_id"]) if legacy_ws else None
            if ws_id:
                query["$or"] = [
                    {"workspace_id": ws_id},
                    {"workspace_id": None},
                    {"workspace_id": {"$exists": False}}
                ]
    else:
        # Anonymous legacy caller (e.g. run_slot_cli.py / cron)
        legacy_ws = db.workspaces.find_one({"is_legacy_default": True})
        ws_id = str(legacy_ws["_id"]) if legacy_ws else None
        if ws_id:
            query["$or"] = [
                {"workspace_id": ws_id},
                {"workspace_id": None},
                {"workspace_id": {"$exists": False}}
            ]

    cursor = db.videos.find(query).sort("created_at", -1).limit(limit)
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


@router.delete("/{video_id}")
async def delete_video(video_id: str) -> dict[str, Any]:
    """Delete a video from MongoDB database and remove local rendered files."""
    import os
    from bson import ObjectId

    db = SyncMongoDB.get_db()

    # Find the video doc by ObjectId or string ID
    query = {"_id": ObjectId(video_id)} if ObjectId.is_valid(video_id) else {"_id": video_id}
    doc = db.videos.find_one(query)
    if not doc:
        # Fallback check with string id
        doc = db.videos.find_one({"_id": video_id})

    if not doc:
        raise HTTPException(status_code=404, detail="Video not found")

    deleted_files = []
    # Safely remove rendered video and thumbnail from disk if they exist locally
    for path_key in ("file_path", "thumbnail_path"):
        path_val = doc.get(path_key)
        if path_val and isinstance(path_val, str) and not path_val.startswith("http"):
            try:
                abs_p = os.path.abspath(path_val)
                if os.path.isfile(abs_p):
                    os.remove(abs_p)
                    deleted_files.append(abs_p)
                    logger.info(f"Deleted local video file: {abs_p}")
            except Exception as fe:
                logger.warning(f"Could not delete local file {path_val}: {fe}")

    # Delete video record from MongoDB
    db.videos.delete_one({"_id": doc["_id"]})

    # Clean up linked publishing job if present
    job_id = doc.get("job_id")
    if job_id:
        try:
            job_query = {"_id": ObjectId(job_id)} if ObjectId.is_valid(job_id) else {"_id": job_id}
            db.publishing_jobs.delete_one(job_query)
        except Exception:
            pass

    logger.info(f"Video {video_id} permanently deleted from database.")
    return {
        "status": "DELETED",
        "video_id": video_id,
        "title": doc.get("title", ""),
        "deleted_files": deleted_files
    }
