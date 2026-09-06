"""Autonomous Daily Publishing Scheduler with Intelligent Catch-Up Recovery.
Target Slots: 07:00 AM (Slot 1) and 06:00 PM (Slot 2) Asia/Kolkata.
"""

import asyncio
from datetime import datetime, timezone
import zoneinfo
from typing import Any, Optional

from backend.app.config import settings
from backend.app.core.logging import logger

_scheduler_task: Optional[asyncio.Task] = None
_is_autopilot_enabled: bool = True
_is_pipeline_running: bool = False
_currently_running_slot: Optional[int] = None


def is_slot_published_today(slot_index: int, today_str: Optional[str] = None) -> bool:
    """Check MongoDB to verify if a video was already published for the given slot today."""
    try:
        from backend.app.core.db import SyncMongoDB
        db = SyncMongoDB.get_db()
        tz = zoneinfo.ZoneInfo(settings.timezone)
        now = datetime.now(tz)
        if not today_str:
            today_str = now.strftime("%Y-%m-%d")

        # Parse local midnight and convert to UTC for boundary search
        start_local = datetime.strptime(today_str, "%Y-%m-%d").replace(tzinfo=tz)
        start_utc = start_local.astimezone(timezone.utc)

        # Check for published video with matching slot_index for today
        doc = db.videos.find_one({
            "slot_index": slot_index,
            "status": "PUBLISHED",
            "$or": [
                {"slot_date": today_str},
                {"published_at": {"$gte": start_utc}},
                {"created_at": {"$gte": start_utc}}
            ]
        })
        return doc is not None
    except Exception as e:
        logger.error(f"Error checking slot {slot_index} status in DB: {e}")
        return False


def get_slot_status_today(slot_index: int, today_str: Optional[str] = None) -> str:
    """Get the real-time status string for today's slot ('PUBLISHED', 'RUNNING', 'PENDING')."""
    global _is_pipeline_running, _currently_running_slot
    if _is_pipeline_running and _currently_running_slot == slot_index:
        return "RUNNING"
    if is_slot_published_today(slot_index, today_str):
        return "PUBLISHED"
    return "PENDING"


async def execute_slot_pipeline(slot_index: int, custom_topic: Optional[str] = None) -> dict:
    """Execute full end-to-end Short generation and YouTube publishing for a slot.

    Uses the REAL PipelineOrchestrator — same path as Celery tasks and run_slot_cli.py.
    No dependency on run_autopilot_pipeline() (deleted) or Celery/Redis.
    """
    from datetime import timezone
    from backend.app.core.db import SyncMongoDB
    from backend.app.core.security import compute_content_hash
    from backend.app.core.repositories import JobRepository, VideoRepository
    from backend.app.models.job import JobState
    from backend.app.celery_app.tasks import _build_orchestrator

    db = SyncMongoDB.get_db()
    now = datetime.now(timezone.utc)
    tz = zoneinfo.ZoneInfo(settings.timezone)
    date_str = datetime.now(tz).strftime("%Y-%m-%d")
    idempotency_key = compute_content_hash(f"autopilot_{date_str}_slot{slot_index}")

    existing = db.publishing_jobs.find_one({"idempotency_key": idempotency_key})
    if existing and existing.get("state") == JobState.PUBLISHED.value:
        return {
            "status": "ALREADY_PUBLISHED",
            "youtube_url": existing.get("youtube_url", ""),
            "youtube_video_id": existing.get("youtube_video_id"),
        }

    if existing:
        job_id = str(existing["_id"])
        db.publishing_jobs.update_one(
            {"_id": existing["_id"]},
            {"$set": {"state": JobState.CREATED.value, "error_message": None, "updated_at": now}}
        )
    else:
        doc = {
            "slot_index": slot_index,
            "scheduled_at": now,
            "state": JobState.CREATED.value,
            "idempotency_key": idempotency_key,
            "topic": custom_topic or "Python Quiz #Shorts",
            "created_at": now,
            "updated_at": now,
            "is_buffered": False,
            "triggered_by": "fastapi_scheduler",
        }
        res = db.publishing_jobs.insert_one(doc)
        job_id = str(res.inserted_id)

    orchestrator = _build_orchestrator(db)
    orchestrator.job_repo = JobRepository(db)
    orchestrator.video_repo = VideoRepository(db)
    return await orchestrator.execute_job(job_id=job_id, custom_topic=custom_topic)


async def run_slot_with_lock(slot_index: int, custom_topic: Optional[str] = None) -> dict:
    """Execute slot pipeline with mutual exclusion lock preventing concurrent overlapping runs."""
    global _is_pipeline_running, _currently_running_slot
    if _is_pipeline_running:
        logger.warning(f"Pipeline already active for slot {_currently_running_slot}. Skipping overlapping run.")
        return {"status": "SKIPPED", "reason": f"Slot {_currently_running_slot} is currently running."}

    _is_pipeline_running = True
    _currently_running_slot = slot_index
    try:
        result = await execute_slot_pipeline(slot_index=slot_index, custom_topic=custom_topic)
        logger.info(f"✅ Slot {slot_index} finished successfully: {result.get('youtube_url')}")
        return result
    except Exception as exc:
        logger.error(f"❌ Slot {slot_index} pipeline encountered error: {exc}", exc_info=True)
        return {"status": "ERROR", "error": str(exc)}
    finally:
        _is_pipeline_running = False
        _currently_running_slot = None


async def _scheduler_loop():
    """Continuous background loop with automatic catch-up recovery.
    - Slot 1 (07:00 AM IST): Active 07:00 - 17:59. If not published today, triggers immediately.
    - Slot 2 (06:00 PM IST): Active 18:00 - 23:59. If not published today, triggers immediately.
    """
    logger.info(f"Starting Autopilot Scheduler with Catch-Up Recovery: 07:00 & 18:00 ({settings.timezone})")
    tz = zoneinfo.ZoneInfo(settings.timezone)

    while True:
        try:
            if not _is_autopilot_enabled:
                await asyncio.sleep(15)
                continue

            now = datetime.now(tz)
            today_str = now.strftime("%Y-%m-%d")
            hour = now.hour

            # Morning Slot (Slot 1): Target 07:00 AM IST
            # If current time is 07:00 or later (up to 17:59) and Slot 1 has not posted yet today:
            if 7 <= hour < 18:
                if not is_slot_published_today(1, today_str) and not _is_pipeline_running:
                    logger.info(f"⏰ [Autopilot Scheduler] Slot 1 (07:00 AM) due or catching up for {today_str}. Launching...")
                    asyncio.create_task(run_slot_with_lock(1))

            # Evening Slot (Slot 2): Target 06:00 PM (18:00) IST
            # If current time is 18:00 or later (up to 23:59) and Slot 2 has not posted yet today:
            elif 18 <= hour <= 23:
                if not is_slot_published_today(2, today_str) and not _is_pipeline_running:
                    logger.info(f"⏰ [Autopilot Scheduler] Slot 2 (06:00 PM) due or catching up for {today_str}. Launching...")
                    asyncio.create_task(run_slot_with_lock(2))

            # Poll interval: check every 30 seconds
            await asyncio.sleep(30)
        except asyncio.CancelledError:
            logger.info("Autopilot Scheduler loop cancelled.")
            break
        except Exception as e:
            logger.error(f"Autopilot Scheduler error: {e}", exc_info=True)
            await asyncio.sleep(30)


def start_autopilot_scheduler():
    """Start the background scheduler task inside the FastAPI event loop."""
    global _scheduler_task, _is_autopilot_enabled
    _is_autopilot_enabled = True
    if _scheduler_task is None or _scheduler_task.done():
        _scheduler_task = asyncio.create_task(_scheduler_loop())
        logger.info("Autonomous daily scheduler initialized.")


def stop_autopilot_scheduler():
    """Stop the background scheduler task gracefully."""
    global _scheduler_task, _is_autopilot_enabled
    _is_autopilot_enabled = False
    if _scheduler_task and not _scheduler_task.done():
        _scheduler_task.cancel()
        logger.info("Autonomous daily scheduler stopped.")


def set_autopilot_enabled(enabled: bool) -> bool:
    """Toggle the autonomous scheduler state on or off."""
    global _is_autopilot_enabled, _scheduler_task
    _is_autopilot_enabled = enabled
    if enabled:
        start_autopilot_scheduler()
    else:
        logger.info("Autopilot scheduler paused by user.")
    return _is_autopilot_enabled


def get_autopilot_status() -> dict[str, Any]:
    """Retrieve comprehensive real-time status of the autopilot scheduler."""
    tz = zoneinfo.ZoneInfo(settings.timezone)
    now = datetime.now(tz)
    today_str = now.strftime("%Y-%m-%d")

    return {
        "is_enabled": _is_autopilot_enabled,
        "daily_limit": settings.daily_video_limit,
        "slot_1_time": "07:00",
        "slot_2_time": "18:00",
        "timezone": settings.timezone,
        "zero_cost_mode": settings.zero_cost_mode,
        "is_running": _is_pipeline_running,
        "running_slot": _currently_running_slot,
        "status_today": {
            "slot_1": get_slot_status_today(1, today_str),
            "slot_2": get_slot_status_today(2, today_str)
        }
    }
