import sys, os
from datetime import datetime, timezone
import zoneinfo

sys.path.insert(0, r"c:\Users\DELL\OneDrive\Desktop\yt")
from backend.app.core.db import SyncMongoDB

db = SyncMongoDB.get_db()
tz = zoneinfo.ZoneInfo("Asia/Kolkata")
now = datetime.now(tz)
start_of_today = datetime(now.year, now.month, now.day, tzinfo=tz).astimezone(timezone.utc)

print(f"=== AUDIT FOR TODAY: {now.strftime('%Y-%m-%d')} (Asia/Kolkata) ===")
jobs = list(db.publishing_jobs.find({"created_at": {"$gte": start_of_today}}).sort("created_at", 1))
print(f"Total Jobs Created Today: {len(jobs)}")
for j in jobs:
    ws = db.workspaces.find_one({"_id": j.get("workspace_id")}) if j.get("workspace_id") else None
    owner = db.users.find_one({"_id": ws["owner_id"]}) if ws and ws.get("owner_id") else None
    print(f"Job: {j.get('_id')} | State: {j.get('state')} | Scheduled: {j.get('scheduled_at')} | WS: {ws.get('name') if ws else 'Owner/Default'} ({owner.get('email') if owner else 'Owner'}) | Err: {j.get('error') or j.get('error_message')}")

videos = list(db.videos.find({"created_at": {"$gte": start_of_today}}).sort("created_at", 1))
print(f"\nTotal Videos Created Today: {len(videos)}")
for v in videos:
    ws = db.workspaces.find_one({"_id": v.get("workspace_id")}) if v.get("workspace_id") else None
    owner = db.users.find_one({"_id": ws["owner_id"]}) if ws and ws.get("owner_id") else None
    print(f"Video: {v.get('_id')} | Title: {v.get('title')} | Status: {v.get('status')} | YT ID: {v.get('youtube_video_id')} | WS: {ws.get('name') if ws else 'Owner/Default'} ({owner.get('email') if owner else 'Owner'})")

print("\n=== USERS & WORKSPACES CONFIG ===")
workspaces = list(db.workspaces.find({}))
for ws in workspaces:
    owner = db.users.find_one({"_id": ws.get("owner_id")})
    print(f"WS: {ws.get('name')} | Autopilot: {ws.get('autopilot_enabled')} | Channel: {ws.get('connected_channel_id')} | Owner: {owner.get('email') if owner else 'None'} ({'OWNER' if owner and owner.get('is_owner') else 'USER'})")
