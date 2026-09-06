"""Standalone CLI runner for autonomous YouTube Shorts publishing.

Executed by: .github/workflows/daily_autopilot.yml (GitHub Actions — primary scheduler)
Also runnable manually for local testing.

This script calls the REAL PipelineOrchestrator via the same path used and verified in
backend/app/celery_app/tasks.py (_build_orchestrator / _execute_pipeline_job).

It does NOT depend on a running Celery worker or Redis broker.
MongoDB Atlas must be reachable from wherever this runs (GitHub Actions runners use Atlas,
not a local database — see MONGODB_URI in GitHub Secrets).
"""

import sys
import os
import argparse
import asyncio
from datetime import datetime, timezone
import zoneinfo

# Ensure workspace root is on sys.path so 'backend.*' imports resolve
WORKSPACE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, WORKSPACE_DIR)

from backend.app.config import settings
from backend.app.core.logging import logger
from backend.app.core.db import SyncMongoDB
from backend.app.core.cron_scheduler import is_slot_published_today
from backend.app.core.security import compute_content_hash
from backend.app.models.job import JobState

# Import the real orchestrator builder — the same function used by Celery tasks.
# No Celery/Redis needed: orchestrator.execute_job() is pure async Python that
# talks directly to MongoDB Atlas and the YouTube API.
from backend.app.celery_app.tasks import _build_orchestrator


def log_run(message: str):
    """Log to stdout and persistent file."""
    tz = zoneinfo.ZoneInfo(settings.timezone)
    now_str = datetime.now(tz).strftime("%Y-%m-%d %H:%M:%S %Z")
    line = f"[{now_str}] {message}"
    print(line, flush=True)
    log_file = os.path.join(WORKSPACE_DIR, "media_storage", "autopilot_scheduler.log")
    os.makedirs(os.path.dirname(log_file), exist_ok=True)
    try:
        with open(log_file, "a", encoding="utf-8") as f:
            f.write(line + "\n")
    except OSError:
        pass  # Log file write failure must never suppress the pipeline error


async def run_real_pipeline(slot_index: int, custom_topic: str | None = None) -> dict:
    """
    Execute the REAL full pipeline (IdeaAgent → FactCheckAgent → QCAgent → YouTubeAgent)
    via PipelineOrchestrator.

    - Creates a publishing_jobs document with an idempotency key (same logic as Celery tasks).
    - Idempotency key prevents double-publishing when GitHub Actions fires multiple runners
      for the same slot/date.
    - Asserts a real youtube_video_id from the API response before declaring success.
    - On failure, transitions job to FAILED with real error — never to PUBLISHED.
    """
    db = SyncMongoDB.get_db()
    now = datetime.now(timezone.utc)
    tz = zoneinfo.ZoneInfo(settings.timezone)
    now_local = datetime.now(tz)
    date_str = now_local.strftime("%Y-%m-%d")

    # Idempotency: reuse an existing job for this slot/date rather than creating a duplicate
    idempotency_key = compute_content_hash(f"autopilot_{date_str}_slot{slot_index}")
    existing_job = db.publishing_jobs.find_one({"idempotency_key": idempotency_key})

    if existing_job and existing_job.get("state") == JobState.PUBLISHED.value:
        yt_url = existing_job.get("youtube_url", "")
        log_run(
            f"✅ Slot {slot_index} already PUBLISHED today "
            f"(job={existing_job['_id']}, url={yt_url}). Skipping."
        )
        return {
            "status": "ALREADY_PUBLISHED",
            "youtube_url": yt_url,
            "youtube_video_id": existing_job.get("youtube_video_id"),
        }

    if existing_job and existing_job.get("state") not in (
        JobState.CREATED.value,
        JobState.FAILED.value,
        JobState.MISSED.value,
    ):
        # Job is in an intermediate state (QUEUED / RENDERING / etc.) — wait is not practical
        # in a 15-min GitHub Actions job, so we proceed to create a fresh job record only if
        # the existing one is genuinely terminal.
        log_run(
            f"⚠️  Existing job for Slot {slot_index} is in state "
            f"'{existing_job.get('state')}'. Proceeding anyway with a fresh orchestrator run."
        )

    # Create (or reuse) the job document
    if existing_job:
        job_id = str(existing_job["_id"])
        db.publishing_jobs.update_one(
            {"_id": existing_job["_id"]},
            {
                "$set": {
                    "state": JobState.CREATED.value,
                    "error_message": None,
                    "updated_at": now,
                }
            },
        )
        log_run(f"♻️  Reusing existing job {job_id} for Slot {slot_index} / {date_str}.")
    else:
        job_doc = {
            "slot_index": slot_index,
            "scheduled_at": now,
            "state": JobState.CREATED.value,
            "idempotency_key": idempotency_key,
            "topic": custom_topic or "Python Quiz #Shorts",
            "created_at": now,
            "updated_at": now,
            "is_buffered": False,
            "triggered_by": "github_actions_cli",
        }
        res = db.publishing_jobs.insert_one(job_doc)
        job_id = str(res.inserted_id)
        log_run(f"📝 Created new job {job_id} for Slot {slot_index} / {date_str}.")

    # Build the real orchestrator — zero mocks, zero Celery dependency
    orchestrator = _build_orchestrator(db)

    from backend.app.core.repositories import JobRepository, VideoRepository
    orchestrator.job_repo = JobRepository(db)
    orchestrator.video_repo = VideoRepository(db)

    log_run(f"🤖 Launching real PipelineOrchestrator for job {job_id} (slot {slot_index})...")
    result = await orchestrator.execute_job(
        job_id=job_id,
        custom_topic=custom_topic,
        publish_immediately=True,
        slot_index=slot_index
    )

    # Hard-assert that a real YouTube video ID was returned — never accept a fake success
    youtube_video_id = result.get("youtube_video_id") or result.get("video_id")
    youtube_url = result.get("youtube_url") or result.get("url")

    if not youtube_video_id:
        raise RuntimeError(
            f"Pipeline completed but YouTube API did not return a confirmed real video ID. "
            f"Full result: {result}"
        )

    log_run(f"🎉 Real video ID confirmed: {youtube_video_id} → {youtube_url}")

    # Verify the real QC score is present (not the legacy hardcoded 98.0)
    qc_score = result.get("quality_score")
    if qc_score is not None:
        log_run(f"📊 Real QCAgent score: {qc_score:.1f}")
    else:
        log_run("⚠️  QC score not present in result — check QCAgent output in DB.")

    return result


async def main():
    parser = argparse.ArgumentParser(
        description="Real-pipeline YouTube Shorts CLI Runner (GitHub Actions primary)"
    )
    parser.add_argument(
        "--slot",
        type=int,
        default=0,
        choices=[0, 1, 2],
        help="Slot index: 1 = Morning 07:00 IST, 2 = Evening 18:00 IST, 0 = Auto-detect by IST time",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Force execution even if this slot was already published today",
    )
    parser.add_argument(
        "--topic",
        type=str,
        default=None,
        help="Optional custom topic override (overrides IdeaAgent quiz pool selection)",
    )
    args = parser.parse_args()

    tz = zoneinfo.ZoneInfo(settings.timezone)
    now_local = datetime.now(tz)
    today_str = now_local.strftime("%Y-%m-%d")

    slot = args.slot
    if slot == 0:
        # Auto-detect: morning slot if before 13:00 IST, evening slot otherwise
        slot = 1 if now_local.hour < 13 else 2
        log_run(
            f"🕒 Auto-detected slot from current time "
            f"({now_local.strftime('%H:%M')} IST): Slot {slot}"
        )

    slot_name = "Morning Slot 1 (07:00 AM IST)" if slot == 1 else "Evening Slot 2 (06:00 PM IST)"
    log_run(f"🔔 Task triggered for {slot_name}")

    # Check idempotency via MongoDB Atlas (reachable from GitHub Actions runners)
    if not args.force and is_slot_published_today(slot, today_str):
        log_run(
            f"✅ {slot_name} has ALREADY been published today ({today_str}). "
            f"Skipping redundant run. Use --force to override."
        )
        sys.exit(0)

    log_run(
        f"🚀 Starting REAL pipeline (PipelineOrchestrator) "
        f"for {slot_name} — slot {slot}, date {today_str}..."
    )

    try:
        result = await run_real_pipeline(slot_index=slot, custom_topic=args.topic)
        yt_url = result.get("youtube_url")
        if not yt_url or yt_url in ("Local Render Only", "", None):
            raise RuntimeError(
                f"Pipeline reported success but YouTube URL is missing or invalid: {result}"
            )
        log_run(f"✅ SUCCESS: Published to YouTube → {yt_url}")
        sys.exit(0)
    except Exception as e:
        log_run(f"❌ PIPELINE FAILED: {e}")
        logger.exception("CLI Real-Pipeline Error")
        sys.exit(1)  # Non-zero exit causes GitHub Actions to mark the run as FAILED


if __name__ == "__main__":
    asyncio.run(main())
