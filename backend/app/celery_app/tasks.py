"""Celery background tasks for video pipeline execution and scheduling."""

import asyncio
import threading
import time
from datetime import datetime, timezone
from typing import Any, Optional
from celery import shared_task

from backend.app.agents.caption import CaptionAgent
from backend.app.agents.editor import EditorAgent
from backend.app.agents.hook import HookAgent
from backend.app.agents.idea import IdeaAgent
from backend.app.agents.media import MediaAgent
from backend.app.agents.qc import QCAgent
from backend.app.agents.research import FactCheckAgent, ResearchAgent
from backend.app.agents.script import ScriptAgent
from backend.app.agents.storyboard import StoryboardAgent
from backend.app.agents.thumbnail import ThumbnailAgent
from backend.app.agents.title import DescriptionAgent, TitleAgent
from backend.app.agents.voice import VoiceAgent
from backend.app.agents.youtube import YouTubeAgent
from backend.app.config import settings
from backend.app.core.logging import logger
from backend.app.core.db import SyncMongoDB
from backend.app.core.repositories import JobRepository, VideoRepository
from backend.app.core.security import compute_content_hash
from backend.app.models.job import JobState, PublishingJob
from backend.app.pipeline.orchestrator import PipelineOrchestrator
from backend.app.providers.ai.openrouter import OpenRouterProvider
from backend.app.providers.search.ddg_search import DuckDuckGoSearchProvider
from backend.app.providers.storage.local_storage import LocalStorageProvider
from backend.app.providers.tts.edge_tts_provider import EdgeTTSProvider
from backend.app.providers.stt.whisper_provider import WhisperProvider
from backend.app.providers.media.stock_media import StockMediaEngine
from backend.app.providers.thumbnail.thumbnail_engine import ThumbnailEngine
from backend.app.providers.youtube.youtube_client import YouTubeClientProvider


def _build_orchestrator() -> PipelineOrchestrator:
    """Build a concrete PipelineOrchestrator using real provider and agent implementations."""
    storage = LocalStorageProvider(base_dir=settings.media_storage_dir)
    ai_provider = OpenRouterProvider(api_key=settings.openrouter_api_key, timeout_seconds=5.0, max_retries=1)
    search_provider = DuckDuckGoSearchProvider()
    tts_provider = EdgeTTSProvider()
    stt_provider = WhisperProvider()
    stock_provider = StockMediaEngine(media_dir=settings.media_storage_dir)
    thumb_provider = ThumbnailEngine()
    youtube_provider = YouTubeClientProvider()

    idea = IdeaAgent(ai_provider=ai_provider)
    research = ResearchAgent(ai_provider=ai_provider, search_provider=search_provider)
    fact_check = FactCheckAgent(ai_provider=ai_provider)
    hook = HookAgent(ai_provider=ai_provider)
    script = ScriptAgent(ai_provider=ai_provider)
    storyboard = StoryboardAgent(ai_provider=ai_provider)
    media = MediaAgent(stock_provider=stock_provider, storage_provider=storage)
    voice = VoiceAgent(tts_provider=tts_provider, storage_provider=storage)
    caption = CaptionAgent(stt_provider=stt_provider, storage_provider=storage)
    editor = EditorAgent(storage_provider=storage)
    qc = QCAgent()
    thumbnail = ThumbnailAgent(
        ai_provider=ai_provider,
        thumbnail_provider=thumb_provider,
        storage_provider=storage
    )
    title = TitleAgent(ai_provider=ai_provider)
    description = DescriptionAgent(ai_provider=ai_provider)
    youtube = YouTubeAgent(youtube_provider=youtube_provider)

    db = SyncMongoDB.get_db()
    job_repo = JobRepository(db)
    video_repo = VideoRepository(db)

    return PipelineOrchestrator(
        idea_agent=idea,
        research_agent=research,
        fact_check_agent=fact_check,
        hook_agent=hook,
        script_agent=script,
        storyboard_agent=storyboard,
        media_agent=media,
        voice_agent=voice,
        caption_agent=caption,
        editor_agent=editor,
        qc_agent=qc,
        thumbnail_agent=thumbnail,
        title_agent=title,
        description_agent=description,
        youtube_agent=youtube,
        db_job_repo=job_repo,
        db_video_repo=video_repo
    )


async def _execute_pipeline_job(job_id: str) -> dict[str, Any]:
    """Run the actual orchestrator against a persisted job and update Mongo state in-place."""
    db = SyncMongoDB.get_db()
    repo = JobRepository(db)
    video_repo = VideoRepository(db)
    job_data = db.publishing_jobs.find_one({"_id": job_id})
    topic = job_data.get("topic") if job_data else None
    orchestrator = _build_orchestrator()
    orchestrator.job_repo = repo
    orchestrator.video_repo = video_repo
    return await orchestrator.execute_job(job_id=job_id, custom_topic=topic)


def _run_async_pipeline(job_id: str) -> dict[str, Any]:
    """Execute the async orchestrator even when called from an already-running event loop, such as FastAPI request handling."""
    try:
        asyncio.get_running_loop()
    except RuntimeError:
        return asyncio.run(_execute_pipeline_job(job_id))

    result: dict[str, Any] = {}
    error: dict[str, Exception] = {}

    def runner() -> None:
        try:
            result["value"] = asyncio.run(_execute_pipeline_job(job_id))
        except Exception as exc2:  # pragma: no cover - defensive
            error["value"] = exc2

    worker = threading.Thread(target=runner, daemon=True)
    worker.start()
    worker.join()

    if "value" in error:
        raise error["value"]
    return result["value"]


@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def run_pipeline_task(self, job_id: str) -> dict[str, Any]:
    """Execute the full end-to-end video pipeline for a scheduled job."""
    logger.info(f"[Celery] Starting execution for job_id={job_id}")
    db = SyncMongoDB.get_db()

    job_data = db.publishing_jobs.find_one({"_id": job_id})
    if not job_data:
        from bson import ObjectId
        if ObjectId.is_valid(job_id):
            job_data = db.publishing_jobs.find_one({"_id": ObjectId(job_id)})

    if not job_data:
        logger.error(f"[Celery] Job {job_id} not found in database.")
        return {"status": "ERROR", "message": "Job not found"}

    current_state = job_data.get("state")
    if current_state in [JobState.PUBLISHED.value, JobState.READY.value]:
        logger.info(f"[Celery] Job {job_id} already in state {current_state}. Skipping redundant execution.")
        return {"status": "ALREADY_COMPLETED", "state": current_state}

    db.publishing_jobs.update_one(
        {"_id": job_data["_id"]},
        {"$set": {"state": JobState.QUEUED.value, "previous_state": current_state, "updated_at": datetime.now(timezone.utc)}}
    )

    try:
        result = _run_async_pipeline(job_id)
        db.publishing_jobs.update_one(
            {"_id": job_data["_id"]},
            {"$set": {"state": result.get("status", JobState.READY.value), "updated_at": datetime.now(timezone.utc)}}
        )
        return result
    except Exception as exc:
        logger.exception("[Celery] Pipeline execution failed for job_id=%s", job_id)
        db.publishing_jobs.update_one(
            {"_id": job_data["_id"]},
            {"$set": {"state": JobState.FAILED.value, "error_message": str(exc), "updated_at": datetime.now(timezone.utc)}}
        )
        raise


@shared_task
def pregenerate_slot_task(slot_index: int = 1) -> dict[str, Any]:
    """Pre-generate a video ahead of its publishing slot (01:00 for Slot 1, 12:00 for Slot 2)."""
    logger.info(f"[Celery Beat] Triggering pre-generation for Slot {slot_index}")
    db = SyncMongoDB.get_db()

    now = datetime.now(timezone.utc)
    date_str = now.strftime("%Y-%m-%d")
    idempotency_key = compute_content_hash(f"autopilot_{date_str}_slot{slot_index}")

    # Prevent duplicate job creation for the same slot
    existing = db.publishing_jobs.find_one({"idempotency_key": idempotency_key})
    if existing:
        logger.info(f"[Celery Beat] Slot {slot_index} already has an active job ({existing['_id']}). Skipping.")
        return {"status": "ALREADY_EXISTS", "job_id": str(existing["_id"])}

    job_doc = {
        "slot_index": slot_index,
        "scheduled_at": now,
        "state": JobState.CREATED.value,
        "idempotency_key": idempotency_key,
        "topic": "Autonomous Tech & AI Discovery",
        "created_at": now,
        "updated_at": now,
        "is_buffered": True
    }
    res = db.publishing_jobs.insert_one(job_doc)
    job_id = str(res.inserted_id)

    # Dispatch pipeline execution
    run_pipeline_task.delay(job_id)

    return {"status": "QUEUED", "job_id": job_id, "slot": slot_index}


@shared_task
def publish_slot_task(slot_index: int = 1) -> dict[str, Any]:
    """Publish a ready video at exact scheduled slot (07:00 Slot 1, 18:00 Slot 2)."""
    logger.info(f"[Celery Beat] Initiating publishing check for Slot {slot_index}")
    db = SyncMongoDB.get_db()

    now = datetime.now(timezone.utc)
    date_str = now.strftime("%Y-%m-%d")
    idempotency_key = compute_content_hash(f"autopilot_{date_str}_slot{slot_index}")

    job = db.publishing_jobs.find_one({"idempotency_key": idempotency_key})

    if not job or job.get("state") != JobState.READY.value:
        # Video is NOT ready at scheduled publish time!
        # Mark slot MISSED. Never fake success!
        logger.warning(f"[Celery Beat] Video for Slot {slot_index} was NOT ready at scheduled time. Marking MISSED.")
        if job:
            db.publishing_jobs.update_one(
                {"_id": job["_id"]},
                {
                    "$set": {
                        "state": JobState.MISSED.value,
                        "error_message": "Slot missed: Video was not rendered or QC-passed by scheduled publish time.",
                        "updated_at": now
                    }
                }
            )
        else:
            db.publishing_jobs.insert_one({
                "slot_index": slot_index,
                "scheduled_at": now,
                "state": JobState.MISSED.value,
                "idempotency_key": idempotency_key,
                "error_message": "Slot missed: Host was likely offline or asleep during pre-generation window.",
                "created_at": now,
                "updated_at": now
            })
        return {"status": "MISSED", "slot": slot_index}

    # If READY, transition to PUBLISHING
    db.publishing_jobs.update_one(
        {"_id": job["_id"]},
        {"$set": {"state": JobState.PUBLISHING.value, "updated_at": now}}
    )
    return {"status": "PUBLISHING", "job_id": str(job["_id"]), "slot": slot_index}


@shared_task
def reconcile_system_jobs_task() -> dict[str, Any]:
    """Periodic audit reconciling crashed or uncompleted jobs."""
    logger.info("[Celery Beat] Running system restart and failure reconciliation...")
    db = SyncMongoDB.get_db()

    # Find jobs stuck in intermediate states for more than 45 minutes
    now = datetime.now(timezone.utc)
    stuck_cursor = db.publishing_jobs.find({
        "state": {
            "$in": [
                JobState.QUEUED.value,
                JobState.RESEARCHING.value,
                JobState.SCRIPTING.value,
                JobState.RENDERING.value
            ]
        }
    })

    reconciled_count = 0
    for stuck in stuck_cursor:
        # Check if scheduled time has passed
        scheduled_at = stuck.get("scheduled_at", now)
        if (now - scheduled_at).total_seconds() > 3600:  # Older than 1 hour past scheduled
            db.publishing_jobs.update_one(
                {"_id": stuck["_id"]},
                {
                    "$set": {
                        "state": JobState.MISSED.value,
                        "error_message": "Reconciliation: Job was interrupted and exceeded scheduled window grace period.",
                        "updated_at": now
                    }
                }
            )
            reconciled_count += 1

    return {"status": "COMPLETED", "reconciled_count": reconciled_count}
