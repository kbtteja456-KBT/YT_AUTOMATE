import sys, os
from datetime import datetime, timezone
sys.path.insert(0, r"c:\Users\DELL\OneDrive\Desktop\yt")
from backend.app.core.db import SyncMongoDB

db = SyncMongoDB.get_db()

today_start = datetime(2026, 9, 15, 0, 0, 0)
today_jobs = list(db.publishing_jobs.find({"created_at": {"$gte": today_start}}).sort("created_at", 1))

print(f"=== JOBS CREATED ON 2026-09-15 (TOTAL: {len(today_jobs)}) ===")
for j in today_jobs:
    ws_id = j.get("workspace_id")
    ws = db.workspaces.find_one({"_id": ws_id}) if ws_id else None
    owner = db.users.find_one({"_id": ws["owner_id"]}) if ws and ws.get("owner_id") else None
    print(f"\nJob ID: {j['_id']}")
    print(f"  Workspace: {ws.get('name') if ws else j.get('workspace_id')} (Owner: {owner.get('email') if owner else 'None'})")
    print(f"  Channel ID: {j.get('channel_id')}")
    print(f"  State: {j.get('state')}")
    print(f"  Scheduled: {j.get('scheduled_at')}")
    print(f"  Video ID: {j.get('video_id')}")
    print(f"  Error: {j.get('error') or j.get('error_message')}")
    
    # check video details
    v = None
    if j.get("video_id"):
        v = db.videos.find_one({"_id": j.get("video_id")})
    if not v:
        v = db.videos.find_one({"job_id": str(j["_id"])})
    if v:
        print(f"  -> Associated Video: {v['_id']}")
        print(f"     Title: {v.get('title')}")
        print(f"     Status: {v.get('status')}")
        print(f"     YT ID: {v.get('youtube_video_id')}")
        print(f"     File: {v.get('file_path')} (Exists: {os.path.exists(v.get('file_path')) if v.get('file_path') else False})")

today_videos = list(db.videos.find({"created_at": {"$gte": today_start}}).sort("created_at", 1))
print(f"\n=== VIDEOS CREATED ON 2026-09-15 (TOTAL: {len(today_videos)}) ===")
for v in today_videos:
    ws = db.workspaces.find_one({"_id": v.get("workspace_id")}) if v.get("workspace_id") else None
    owner = db.users.find_one({"_id": ws["owner_id"]}) if ws and ws.get("owner_id") else None
    print(f"\nVideo: {v['_id']}")
    print(f"  Title: {v.get('title')}")
    print(f"  Workspace: {ws.get('name') if ws else v.get('workspace_id')} ({owner.get('email') if owner else 'None'})")
    print(f"  Status: {v.get('status')}")
    print(f"  YT ID: {v.get('youtube_video_id')}")
    print(f"  YT URL: {v.get('youtube_url')}")
    print(f"  File: {v.get('file_path')} (Exists: {os.path.exists(v.get('file_path')) if v.get('file_path') else False})")
