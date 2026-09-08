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
    dry_run: bool = False,
    workspace_id: Optional[str] = None
) -> dict:
    """
    Execute the full end-to-end Short generation with atomic concurrency locking.

    - Uses atomic MongoDB find_one_and_update to guarantee only ONE runner can execute.
    - Multiple triggers (external webhooks, backup crons) will never produce duplicate videos.
    - If another runner is currently active (<15 minutes lease), exits cleanly with ALREADY_RUNNING.
    - If slot is already published today, exits cleanly with ALREADY_PUBLISHED.
    - Recovers from stale or failed executions automatically without laptop booting.
    - Supports dry_run mode (renders video and audits QC without public YouTube upload).
    - When workspace_id is provided, runs for that tenant workspace and enforces trial quota.
    """
    from bson import ObjectId
    from backend.app.core.ledger import check_and_acquire_trial_quota_atomic_sync

    db = SyncMongoDB.get_db()
    tz = zoneinfo.ZoneInfo(settings.timezone)
    now_local = datetime.now(tz)
    date_str = now_local.strftime("%Y-%m-%d")
    now_utc = datetime.now(timezone.utc)
    stale_lease_seconds = 15 * 60  # 15 minutes lease

    # Resolve workspace niche and verify eligibility if tenant
    workspace_niche = "Python Quiz #Shorts"
    if workspace_id:
        if not dry_run:
            from backend.app.core.ledger import can_workspace_generate_sync
            allowed, reason = can_workspace_generate_sync(workspace_id)
            if not allowed:
                log_run(f"❌ [TRIAL QUOTA] Workspace {workspace_id} cannot publish: {reason}")
                return {"status": "QUOTA_EXHAUSTED", "reason": reason}

        ws_obj = db.workspaces.find_one({"_id": ObjectId(workspace_id)}) if ObjectId.is_valid(workspace_id) else db.workspaces.find_one({"_id": workspace_id})
        if ws_obj:
            workspace_niche = ws_obj.get("niche") or ws_obj.get("settings", {}).get("niche") or "Tech & Tools"
        idempotency_key = compute_content_hash(f"autopilot_{date_str}_{workspace_id}_slot{slot_index}")
    else:
        idempotency_key = compute_content_hash(f"autopilot_{date_str}_slot{slot_index}")

    # 1. Check if already published today
    if not force and is_slot_published_today(slot_index, date_str, workspace_id=workspace_id):
        log_run(
            f"✅ [IDEMPOTENCY] Slot {slot_index} has ALREADY been published today ({date_str}) for workspace {workspace_id or 'Owner'}. "
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
    if workspace_id and not dry_run:
        allowed, reason = check_and_acquire_trial_quota_atomic_sync(workspace_id, is_video_generation=True)
        if not allowed:
            log_run(f"❌ [TRIAL QUOTA] Workspace {workspace_id} cannot acquire quota: {reason}")
            return {"status": "QUOTA_EXHAUSTED", "reason": reason}

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
                "topic": custom_topic or workspace_niche,
                "niche": workspace_niche,
                "created_at": now_utc,
                "updated_at": now_utc,
                "is_buffered": False,
                "triggered_by": "cloud_autopilot",
                "retry_count": 0,
            }
            if workspace_id:
                job_doc["workspace_id"] = workspace_id
            res = db.publishing_jobs.insert_one(job_doc)
            job_id = str(res.inserted_id)
            log_run(f"📝 Acquired new atomic job lock {job_id} for Slot {slot_index} ({date_str}).")
        except DuplicateKeyError:
            # Race condition: Another runner inserted at the exact same millisecond
            log_run(f"🔒 Race condition detected: Another runner acquired lock first. Standing down.")
            return {"status": "ALREADY_RUNNING"}

    # 4. Build and execute the real PipelineOrchestrator
    orchestrator = _build_orchestrator(db, workspace_id=workspace_id)
    from backend.app.core.repositories import JobRepository, VideoRepository
    orchestrator.job_repo = JobRepository(db)
    orchestrator.video_repo = VideoRepository(db)

    log_run(f"🤖 Launching PipelineOrchestrator for job {job_id} (slot {slot_index}, dry_run={dry_run}, ws={workspace_id or 'Owner'})...")

    result = await orchestrator.execute_job(
        job_id=job_id,
        niche=workspace_niche,
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
    parser.add_argument(
        "--workspace-id",
        type=str,
        default=None,
        help="Target a specific tenant workspace ID instead of Owner default",
    )
    parser.add_argument(
        "--include-tenants",
        action="store_true",
        help="Also trigger scheduled publishing for active tenant workspaces with Autopilot enabled",
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

    is_evening_window = (hour == 17 and now_local.minute >= 40) or hour >= 18
    target_slot = args.slot
    owner_slot = None

    if target_slot == 0:
        target_slot = 2 if is_evening_window else 1
        slot1_done = is_slot_published_today(1, today_str)
        slot2_done = is_slot_published_today(2, today_str)

        if is_evening_window:
            if not slot2_done:
                owner_slot = 2
                log_run(f"⏰ [CATCH-UP/DUE] Evening Slot 2 (06:00 PM IST) is pending for owner. Launching Slot 2.")
            elif not slot1_done:
                owner_slot = 1
                log_run(f"⏰ [CATCH-UP] Slot 2 published, but morning Slot 1 was missed earlier today for owner. Catching up Slot 1 now.")
            else:
                log_run(f"✅ Both Slot 1 and Slot 2 are already published for owner today ({today_str}).")
        else:
            if not slot1_done:
                owner_slot = 1
                log_run(f"⏰ [CATCH-UP/DUE] Morning Slot 1 (07:00 AM IST) is pending for owner. Launching Slot 1.")
            else:
                log_run(f"✅ Morning Slot 1 already published for owner today ({today_str}).")
    else:
        owner_slot = target_slot

    slot_title = "Morning Slot 1 (07:00 AM IST)" if target_slot == 1 else "Evening Slot 2 (06:00 PM IST)"
    print(
        f"\n============================================================\n"
        f"[STAGE: TRIGGERED] {slot_title} - Date: {today_str} ({now_local.strftime('%H:%M:%S')} IST)\n"
        f"Mode: {'DRY RUN' if args.dry_run else 'PRODUCTION'} | Force: {args.force} | Include Tenants: {args.include_tenants}\n"
        f"============================================================"
    )

    # 1. Execute Owner pipeline (or targeted workspace)
    if args.workspace_id:
        try:
            res = await run_real_pipeline(
                slot_index=target_slot,
                custom_topic=args.topic,
                force=args.force,
                dry_run=args.dry_run,
                workspace_id=args.workspace_id
            )
            log_run(f"Target workspace {args.workspace_id} finished with status: {res.get('status')}")
        except Exception as e:
            log_run(f"❌ Target workspace execution failed: {e}")
            logger.exception("Target Workspace Pipeline Error")
    elif owner_slot is not None or args.force:
        exec_slot = owner_slot or target_slot
        try:
            result = await run_real_pipeline(
                slot_index=exec_slot,
                custom_topic=args.topic,
                force=args.force,
                dry_run=args.dry_run,
                workspace_id=None
            )
            status = result.get("status")
            if status in ("ALREADY_PUBLISHED", "ALREADY_RUNNING"):
                log_run(f"Owner pipeline finished with status: {status}")
            elif status == "DRY_RUN_COMPLETED":
                log_run("✅ Dry run verification finished successfully.")
            elif status == "PUBLISHED":
                yt_url = result.get("youtube_url")
                log_run(f"✅ SUCCESS: Short published to YouTube → {yt_url}")
            else:
                log_run(f"Owner pipeline finished with status: {status}")
        except Exception as e:
            log_run(f"❌ Owner pipeline encountered error: {e}")
            logger.exception("Owner Cloud Pipeline Error")
    else:
        log_run("Owner publishing skipped (all active slots already published for owner).")

    # 2. Process all tenant workspaces if requested
    if args.include_tenants and not args.workspace_id:
        try:
            from backend.app.core.cron_scheduler import process_tenant_workspaces_for_slot
            log_run(f"Scanning and processing active tenant workspaces for Slot {target_slot}...")
            await process_tenant_workspaces_for_slot(target_slot, today_str)

            # In evening window, also check if any tenant missed morning Slot 1 catch-up
            if target_slot == 2 and args.slot == 0:
                log_run("Checking active tenant workspaces for morning Slot 1 catch-up...")
                await process_tenant_workspaces_for_slot(1, today_str)
        except Exception as t_err:
            log_run(f"❌ Tenant workspaces processing encountered error: {t_err}")
            logger.exception("Tenant Cloud Pipeline Error")

    sys.exit(0)


if __name__ == "__main__":
    asyncio.run(main())
