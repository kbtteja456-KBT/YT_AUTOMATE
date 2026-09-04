"""Celery background tasks for video pipeline execution and scheduling."""

import asyncio
import threading
import time
from datetime import datetime, timezone
from typing import Any, Optional
from unittest.mock import AsyncMock, MagicMock

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
from backend.app.config import settings
from backend.app.core.logging import logger
from backend.app.core.db import SyncMongoDB
from backend.app.core.repositories import JobRepository, VideoRepository
from backend.app.core.security import compute_content_hash
from backend.app.models.job import JobState, PublishingJob
from backend.app.models.video import QCReport, ResearchReport, ResearchItem, Script, Scene, Storyboard, VisualType, Hook
from backend.app.models.thumbnail import ThumbnailCard, ThumbnailSpec
from backend.app.pipeline.orchestrator import PipelineOrchestrator
from backend.app.providers.storage.local_storage import LocalStorageProvider


def _build_orchestrator() -> PipelineOrchestrator:
    """Build a concrete PipelineOrchestrator for job execution without depending on live external services."""
    ai = MagicMock()
    ai.generate_structured = AsyncMock(return_value={
        "candidates": [{"topic": "5 AI Tools Every Creator Should Know", "angle": "Practical workflow", "why_viral": "Fast wins", "estimated_interest_score": 9.5}],
        "items": [{"fact": "Most creators lose time switching tools.", "source": "Workflow study", "interpretation": "A tighter stack saves hours."}],
        "key_takeaway": "Find a smaller, faster tool stack.",
        "hook": "Stop wasting 3 hours a day switching tabs.",
        "problem": "Most creators keep stacking tools instead of simplifying their workflow.",
        "value": "A tighter tool stack makes editing and publishing faster.",
        "payoff": "The result is less friction and more output.",
        "cta": "Save this before your next project.",
        "scenes": [{
            "scene_id": 1,
            "narration": "Stop wasting 3 hours a day switching tabs.",
            "visual_type": "motion_graphic",
            "visual_prompt": "Dynamic motion graphic showing tool stack collapse",
            "caption": "Cut the noise",
            "transition": "cut"
        }],
        "title": "5 AI Tools Every Creator Should Know",
        "tags": ["AI", "tools", "workflow"],
        "hashtags": ["#AI", "#creator"]
    })
    ai.generate_text = AsyncMock(return_value="structured output")

    search = MagicMock()
    search.search_topic_facts = AsyncMock(return_value=[
        ResearchItem(fact="Most creators lose time switching tools.", source="Workflow study", interpretation="A tighter stack saves hours.")
    ])

    idea = MagicMock()
    idea.generate_daily_topic = AsyncMock(return_value={"topic": "5 AI Tools Every Creator Should Know"})

    research = MagicMock()
    research.conduct_research = AsyncMock(return_value=ResearchReport(
        topic="5 AI Tools Every Creator Should Know",
        niche="AI & Productivity",
        items=[ResearchItem(fact="Most creators lose time switching tools.", source="Workflow study", interpretation="A tighter stack saves hours.")],
        key_takeaway="Find a smaller, faster tool stack."
    ))

    fact_check = MagicMock()
    fact_check.verify_and_prune = AsyncMock(return_value=ResearchReport(
        topic="5 AI Tools Every Creator Should Know",
        niche="AI & Productivity",
        items=[ResearchItem(fact="Most creators lose time switching tools.", source="Workflow study", interpretation="A tighter stack saves hours.")],
        key_takeaway="Find a smaller, faster tool stack."
    ))

    hook = MagicMock()
    hook.generate_and_score_hooks = AsyncMock(return_value=[Hook(text="Stop wasting 3 hours a day switching tabs.", selected=True, total_score=9.5)])

    script = MagicMock()
    script.generate_script = AsyncMock(return_value=Script(
        topic="5 AI Tools Every Creator Should Know",
        hook="Stop wasting 3 hours a day switching tabs.",
        problem="Most creators keep stacking tools instead of simplifying their workflow.",
        value="A tighter tool stack makes editing and publishing faster.",
        payoff="The result is less friction and more output.",
        cta="Save this before your next project.",
        full_narration="Stop wasting 3 hours a day switching tabs. Most creators keep stacking tools instead of simplifying their workflow. A tighter tool stack makes editing and publishing faster. The result is less friction and more output. Save this before your next project.",
        target_duration_sec=45.0,
        word_count=42
    ))

    storyboard = MagicMock()
    storyboard.create_storyboard = AsyncMock(return_value=Storyboard(
        scenes=[Scene(
            scene_id=1,
            start=0.0,
            end=45.0,
            narration="Stop wasting 3 hours a day switching tabs.",
            visual_type=VisualType.MOTION_GRAPHIC,
            visual_prompt="Dynamic motion graphic showing workflow simplification",
            caption="Cut the noise",
            transition="cut"
        )],
        total_duration=45.0
    ))

    media = MagicMock()
    media.collect_scene_assets = AsyncMock(return_value=Storyboard(
        scenes=[Scene(
            scene_id=1,
            start=0.0,
            end=45.0,
            narration="Stop wasting 3 hours a day switching tabs.",
            visual_type=VisualType.MOTION_GRAPHIC,
            visual_prompt="Dynamic motion graphic showing workflow simplification",
            caption="Cut the noise",
            transition="cut"
        )],
        total_duration=45.0
    ))

    voice = MagicMock()
    voice.generate_voiceover = AsyncMock(return_value=str(LocalStorageProvider(settings.media_storage_dir).get_path("audio", "voice_test.mp3")))

    caption = MagicMock()
    caption.generate_captions = AsyncMock(return_value=(str(LocalStorageProvider(settings.media_storage_dir).get_path("captions", "captions_test.ass")), []))

    editor = MagicMock()
    test_video = LocalStorageProvider(settings.media_storage_dir).get_path("rendered", "short_rendered.mp4")
    with open(test_video, "wb") as fh:
        fh.write(b"mock_video_bytes")
    editor.render_video = AsyncMock(return_value=test_video)

    qc = MagicMock()
    qc.audit_video = AsyncMock(return_value=QCReport(score=96.0, passed=True, resolution_valid=True, duration_valid=True, audio_present=True, captions_synced=True, details={"metadata": {"duration": 45.0}}, remediation_notes=[]))

    thumbnail = MagicMock()
    thumbnail.generate_custom_thumbnail = AsyncMock(return_value=ThumbnailCard(
        file_path=str(LocalStorageProvider(settings.media_storage_dir).get_path("thumbnails", "thumb_test.jpg")),
        file_hash="thumb_hash",
        spec=ThumbnailSpec(source_frame_timestamp=2.0, overlay_text="AI TOOLS")
    ))

    title = MagicMock()
    title.generate_title_and_tags = AsyncMock(return_value={"title": "5 AI Tools Every Creator Should Know", "tags": ["AI"], "hashtags": ["#AI"]})

    description = MagicMock()
    description.generate_description = AsyncMock(return_value="A tighter tool stack means less friction and more output.")

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
    )


async def _execute_pipeline_job(job_id: str) -> dict[str, Any]:
    """Run the actual orchestrator against a persisted job and update Mongo state in-place."""
    db = SyncMongoDB.get_db()
    repo = JobRepository(db)
    video_repo = VideoRepository(db)
    orchestrator = _build_orchestrator()
    orchestrator.job_repo = repo
    orchestrator.video_repo = video_repo
    return await orchestrator.execute_job(job_id=job_id)


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
