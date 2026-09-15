import sys
import os
import json
from datetime import datetime, timezone
from bson import ObjectId

sys.path.insert(0, r"c:\Users\DELL\OneDrive\Desktop\yt")
from backend.app.core.db import SyncMongoDB
from backend.app.config import settings

def default_json(obj):
    if isinstance(obj, (datetime,)):
        return obj.isoformat()
    if isinstance(obj, ObjectId):
        return str(obj)
    return str(obj)

def inspect():
    db = SyncMongoDB.get_db()
    print("=== DATABASE INFO ===")
    print("Database Name:", db.name)
    print("Collections:", db.list_collection_names())
    print()

    print("=== USERS ===")
    users = list(db.users.find({}))
    print(f"Total Users: {len(users)}")
    for u in users:
        print(f"User: id={u.get('_id')}, email={u.get('email')}, is_owner={u.get('is_owner')}, active={u.get('is_active')}, default_ws={u.get('default_workspace_id')}")
    print()

    print("=== WORKSPACES ===")
    workspaces = list(db.workspaces.find({}))
    print(f"Total Workspaces: {len(workspaces)}")
    for ws in workspaces:
        print(f"Workspace: id={ws.get('_id')}, name={ws.get('name')}, slug={ws.get('slug')}, owner_id={ws.get('owner_id')}, autopilot_enabled={ws.get('autopilot_enabled')}, connected_channel_id={ws.get('connected_channel_id')}, niche={ws.get('niche')}")
    print()

    print("=== CHANNELS ===")
    channels = list(db.channels.find({}))
    print(f"Total Channels: {len(channels)}")
    for ch in channels:
        print(f"Channel: id={ch.get('_id')}, workspace_id={ch.get('workspace_id')}, channel_id={ch.get('channel_id')}, title={ch.get('title')}, is_active={ch.get('is_active')}")
    print()

    print("=== OAUTH TOKENS ===")
    tokens = list(db.oauth_tokens.find({}))
    print(f"Total Tokens: {len(tokens)}")
    for t in tokens:
        print(f"Token: id={t.get('_id')}, workspace_id={t.get('workspace_id')}, channel_id={t.get('channel_id')}, token_type={t.get('token_type')}, has_refresh={bool(t.get('refresh_token'))}, expires_at={t.get('expires_at')}")
    print()

    print("=== PUBLISHING JOBS ===")
    jobs = list(db.publishing_jobs.find({}).sort("created_at", -1))
    print(f"Total Publishing Jobs: {len(jobs)}")
    for j in jobs[:20]:
        print(f"Job: id={j.get('_id')}, video_id={j.get('video_id')}, channel_id={j.get('channel_id')}, state={j.get('state')}, scheduled_at={j.get('scheduled_at')}, error={j.get('error') or j.get('error_message')}")
    print()

    print("=== VIDEOS ===")
    videos = list(db.videos.find({}).sort("created_at", -1))
    print(f"Total Videos: {len(videos)}")
    for v in videos:
        print(f"Video: id={v.get('_id')}, workspace_id={v.get('workspace_id')}, title={v.get('title')}")
        print(f"   status={v.get('status')}, youtube_video_id={v.get('youtube_video_id')}, youtube_url={v.get('youtube_url')}, published_at={v.get('youtube_published_at')}")
        print(f"   file_path={v.get('file_path')}, file_exists={os.path.exists(v.get('file_path')) if v.get('file_path') else False}")
        print(f"   created_at={v.get('created_at')}")
        print("-" * 50)

if __name__ == "__main__":
    inspect()
