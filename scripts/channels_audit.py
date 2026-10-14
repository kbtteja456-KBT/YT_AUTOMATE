import sys
from bson import ObjectId
sys.path.insert(0, r"c:\Users\DELL\OneDrive\Desktop\yt")
from backend.app.core.db import SyncMongoDB
from backend.app.core.cron_scheduler import is_slot_published_today
from datetime import datetime, timezone
import zoneinfo

db = SyncMongoDB.get_db()
tz = zoneinfo.ZoneInfo("Asia/Kolkata")
now = datetime.now(tz)
today_str = now.strftime("%Y-%m-%d")

workspaces = list(db.workspaces.find({}))
print(f"=== CHANNELS & WORKSPACES AUDIT ({today_str}) ===")
for ws in workspaces:
    ws_id = str(ws["_id"])
    chan = db.youtube_channels.find_one({"workspace_id": ws_id})
    token = db.oauth_tokens.find_one({"workspace_id": ws_id}) or (db.oauth_tokens.find_one({"channel_id": chan["channel_id"]}) if chan else None)
    vids = list(db.videos.find({"workspace_id": ws["_id"]}))
    if not vids and ws.get("is_legacy_default"):
        vids = list(db.videos.find({"workspace_id": {"$in": [None, ws["_id"]]}}))
    pub_vids = [v for v in vids if v.get("status") == "PUBLISHED" and v.get("youtube_video_id")]
    pending_vids = [v for v in vids if v.get("status") != "PUBLISHED"]
    
    is_owner = ws.get("is_legacy_default") or (not ws.get("owner_id"))
    s1 = is_slot_published_today(1, today_str, workspace_id=(None if is_owner else ws_id))
    s2 = is_slot_published_today(2, today_str, workspace_id=(None if is_owner else ws_id))
    
    print(f"\nWorkspace: '{ws.get('name')}' (ID: {ws_id})")
    print(f"  Autopilot: {ws.get('autopilot_enabled')} | Legacy Default (Owner): {ws.get('is_legacy_default')}")
    print(f"  Channel: {chan.get('channel_title') if chan else 'No channel'} (ID: {chan.get('channel_id') if chan else 'N/A'}) | Active: {chan.get('is_active') if chan else 'N/A'}")
    print(f"  Token in DB: {bool(token)}")
    print(f"  Total Videos: {len(vids)} (Published: {len(pub_vids)}, Unpublished/Pending: {len(pending_vids)})")
    print(f"  Today Slot 1 (07:00 AM) Published: {s1}")
    print(f"  Today Slot 2 (06:00 PM) Published: {s2}")
    if pending_vids:
        print("  Unpublished videos:")
        for pv in pending_vids:
            print(f"    - ID: {pv.get('_id')} | Title: {pv.get('title')} | Status: {pv.get('status')}")
