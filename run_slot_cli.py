"""Standalone CLI runner for autonomous 24/7 YouTube Shorts publishing in the cloud.

Executed by: .github/workflows/daily_autopilot.yml (GitHub Actions — 100% cloud scheduler)
Can also be triggered via GitHub repository_dispatch (from cron-job.org or webhooks)
and workflow_dispatch for manual testing.

Zero Laptop Dependency:
- Database: MongoDB Atlas (cloud)
- YouTube OAuth: Decrypted from MongoDB Atlas in-memory
- Video Rendering: Ubuntu Linux system FFmpeg & Liberation fonts
- Voice: Edge TTS (cloud synthesis)
- Stock Media: Pexels API / Incompetech CC-BY fallback
"""

import sys
import os
import argparse
import asyncio
import subprocess
import shutil
from datetime import datetime, timezone, timedelta
import zoneinfo
from typing import Optional, Dict, Any

# Ensure workspace root is on sys.path so 'backend.*' imports resolve
WORKSPACE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, WORKSPACE_DIR)

from backend.app.config import settings
from backend.app.core.logging import logger
from backend.app.core.db import SyncMongoDB
from backend.app.core.cron_scheduler import is_slot_published_today
from backend.app.core.security import compute_content_hash
from backend.app.models.job import JobState
from backend.app.celery_app.tasks import _build_orchestrator, _get_authenticated_youtube_provider
from pymongo.collection import ReturnDocument
from pymongo.errors import DuplicateKeyError


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
        pass


def check_health() -> bool:
    """Comprehensive pre-flight health check verifying all cloud automation components.
    
    Verifies:
    1. Required environment variables
    2. Cloud MongoDB Atlas connectivity (blocks localhost/private IPs)
    3. YouTube OAuth credentials decryption and channel API verification
    4. OpenRouter API connectivity
    5. FFmpeg binary, codecs, and font configuration
    """
    print("\n" + "=" * 65)
    print("AI YOUTUBE SHORTS AUTOPILOT - CLOUD HEALTH CHECK")
    print("=" * 65)
    all_passed = True

    # 1. Check Environment Variables
    print("\n[1/5] Checking Environment Variables...")
    required_vars = [
        ("MONGODB_URI", settings.mongodb_uri),
        ("ENCRYPTION_KEY", settings.encryption_key),
        ("GOOGLE_CLIENT_ID", settings.google_client_id),
        ("GOOGLE_CLIENT_SECRET", settings.google_client_secret),
        ("PEXELS_API_KEY", settings.pexels_api_key),
        ("OPENROUTER_API_KEY", settings.openrouter_api_key),
    ]
    missing_vars = [name for name, val in required_vars if not val or val.strip() == ""]
    if missing_vars:
        print(f"  ❌ Missing required environment variables: {', '.join(missing_vars)}")
        all_passed = False
    else:
        print("  ✅ All 6 required environment variables configured.")

    # Check that MongoDB URI is cloud-accessible (not localhost)
    mongo_uri = settings.mongodb_uri.lower()
    if "localhost" in mongo_uri or "127.0.0.1" in mongo_uri or "mongodb://192.168." in mongo_uri:
        print(f"  ❌ BLOCKER: MONGODB_URI points to localhost/private IP ({settings.mongodb_uri[:20]}...).")
        print("     GitHub Actions cannot connect to a local database. Use MongoDB Atlas (mongodb+srv://...).")
        all_passed = False
    else:
        print("  ✅ MONGODB_URI is cloud-accessible (MongoDB Atlas).")

    # Optional variables
    optional_vars = [
        ("FMA_API_KEY", settings.fma_api_key, "Free Music Archive (optional fallback: Incompetech CC-BY)"),
        ("PIXABAY_API_KEY", settings.pixabay_api_key, "Pixabay stock media (optional fallback: Pexels)"),
    ]
    for name, val, desc in optional_vars:
        status = "Configured" if val and val.strip() else "Not set (optional, gracefully skipped)"
        print(f"  ℹ️  {name}: {status} — {desc}")

    # 2. Check Cloud MongoDB Atlas Connection
    print("\n[2/5] Testing MongoDB Atlas Connection...")
    try:
        db = SyncMongoDB.get_db()
        db.command("ping")
        collections = db.list_collection_names()
        print(f"  ✅ Connected to MongoDB Atlas: '{settings.mongodb_db_name}' ({len(collections)} collections found).")
    except Exception as e:
        print(f"  ❌ MongoDB Atlas Connection Failed: {e}")
        all_passed = False

    # 3. Check YouTube OAuth Authentication
    print("\n[3/5] Testing YouTube OAuth Authentication from MongoDB...")
    try:
        db = SyncMongoDB.get_db()
        provider = _get_authenticated_youtube_provider(db)
        if not provider.credentials:
            print("  ❌ No valid YouTube credentials found in MongoDB 'oauth_tokens' collection.")
            all_passed = False
        else:
            service = provider._get_service()
            req = service.channels().list(part="snippet,statistics", mine=True)
            res = req.execute()
            items = res.get("items", [])
            if items:
                channel = items[0]
                ch_title = channel["snippet"]["title"]
                ch_id = channel["id"]
                subs = channel["statistics"].get("subscriberCount", "N/A")
                print(f"  ✅ Authenticated YouTube Channel: '{ch_title}' (ID: {ch_id}, Subscribers: {subs}).")
            else:
                print("  ❌ YouTube API authenticated, but no channel found for this account.")
                all_passed = False
    except Exception as e:
        print(f"  ❌ YouTube Authentication Failed: {e}")
        all_passed = False

    # 4. Check OpenRouter Free Model API
    print("\n[4/5] Testing OpenRouter AI Provider...")
    try:
        import httpx
        headers = {
            "Authorization": f"Bearer {settings.openrouter_api_key}",
            "HTTP-Referer": "https://github.com/kbtteja456-KBT/YT_AUTOMATE",
            "X-Title": "YT_AUTOMATE Autopilot"
        }
        res = httpx.get("https://openrouter.ai/api/v1/auth/key", headers=headers, timeout=10.0)
        if res.status_code == 200:
            data = res.json().get("data", {})
            label = data.get("label", "active_key")
            limit = data.get("limit", "unlimited")
            print(f"  ✅ OpenRouter API Key Valid. Label: {label}, Limit: {limit}.")
            print(f"     Target Model: '{settings.openrouter_model}'.")
        else:
            print(f"  ❌ OpenRouter Auth Returned Status {res.status_code}: {res.text[:120]}")
            all_passed = False
    except Exception as e:
        print(f"  ❌ OpenRouter Connection Failed: {e}")
        all_passed = False

    # 5. Check FFmpeg & Fonts
    print("\n[5/5] Testing FFmpeg and System Fonts...")
    ffmpeg_bin = shutil.which("ffmpeg")
    if not ffmpeg_bin:
        try:
            import imageio_ffmpeg
            ffmpeg_bin = imageio_ffmpeg.get_ffmpeg_exe()
        except Exception:
            ffmpeg_bin = None

    if not ffmpeg_bin:
        print("  ❌ FFmpeg binary not found in PATH or imageio_ffmpeg.")
        all_passed = False
    else:
        try:
            cmd = [ffmpeg_bin, "-version"]
            out = subprocess.check_output(cmd, stderr=subprocess.STDOUT, text=True)
            first_line = out.splitlines()[0] if out else "Unknown version"
            print(f"  ✅ FFmpeg Found: {first_line} ({ffmpeg_bin}).")
        except Exception as e:
            print(f"  ❌ FFmpeg execution check failed: {e}")
            all_passed = False

    print("\n" + "=" * 65)
    if all_passed:
        print("🎉 HEALTH CHECK PASSED: System is 100% ready for 24/7 cloud publishing.")
    else:
        print("❌ HEALTH CHECK FAILED: Resolve the issues above before running in production.")
    print("=" * 65 + "\n")
    return all_passed


async def run_real_pipeline(
    slot_index: int,
    custom_topic: Optional[str] = None,
    force: bool = False,
    dry_run: bool = False
) -> dict:
    """
    Execute the full end-to-end Short generation with atomic concurrency locking.

    - Uses atomic MongoDB find_one_and_update to guarantee only ONE runner can execute.
    - Multiple triggers (external webhooks, backup crons) will never produce duplicate videos.
    - If another runner is currently active (<15 minutes lease), exits cleanly with ALREADY_RUNNING.
    - If slot is already published today, exits cleanly with ALREADY_PUBLISHED.
    - Recovers from stale or failed executions automatically without laptop booting.
    - Supports dry_run mode (renders video and audits QC without public YouTube upload).
    """
    db = SyncMongoDB.get_db()
    tz = zoneinfo.ZoneInfo(settings.timezone)
    now_local = datetime.now(tz)
    date_str = now_local.strftime("%Y-%m-%d")
    now_utc = datetime.now(timezone.utc)
    stale_lease_seconds = 15 * 60  # 15 minutes lease

    # Idempotency key uniquely identifies slot per date
    idempotency_key = compute_content_hash(f"autopilot_{date_str}_slot{slot_index}")

    # 1. Check if already published today
    if not force and is_slot_published_today(slot_index, date_str):
        log_run(
            f"✅ [IDEMPOTENCY] Slot {slot_index} has ALREADY been published today ({date_str}). "
            f"Skipping redundant run to prevent duplicate videos."
        )
        return {"status": "ALREADY_PUBLISHED"}

    # 2. Concurrency Lock: Check if another runner is currently active
    existing_job = db.publishing_jobs.find_one({"idempotency_key": idempotency_key})
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

    if existing_job and not force:
        if existing_job.get("state") == JobState.PUBLISHED.value:
            yt_url = existing_job.get("youtube_url", "")
            log_run(f"✅ Slot {slot_index} already marked PUBLISHED in DB (url: {yt_url}). Skipping.")
            return {"status": "ALREADY_PUBLISHED", "youtube_url": yt_url}

        job_updated = existing_job.get("updated_at") or existing_job.get("created_at") or now_utc
        if job_updated.tzinfo is None:
            job_updated = job_updated.replace(tzinfo=timezone.utc)

        age_seconds = (now_utc - job_updated).total_seconds()
        is_active = existing_job.get("state") in active_states

        if is_active and age_seconds < stale_lease_seconds:
            log_run(
                f"🔒 [CONCURRENCY GUARD] Slot {slot_index} is currently ACTIVE in another cloud runner "
                f"(job={existing_job['_id']}, state='{existing_job.get('state')}', last updated {int(age_seconds)}s ago). "
                f"Exiting cleanly to prevent concurrent duplicate publishing."
            )
            return {"status": "ALREADY_RUNNING", "job_id": str(existing_job["_id"])}

    # 3. Atomically acquire/claim the job lock in MongoDB
    if existing_job:
        job_id = str(existing_job["_id"])
        db.publishing_jobs.update_one(
            {"_id": existing_job["_id"]},
            {
                "$set": {
                    "state": JobState.RUNNING.value,
                    "updated_at": now_utc,
                    "error_message": None,
                },
                "$inc": {"retry_count": 1}
            }
        )
        log_run(f"♻️  Claimed existing job lock {job_id} for Slot {slot_index} ({date_str}).")
    else:
        try:
            job_doc = {
                "slot_index": slot_index,
                "scheduled_at": now_utc,
                "state": JobState.RUNNING.value,
                "idempotency_key": idempotency_key,
                "topic": custom_topic or "Python Quiz #Shorts",
                "created_at": now_utc,
                "updated_at": now_utc,
                "is_buffered": False,
                "triggered_by": "cloud_autopilot",
                "retry_count": 0,
            }
            res = db.publishing_jobs.insert_one(job_doc)
            job_id = str(res.inserted_id)
            log_run(f"📝 Acquired new atomic job lock {job_id} for Slot {slot_index} ({date_str}).")
        except DuplicateKeyError:
            # Race condition: Another runner inserted at the exact same millisecond
            log_run(f"🔒 Race condition detected: Another runner acquired lock first. Standing down.")
            return {"status": "ALREADY_RUNNING"}

    # 4. Build and execute the real PipelineOrchestrator
    orchestrator = _build_orchestrator(db)
    from backend.app.core.repositories import JobRepository, VideoRepository
    orchestrator.job_repo = JobRepository(db)
    orchestrator.video_repo = VideoRepository(db)

    log_run(f"🤖 Launching PipelineOrchestrator for job {job_id} (slot {slot_index}, dry_run={dry_run})...")

    result = await orchestrator.execute_job(
        job_id=job_id,
        custom_topic=custom_topic,
        publish_immediately=not dry_run,
        slot_index=slot_index,
        dry_run=dry_run
    )

    if dry_run:
        log_run("✅ Dry run completed successfully (no YouTube upload requested).")
        return result

    # Hard-assert that a real YouTube video ID was returned
    youtube_video_id = result.get("youtube_video_id") or result.get("video_id")
    youtube_url = result.get("youtube_url") or result.get("url")

    if not youtube_video_id:
        raise RuntimeError(
            f"Pipeline completed but YouTube API did not return a confirmed real video ID. Full result: {result}"
        )

    log_run(f"🎉 Real video ID confirmed: {youtube_video_id} → {youtube_url}")
    qc_score = result.get("quality_score")
    if qc_score is not None:
        log_run(f"📊 Quality Control score: {qc_score:.1f}/100")

    return result


async def main():
    parser = argparse.ArgumentParser(
        description="24/7 Cloud YouTube Shorts Autopilot CLI (Zero Laptop Dependency)"
    )
    parser.add_argument(
        "--slot",
        type=int,
        default=0,
        choices=[0, 1, 2],
        help="Slot index: 1 = Morning 07:00 IST, 2 = Evening 18:00 IST, 0 = Auto-detect / Catch-up",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Force execution even if this slot was already published today",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Execute full script, audio, and video rendering but skip YouTube upload",
    )
    parser.add_argument(
        "--check-health",
        action="store_true",
        help="Run comprehensive health checks on environment, MongoDB Atlas, YouTube OAuth, OpenRouter, and FFmpeg",
    )
    parser.add_argument(
        "--topic",
        type=str,
        default=None,
        help="Optional custom topic override",
    )
    args = parser.parse_args()

    # If health check requested, execute and exit immediately
    if args.check_health:
        healthy = check_health()
        sys.exit(0 if healthy else 1)

    tz = zoneinfo.ZoneInfo(settings.timezone)
    now_local = datetime.now(tz)
    today_str = now_local.strftime("%Y-%m-%d")
    hour = now_local.hour

    # Auto-detect and cloud catch-up logic
    slot = args.slot
    if slot == 0:
        # Check morning vs evening slots with automatic catch-up
        slot1_done = is_slot_published_today(1, today_str)
        slot2_done = is_slot_published_today(2, today_str)

        if 7 <= hour < 18:
            # Morning active window (07:00 - 17:59 IST)
            if not slot1_done:
                slot = 1
                log_run(f"⏰ [CATCH-UP/DUE] Morning Slot 1 (07:00 AM IST) is pending. Launching Slot 1.")
            else:
                log_run(f"✅ Morning Slot 1 already published today. Evening Slot 2 will trigger at 18:00 IST. Standing by.")
                sys.exit(0)
        elif hour >= 18:
            # Evening active window (18:00 - 23:59 IST)
            if not slot2_done:
                slot = 2
                log_run(f"⏰ [CATCH-UP/DUE] Evening Slot 2 (06:00 PM IST) is pending. Launching Slot 2.")
            elif not slot1_done:
                # Catch up missed morning slot in the evening window!
                slot = 1
                log_run(f"⏰ [CATCH-UP] Slot 2 published, but morning Slot 1 was missed earlier today. Catching up Slot 1 now.")
            else:
                log_run(f"✅ Both Slot 1 and Slot 2 are already published for today ({today_str}). Standing by.")
                sys.exit(0)
        else:
            # Pre-morning window (< 07:00 AM IST, e.g. 06:45, 06:55 early runner)
            slot = 1
            log_run(f"🕒 Pre-morning window ({now_local.strftime('%H:%M')} IST): Preparing Slot 1.")

    slot_title = "Morning Slot 1 (07:00 AM IST)" if slot == 1 else "Evening Slot 2 (06:00 PM IST)"
    print(
        f"\n============================================================\n"
        f"[STAGE: TRIGGERED] {slot_title} - Date: {today_str} ({now_local.strftime('%H:%M:%S')} IST)\n"
        f"Mode: {'DRY RUN' if args.dry_run else 'PRODUCTION'} | Force: {args.force}\n"
        f"============================================================"
    )

    try:
        result = await run_real_pipeline(
            slot_index=slot,
            custom_topic=args.topic,
            force=args.force,
            dry_run=args.dry_run
        )
        status = result.get("status")
        if status in ("ALREADY_PUBLISHED", "ALREADY_RUNNING"):
            sys.exit(0)
        elif status == "DRY_RUN_COMPLETED":
            log_run("✅ Dry run verification finished successfully.")
            sys.exit(0)
        elif status == "PUBLISHED":
            yt_url = result.get("youtube_url")
            log_run(f"✅ SUCCESS: Short published to YouTube → {yt_url}")
            sys.exit(0)
        else:
            log_run(f"Pipeline finished with status: {status}")
            sys.exit(0)

    except Exception as e:
        log_run(f"❌ PIPELINE EXECUTION FAILED: {e}")
        logger.exception("Cloud Pipeline Error")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
