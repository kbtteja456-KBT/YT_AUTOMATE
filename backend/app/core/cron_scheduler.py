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
_is_tenant_processing: bool = False


def is_slot_published_today(slot_index: int, today_str: Optional[str] = None, workspace_id: Optional[str] = None) -> bool:
    """Check MongoDB to verify if a video was already published for the given slot today.
    - If workspace_id is provided, checks scoped to that tenant workspace.
    - If workspace_id is None, checks the platform owner's default channel.
    """
    try:
        from backend.app.core.db import SyncMongoDB
        from backend.app.core.security import compute_content_hash
        from backend.app.models.job import JobState
        db = SyncMongoDB.get_db()
        tz = zoneinfo.ZoneInfo(settings.timezone)
        now = datetime.now(tz)
        if not today_str:
            today_str = now.strftime("%Y-%m-%d")

        # Parse local midnight and convert to UTC for boundary search
        start_local = datetime.strptime(today_str, "%Y-%m-%d").replace(tzinfo=tz)
        start_utc = start_local.astimezone(timezone.utc)

        if workspace_id:
            idemp_key = compute_content_hash(f"autopilot_{today_str}_{workspace_id}_slot{slot_index}")
            job_doc = db.publishing_jobs.find_one({
                "workspace_id": workspace_id,
                "$or": [
                    {"idempotency_key": idemp_key, "state": JobState.PUBLISHED.value},
                    {
                        "slot_index": slot_index,
                        "state": JobState.PUBLISHED.value,
                        "$or": [
                            {"published_at": {"$gte": start_utc}},
                            {"created_at": {"$gte": start_utc}},
                        ]
                    }
                ]
            })
            if job_doc:
                return True

            doc = db.videos.find_one({
                "workspace_id": workspace_id,
                "slot_index": slot_index,
                "$and": [
                    {
                        "$or": [
                            {"status": "PUBLISHED"},
                            {"youtube_video_id": {"$exists": True, "$ne": None}}
                        ]
                    },
                    {
                        "$or": [
                            {"slot_date": today_str},
                            {"published_at": {"$gte": start_utc}},
                            {"created_at": {"$gte": start_utc}}
                        ]
                    }
                ]
            })
            return doc is not None

        # 1. Check publishing_jobs collection (Owner default)
        idempotency_key = compute_content_hash(f"autopilot_{today_str}_slot{slot_index}")
        job_doc = db.publishing_jobs.find_one({
            "$or": [
                {"idempotency_key": idempotency_key, "state": JobState.PUBLISHED.value},
                {
                    "slot_index": slot_index,
                    "state": JobState.PUBLISHED.value,
                    "$or": [
                        {"published_at": {"$gte": start_utc}},
                        {"created_at": {"$gte": start_utc}},
                    ]
                }
            ]
        })
        if job_doc:
            return True

        # 2. Check videos collection (Owner default)
        doc = db.videos.find_one({
            "slot_index": slot_index,
            "$and": [
                {
                    "$or": [
                        {"status": "PUBLISHED"},
                        {"youtube_video_id": {"$exists": True, "$ne": None}}
                    ]
                },
                {
                    "$or": [
                        {"slot_date": today_str},
                        {"published_at": {"$gte": start_utc}},
                        {"created_at": {"$gte": start_utc}}
                    ]
                }
            ]
        })
        return doc is not None
    except Exception as e:
        logger.error(f"Error checking slot {slot_index} status in DB: {e}")
        return False


def get_slot_status_today(slot_index: int, today_str: Optional[str] = None, workspace_id: Optional[str] = None) -> str:
    """Get the real-time status string for today's slot ('PUBLISHED', 'RUNNING', 'PENDING')."""
    global _is_pipeline_running, _currently_running_slot
    if _is_pipeline_running and _currently_running_slot == slot_index and workspace_id is None:
        return "RUNNING"
    if is_slot_published_today(slot_index, today_str, workspace_id=workspace_id):
        return "PUBLISHED"
    return "PENDING"


async def execute_slot_pipeline(
    slot_index: int,
    custom_topic: Optional[str] = None,
    workspace_id: Optional[str] = None
) -> dict:
    """Execute full end-to-end Short generation and YouTube publishing for a slot.
    - If workspace_id is None: Runs for the Platform Owner channel (100% untouched).
    - If workspace_id is specified: Runs for that tenant workspace with their niche & quota.
    """
    from datetime import timezone
    from bson import ObjectId
    from backend.app.core.db import SyncMongoDB
    from backend.app.core.security import compute_content_hash
    from backend.app.core.repositories import JobRepository, VideoRepository
    from backend.app.models.job import JobState
    from backend.app.celery_app.tasks import _build_orchestrator
    from backend.app.core.ledger import can_workspace_generate_sync, check_and_acquire_trial_quota_atomic_sync

    db = SyncMongoDB.get_db()
    now = datetime.now(timezone.utc)
    tz = zoneinfo.ZoneInfo(settings.timezone)
    date_str = datetime.now(tz).strftime("%Y-%m-%d")

    workspace_niche = "Python Quiz #Shorts"
    if workspace_id:
        can_gen, reason = can_workspace_generate_sync(workspace_id)
        if not can_gen:
            logger.warning(f"[Autopilot] Workspace {workspace_id} cannot publish: {reason}")
            return {"status": "QUOTA_EXHAUSTED", "reason": reason, "workspace_id": workspace_id}

        ws_obj = db.workspaces.find_one({"_id": ObjectId(workspace_id)}) if ObjectId.is_valid(workspace_id) else db.workspaces.find_one({"_id": workspace_id})
        if ws_obj:
            workspace_niche = ws_obj.get("niche") or ws_obj.get("settings", {}).get("niche") or "Tech & Innovation"
        idemp_prefix = f"autopilot_{date_str}_{workspace_id}_slot{slot_index}"
    else:
        ws_obj = db.workspaces.find_one({"is_legacy_default": True}) or db.workspaces.find_one()
        if ws_obj:
            workspace_niche = ws_obj.get("niche") or ws_obj.get("settings", {}).get("niche") or "Python Quiz #Shorts"
        idemp_prefix = f"autopilot_{date_str}_slot{slot_index}"
    custom_prompt = ws_obj.get("custom_content_prompt") or ws_obj.get("settings", {}).get("custom_content_prompt") if ws_obj else None
    pref_format = (
        ws_obj.get("content_template")
        or ws_obj.get("preferred_format")
        or ws_obj.get("settings", {}).get("content_template")
        or ws_obj.get("settings", {}).get("preferred_format")
        or "auto"
    ) if ws_obj else "auto"

    idempotency_key = compute_content_hash(idemp_prefix)
    existing = db.publishing_jobs.find_one({"idempotency_key": idempotency_key})

    if existing:
        if existing.get("state") == JobState.PUBLISHED.value:
            return {
                "status": "ALREADY_PUBLISHED",
                "youtube_url": existing.get("youtube_url", ""),
                "youtube_video_id": existing.get("youtube_video_id"),
            }

        # Concurrency Guard: If another runner is currently active (< 15 mins), stand down
        active_states = [
            JobState.RUNNING.value,
            JobState.RESEARCHING.value,
            JobState.SCRIPTING.value,
            JobState.STORYBOARDING.value,
            JobState.GENERATING_MEDIA.value,
            JobState.GENERATING_VOICE.value,
            JobState.GENERATING_CAPTIONS.value,
            JobState.GENERATED.value,
            JobState.RENDERING.value,
            JobState.RENDERED.value,
            JobState.QUALITY_CHECK.value,
            JobState.QC_PASSED.value,
            JobState.GENERATING_THUMBNAIL.value,
            JobState.UPLOADING.value,
            JobState.PUBLISHING.value,
        ]
        job_updated = existing.get("updated_at") or existing.get("created_at") or now
        if job_updated.tzinfo is None:
            job_updated = job_updated.replace(tzinfo=timezone.utc)
        age_seconds = (now - job_updated).total_seconds()
        if existing.get("state") in active_states and age_seconds < 15 * 60:
            logger.info(
                f"🔒 [CONCURRENCY GUARD] Slot {slot_index} is currently ACTIVE in another runner "
                f"(state='{existing.get('state')}'). Skipping local run to prevent collision."
            )
            return {"status": "ALREADY_RUNNING", "job_id": str(existing["_id"])}

        # Verified not running and not published - verify quota eligibility if tenant
        if workspace_id:
            allowed, reason = can_workspace_generate_sync(workspace_id)
            if not allowed:
                logger.warning(f"[Autopilot] Workspace {workspace_id} cannot generate: {reason}")
                return {"status": "QUOTA_EXHAUSTED", "reason": reason, "workspace_id": workspace_id}

        job_id = str(existing["_id"])
        db.publishing_jobs.update_one(
            {"_id": existing["_id"]},
            {"$set": {"state": JobState.RUNNING.value, "error_message": None, "updated_at": now}}
        )
    else:
        # Verified new run - verify quota eligibility if tenant
        if workspace_id:
            allowed, reason = can_workspace_generate_sync(workspace_id)
            if not allowed:
                logger.warning(f"[Autopilot] Workspace {workspace_id} cannot generate: {reason}")
                return {"status": "QUOTA_EXHAUSTED", "reason": reason, "workspace_id": workspace_id}

        doc = {
            "slot_index": slot_index,
            "scheduled_at": now,
            "state": JobState.RUNNING.value,
            "idempotency_key": idempotency_key,
            "topic": custom_topic or custom_prompt or workspace_niche,
            "niche": workspace_niche,
            "created_at": now,
            "updated_at": now,
            "is_buffered": False,
            "triggered_by": "fastapi_scheduler",
        }
        if workspace_id:
            doc["workspace_id"] = workspace_id
        res = db.publishing_jobs.insert_one(doc)
        job_id = str(res.inserted_id)

    orchestrator = _build_orchestrator(db, workspace_id=workspace_id)
    orchestrator.job_repo = JobRepository(db)
    orchestrator.video_repo = VideoRepository(db)
    return await orchestrator.execute_job(
        job_id=job_id,
        niche=workspace_niche,
        custom_topic=custom_topic,
        custom_prompt=custom_prompt or None,
        content_format=pref_format,
        publish_immediately=True,
        slot_index=slot_index
    )


async def run_slot_with_lock(slot_index: int, custom_topic: Optional[str] = None) -> dict:
    """Execute owner slot pipeline with mutual exclusion lock preventing concurrent overlapping runs."""
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


async def process_tenant_workspaces_for_slot(slot_index: int, today_str: str) -> None:
    """Scan and publish scheduled Shorts for all active tenant workspaces with connected YouTube channels."""
    global _is_tenant_processing
    if _is_tenant_processing:
        logger.debug(f"[Tenant Autopilot] Tenant processing cycle already active. Standing down.")
        return

    _is_tenant_processing = True
    try:
        from backend.app.core.db import SyncMongoDB
        from backend.app.core.ledger import can_workspace_generate_sync
        db = SyncMongoDB.get_db()

        # Clean up any stale interrupted jobs before starting the tenant loop
        reconcile_stuck_in_progress_jobs()

        cursor = db.workspaces.find({
            "is_legacy_default": {"$ne": True},
            "autopilot_enabled": True
        })
        tenants = list(cursor)
        if not tenants:
            return

        logger.info(f"[Tenant Autopilot] Evaluating {len(tenants)} tenant workspace(s) for Slot {slot_index}...")

        for ws in tenants:
            ws_id = str(ws["_id"])
            ws_name = ws.get("name", "Tenant Workspace")
            try:
                # 1. Connected YouTube channel check
                chan = db.youtube_channels.find_one({"workspace_id": ws_id, "is_active": True}) or db.youtube_channels.find_one({"workspace_id": ws_id})
                if not chan:
                    continue

                tok = db.oauth_tokens.find_one({"workspace_id": ws_id}) or db.oauth_tokens.find_one({"channel_id": chan["channel_id"]})
                if not tok or not (tok.get("encrypted_refresh_token") or tok.get("refresh_token")):
                    logger.info(f"[Tenant Autopilot] Workspace '{ws_name}' has no active OAuth credentials. Skipping.")
                    continue

                # 2. Already published today check
                if is_slot_published_today(slot_index, today_str, workspace_id=ws_id):
                    continue

                # 3. Check trial quota or BYOK key
                can_gen, reason = can_workspace_generate_sync(ws_id)
                if not can_gen:
                    logger.info(f"[Tenant Autopilot] Workspace '{ws_name}' ({ws_id}) cannot generate: {reason}")
                    continue

                # 4. Execute pipeline
                logger.info(f"🚀 [Tenant Autopilot] Launching Slot {slot_index} for '{ws_name}' (niche: {ws.get('niche')})")
                res = await execute_slot_pipeline(slot_index=slot_index, workspace_id=ws_id)
                logger.info(f"✅ [Tenant Autopilot] Completed Slot {slot_index} for '{ws_name}': status={res.get('status')}")

            except Exception as ws_err:
                logger.error(f"[Tenant Autopilot] Failed for workspace '{ws_name}': {ws_err}", exc_info=True)
    except Exception as top_err:
        logger.error(f"[Tenant Autopilot] Error scanning tenant workspaces: {top_err}", exc_info=True)
    finally:
        _is_tenant_processing = False


def reconcile_stuck_in_progress_jobs():
    """Self-healing sweep: identify jobs left in intermediate states from an interrupted run and reset/recover them."""
    try:
        from datetime import timedelta
        from pathlib import Path
        from backend.app.core.db import SyncMongoDB
        from backend.app.models.job import JobState
        db = SyncMongoDB.get_db()
        now_utc = datetime.now(timezone.utc)
        stale_threshold = now_utc - timedelta(minutes=15)

        active_states = [
            JobState.RUNNING.value,
            JobState.RESEARCHING.value,
            JobState.SCRIPTING.value,
            JobState.STORYBOARDING.value,
            JobState.GENERATING_MEDIA.value,
            JobState.GENERATING_VOICE.value,
            JobState.GENERATING_CAPTIONS.value,
            JobState.RENDERING.value,
            JobState.UPLOADING.value,
        ]

        stale_jobs = list(db.publishing_jobs.find({
            "state": {"$in": active_states},
            "$or": [
                {"updated_at": {"$lt": stale_threshold}},
                {"created_at": {"$lt": stale_threshold}},
                {"updated_at": {"$exists": False}},
            ]
        }))

        for job in stale_jobs:
            job_id = str(job["_id"])
            vid = db.videos.find_one({"job_id": job_id})
            if vid and vid.get("file_path") and Path(str(vid["file_path"])).exists():
                db.publishing_jobs.update_one(
                    {"_id": job["_id"]},
                    {"$set": {"state": JobState.READY.value, "updated_at": now_utc}}
                )
                logger.info(f"🔄 [Self-Healing] Job {job_id} has rendered MP4 on disk. Auto-transitioned to READY for publishing.")
            else:
                db.publishing_jobs.update_one(
                    {"_id": job["_id"]},
                    {
                        "$set": {
                            "state": JobState.FAILED.value,
                            "error_message": "Recovered by autonomous reconciliation after system interruption.",
                            "updated_at": now_utc
                        }
                    }
                )
                if job.get("workspace_id"):
                    from backend.app.core.ledger import refund_trial_quota_atomic_sync
                    refund_trial_quota_atomic_sync(str(job["workspace_id"]))
                logger.info(f"🔄 [Self-Healing] Stale job {job_id} cleared so slot pipeline can run freshly.")
    except Exception as e:
        logger.warning(f"[Self-Healing] Reconciliation notice: {e}")


async def _scheduler_loop():
    """Continuous background loop with automatic catch-up recovery and self-healing reconciliation.
    - Slot 1 (07:00 AM IST): Active 07:00 - 17:59.
    - Slot 2 (06:00 PM IST): Active 18:00 - 23:59.
    Runs Owner's slot pipeline FIRST, then processes any active tenant workspaces.
    """
    logger.info(f"Starting Autopilot Scheduler with Catch-Up Recovery: 07:00 & 18:00 ({settings.timezone})")
    tz = zoneinfo.ZoneInfo(settings.timezone)

    # Initial self-healing sweep on startup
    reconcile_stuck_in_progress_jobs()

    sweep_counter = 0
    while True:
        try:
            if not _is_autopilot_enabled:
                await asyncio.sleep(15)
                continue

            sweep_counter += 1
            if sweep_counter % 20 == 0:  # Every 10 minutes, self-heal any stale interrupted jobs
                reconcile_stuck_in_progress_jobs()

            now = datetime.now(tz)
            today_str = now.strftime("%Y-%m-%d")
            hour = now.hour

            # Morning Slot (Slot 1): Target 07:00 AM IST
            if 7 <= hour < 18:
                if not is_slot_published_today(1, today_str) and not _is_pipeline_running:
                    logger.info(f"⏰ [Autopilot Scheduler] Slot 1 (07:00 AM) due or catching up for {today_str}. Launching Owner Pipeline...")
                    asyncio.create_task(run_slot_with_lock(1))
                # Process active tenant workspaces
                if not _is_tenant_processing:
                    asyncio.create_task(process_tenant_workspaces_for_slot(1, today_str))

            # Evening Slot (Slot 2): Target 06:00 PM (18:00) IST
            elif 18 <= hour <= 23:
                if not is_slot_published_today(2, today_str) and not _is_pipeline_running:
                    logger.info(f"⏰ [Autopilot Scheduler] Slot 2 (06:00 PM) due or catching up for {today_str}. Launching Owner Pipeline...")
                    asyncio.create_task(run_slot_with_lock(2))
                # Process active tenant workspaces
                if not _is_tenant_processing:
                    asyncio.create_task(process_tenant_workspaces_for_slot(2, today_str))

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
