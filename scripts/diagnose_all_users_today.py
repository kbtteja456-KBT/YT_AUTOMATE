import sys, os
from datetime import datetime, timezone
import zoneinfo

sys.path.insert(0, r"c:\Users\DELL\OneDrive\Desktop\yt")
from backend.app.core.db import SyncMongoDB
from backend.app.core.cron_scheduler import is_slot_published_today
from backend.app.core.ledger import can_workspace_generate_sync

db = SyncMongoDB.get_db()
tz = zoneinfo.ZoneInfo("Asia/Kolkata")
now = datetime.now(tz)
today_str = now.strftime("%Y-%m-%d")
start_of_today = datetime(now.year, now.month, now.day, tzinfo=tz).astimezone(timezone.utc)

users = list(db.users.find({}))
workspaces = list(db.workspaces.find({}))
jobs_today = list(db.publishing_jobs.find({"created_at": {"$gte": start_of_today}}))
videos_today = list(db.videos.find({"created_at": {"$gte": start_of_today}}))

print("================================================================================")
print(f"DIAGNOSTIC REPORT FOR ALL USERS AND OWNERS — {today_str} ({now.strftime('%H:%M:%S')} IST)")
print("================================================================================\n")

for u in users:
    u_id = str(u["_id"])
    email = u.get("email")
    is_owner = u.get("is_owner", False)
    role_str = "PLATFORM OWNER" if is_owner else "USER"
    
    print(f"[{role_str}] {email} (User ID: {u_id})")
    
    # Workspaces for this user
    user_ws = [w for w in workspaces if str(w.get("owner_id")) == u_id or (is_owner and w.get("is_legacy_default"))]
    if not user_ws:
        print("  ❌ No workspaces found.\n")
        continue
        
    for ws in user_ws:
        ws_id = str(ws["_id"])
        ws_name = ws.get("name")
        autopilot_enabled = ws.get("autopilot_enabled", False)
        is_legacy = ws.get("is_legacy_default", False)
        niche = ws.get("niche")
        
        # Channels and tokens
        chan = db.youtube_channels.find_one({"workspace_id": ws_id}) or (db.youtube_channels.find_one({"is_active": True}) if is_legacy else None)
        tok = db.oauth_tokens.find_one({"workspace_id": ws_id}) or (db.oauth_tokens.find_one({"channel_id": chan["channel_id"]}) if chan else None)
        has_token = bool(tok and (tok.get("encrypted_refresh_token") or tok.get("refresh_token")))
        
        # Quota check
        if is_legacy:
            can_gen, gen_reason = True, "Owner unlimited"
        else:
            can_gen, gen_reason = can_workspace_generate_sync(ws_id)
            
        # Slot status
        slot1_published = is_slot_published_today(1, today_str, workspace_id=None if is_legacy else ws_id)
        slot2_published = is_slot_published_today(2, today_str, workspace_id=None if is_legacy else ws_id)
        
        # Videos today for this workspace
        ws_vids_today = [v for v in videos_today if str(v.get("workspace_id")) == ws_id or (is_legacy and (not v.get("workspace_id") or str(v.get("workspace_id")) == ws_id))]
        
        # Jobs today for this workspace
        ws_jobs_today = [j for j in jobs_today if str(j.get("workspace_id")) == ws_id or (is_legacy and (not j.get("workspace_id") or str(j.get("workspace_id")) == ws_id))]
        
        print(f"  * Workspace: '{ws_name}' (ID: {ws_id})")
        print(f"    - Legacy/Owner Default: {is_legacy}")
        print(f"    - Autopilot Enabled: {autopilot_enabled}")
        print(f"    - Channel: {chan.get('channel_title') if chan else 'None'} ({chan.get('channel_id') if chan else 'No channel'})")
        print(f"    - OAuth Token: {'Valid & Decryptable' if has_token else 'Missing / Invalid'}")
        print(f"    - Quota Status: {'Allowed' if can_gen else 'BLOCKED'} ({gen_reason})")
        print(f"    - Slot 1 (07:00 AM IST): {'✅ PUBLISHED' if slot1_published else '❌ NOT PUBLISHED'}")
        print(f"    - Slot 2 (06:00 PM IST): {'✅ PUBLISHED' if slot2_published else '❌ NOT PUBLISHED'}")
        print(f"    - Videos Today: {len(ws_vids_today)}")
        for v in ws_vids_today:
            print(f"        • [{v.get('status')}] {v.get('title')} -> {v.get('youtube_url')}")
        print(f"    - Jobs Today: {len(ws_jobs_today)}")
        for j in ws_jobs_today:
            print(f"        • [Job {j.get('_id')}] State: {j.get('state')}, Error: {j.get('error') or j.get('error_message')}")
        
        # Why not published?
        reasons = []
        if not slot1_published or not slot2_published:
            if not autopilot_enabled:
                reasons.append("Autopilot toggle is turned OFF for this workspace.")
            if not chan:
                reasons.append("No YouTube channel connected.")
            if not has_token:
                reasons.append("Missing YouTube OAuth refresh token.")
            if not can_gen:
                reasons.append(f"Quota / Ledger blocked: {gen_reason}")
        if reasons:
            print(f"    ⚠️ REASONS FOR UNPOSTED SLOTS:")
            for r in reasons:
                print(f"       - {r}")
        print()
