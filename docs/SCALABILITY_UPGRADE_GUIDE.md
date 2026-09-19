# Scalability Upgrade Guide (100–200+ Users)

This document provides a step-by-step upgrade plan with exact file names, functions, and code changes to scale the YouTube Autopilot platform smoothly to 100–200+ users.

---

## 📁 Summary of Files to Modify

| Step | File Path | Function / Section | Purpose |
| :--- | :--- | :--- | :--- |
| **Step 1** | `backend/app/core/cron_scheduler.py` | `process_tenant_workspaces_for_slot` | 3x Parallel Concurrency Pool (`asyncio.Semaphore`) |
| **Step 2** | `backend/app/core/cron_scheduler.py` | `_scheduler_loop` | Overnight Pre-Generation (01:00–06:30 AM) |
| **Step 3** | `backend/app/core/cron_scheduler.py` | `cleanup_old_published_media` | Auto-delete rendered MP4 files older than 3 days |
| **Step 4** | *Google Cloud Console* | YouTube Data API v3 Quotas | Submit free quota increase form for >6 uploads/day |

---

## 🛠️ Step 1: Add 3x Concurrency Pool to Tenant Pipeline

**File**: `backend/app/core/cron_scheduler.py`  
**Function**: `process_tenant_workspaces_for_slot`

### Why This is Needed:
Currently, tenant video generation runs one by one in a sequential loop (`for ws in tenants:`). For 200 users, sequential execution (1.5 minutes per video) takes ~5 hours. Adding an `asyncio.Semaphore(3)` renders 3 videos concurrently, cutting generation time down to ~45–60 minutes.

### Exact Code Change:

Find `process_tenant_workspaces_for_slot` (around line 395) and replace the sequential `for ws in tenants:` loop with:

```python
        # Concurrency limit: Render up to 3 videos simultaneously across CPU cores
        sem = asyncio.Semaphore(3)

        async def _process_single_tenant(ws: dict):
            async with sem:
                ws_id = str(ws["_id"])
                ws_name = ws.get("name", "Tenant Workspace")
                try:
                    # 1. Connected YouTube channel check
                    chan = db.youtube_channels.find_one({"workspace_id": ws_id, "is_active": True}) or db.youtube_channels.find_one({"workspace_id": ws_id})
                    if not chan:
                        return

                    tok = db.oauth_tokens.find_one({"workspace_id": ws_id}) or db.oauth_tokens.find_one({"channel_id": chan["channel_id"]})
                    if not tok or not (tok.get("encrypted_refresh_token") or tok.get("refresh_token")):
                        return

                    # 1b. Pre-flight credential verification (100ms)
                    try:
                        from backend.app.models.channel import OAuthTokenRecord
                        from backend.app.core.oauth import GoogleOAuthManager
                        from google.auth.transport.requests import Request
                        rec = OAuthTokenRecord.model_validate(tok)
                        rf = rec.get_refresh_token()
                        acc = rec.get_access_token()
                        creds = GoogleOAuthManager.get_google_credentials(acc, rf)
                        creds.refresh(Request())
                    except Exception as tok_err:
                        err_str = str(tok_err).lower()
                        if "invalid_grant" in err_str or "expired or revoked" in err_str:
                            logger.warning(f"⚠️ [Tenant Autopilot] '{ws_name}' OAuth expired. Skipping.")
                            db.youtube_channels.update_one(
                                {"_id": chan["_id"]},
                                {"$set": {"is_active": False, "error_message": "YouTube token expired. Please reconnect in Settings."}}
                            )
                            return

                    # 2. Already published today check
                    if is_slot_published_today(slot_index, today_str, workspace_id=ws_id):
                        return

                    # 3. Check trial quota or BYOK key
                    can_gen, reason = can_workspace_generate_sync(ws_id)
                    if not can_gen:
                        logger.info(f"[Tenant Autopilot] '{ws_name}' cannot generate: {reason}")
                        return

                    # 4. Execute pipeline
                    logger.info(f"🚀 [Tenant Autopilot] Launching Slot {slot_index} for '{ws_name}'")
                    res = await execute_slot_pipeline(slot_index=slot_index, workspace_id=ws_id)
                    logger.info(f"✅ [Tenant Autopilot] Completed Slot {slot_index} for '{ws_name}': {res.get('status')}")

                except Exception as ws_err:
                    logger.error(f"[Tenant Autopilot] Failed for workspace '{ws_name}': {ws_err}", exc_info=True)

        # Launch all active tenants bounded by the 3x concurrency semaphore
        tasks = [_process_single_tenant(ws) for ws in tenants]
        await asyncio.gather(*tasks, return_exceptions=True)
```

---

## 🛠️ Step 2: Add Overnight Pre-Generation (01:00 AM – 06:30 AM)

**File**: `backend/app/core/cron_scheduler.py`  
**Function**: `_scheduler_loop`

### Why This is Needed:
If 200 users expect videos published at 07:00 AM, you should NOT start generating videos from scratch at 07:00 AM. Pre-generating them overnight between 01:00 AM and 06:30 AM leaves all MP4 files pre-rendered in `READY` status on disk. At 07:00 AM, the scheduler runs the **3-second Fast-Path upload**, publishing all 200 videos in minutes without CPU spikes.

### Exact Code Change:

Inside `_scheduler_loop()`, find the hour checks and add the overnight pre-gen block:

```python
            # Overnight Pre-Generation Window: 01:00 AM - 06:30 AM IST
            # Pre-renders morning slot videos into READY state so 07:00 AM upload takes only ~3 seconds
            if 1 <= hour < 7:
                if not _is_tenant_processing:
                    # Run slot 1 pre-generation (pipeline renders video, leaves READY, skips upload until 07:00)
                    asyncio.create_task(process_tenant_workspaces_for_slot(1, today_str))

            # Morning Slot (Slot 1): Target 07:00 AM IST
            elif 7 <= hour < 18:
                if not is_slot_published_today(1, today_str) and not _is_pipeline_running:
                    logger.info(f"⏰ [Autopilot Scheduler] Slot 1 (07:00 AM) due for {today_str}. Launching Owner Pipeline...")
                    asyncio.create_task(run_slot_with_lock(1))
                if not _is_tenant_processing:
                    asyncio.create_task(process_tenant_workspaces_for_slot(1, today_str))

            # Evening Slot (Slot 2): Target 06:00 PM (18:00) IST
            elif 18 <= hour <= 23:
                if not is_slot_published_today(2, today_str) and not _is_pipeline_running:
                    logger.info(f"⏰ [Autopilot Scheduler] Slot 2 (06:00 PM) due for {today_str}. Launching Owner Pipeline...")
                    asyncio.create_task(run_slot_with_lock(2))
                if not _is_tenant_processing:
                    asyncio.create_task(process_tenant_workspaces_for_slot(2, today_str))
```

---

## 🛠️ Step 3: Add Automatic Disk Cleanup for Old Published Videos

**File**: `backend/app/core/cron_scheduler.py`

### Why This is Needed:
200 users × 2 videos/day = 400 MP4 files/day (~4 GB per day). After 1 month, that is 120 GB of disk space. A cleanup function automatically deletes local MP4 and ASS files that are **older than 3 days and confirmed as `PUBLISHED`** to YouTube.

### Exact Code to Add:

Add this function to `backend/app/core/cron_scheduler.py`:

```python
def cleanup_old_published_media(days_to_keep: int = 3):
    """Auto-delete local rendered video and caption files older than N days for published videos."""
    try:
        from datetime import timedelta
        from pathlib import Path
        from backend.app.core.db import SyncMongoDB
        db = SyncMongoDB.get_db()

        cutoff = datetime.now(timezone.utc) - timedelta(days=days_to_keep)
        published_videos = db.videos.find({
            "status": "PUBLISHED",
            "created_at": {"$lt": cutoff}
        })

        purged_count = 0
        for vid in published_videos:
            for key in ("file_path", "thumbnail_path"):
                p_str = vid.get(key)
                if p_str:
                    p = Path(p_str)
                    if p.exists():
                        p.unlink(missing_ok=True)
                        purged_count += 1

        if purged_count > 0:
            logger.info(f"🧹 [Auto-Cleanup] Purged {purged_count} published media files older than {days_to_keep} days.")
    except Exception as e:
        logger.warning(f"[Auto-Cleanup] Media purge warning: {e}")
```

Call it once daily inside `_scheduler_loop()`:
```python
            # Run cleanup once per day around midnight (00:00 - 01:00)
            if hour == 0 and sweep_counter % 60 == 0:
                cleanup_old_published_media(days_to_keep=3)
```

---

## 🛠️ Step 4: YouTube API Quota Expansion (Google's 10,000 Limit)

### Why This is Needed:
By default, Google grants each Google Cloud project **10,000 quota units per day**.  
Uploading 1 YouTube Short costs **1,600 units**.  
`10,000 ÷ 1,600 = 6 videos per day maximum` on a shared default project.

### Step-by-Step Instructions to Request Increase:
1. Go to [Google Cloud Console](https://console.cloud.google.com/).
2. Select your Project (`youtube-automation` or your active project).
3. Navigate to **APIs & Services** → **YouTube Data API v3** → **Quotas & System Limits**.
4. Click **Edit Quota** or visit Google's [YouTube API Services - Audit and Quota Extension Form](https://support.google.com/youtube/contact/yt_api_form).
5. Fill in:
   * **Project Number**: (from your Google Cloud Dashboard).
   * **Requested Quota**: `200,000` to `500,000` units/day (enough for 100–300 daily uploads).
   * **Justification**: "Automated educational and documentary Short creator platform for multiple registered student and creator channels."
   * **Link to demo video / terms**: Link to your app's privacy policy and terms.
6. Google usually approves quota increases within **2–3 business days for free**.

---

## 🛡️ Permanent Golden Rule
> **Do not modify the Platform Owner's pipeline.**  
> The Owner channel (`Python Master` / `is_legacy_default: True`) must strictly remain on `quiz_card` format rendering Python quiz cards. All multi-tenant concurrency and format detection features strictly run on `is_legacy_default: False` workspaces.
