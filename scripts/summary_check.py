import sys, os
sys.path.insert(0, r"c:\Users\DELL\OneDrive\Desktop\yt")
from backend.app.core.db import SyncMongoDB

db = SyncMongoDB.get_db()

users = list(db.users.find({}))
workspaces = list(db.workspaces.find({}))
channels = list(db.channels.find({}))
tokens = list(db.oauth_tokens.find({}))
videos = list(db.videos.find({}))

print(f"Total Users: {len(users)}")
for u in users:
    print(f"User: id={u['_id']}, email={u.get('email')}, is_owner={u.get('is_owner')}, default_ws={u.get('default_workspace_id')}")

print(f"\nTotal Workspaces: {len(workspaces)}")
for w in workspaces:
    print(f"WS: id={w['_id']}, name={w.get('name')}, owner_id={w.get('owner_id')}, autopilot={w.get('autopilot_enabled')}, ch_id={w.get('connected_channel_id')}")

print(f"\nTotal Channels: {len(channels)}")
for c in channels:
    print(f"CH: id={c.get('channel_id')}, title={c.get('title')}, ws_id={c.get('workspace_id')}")

print(f"\nTotal Tokens: {len(tokens)}")
for t in tokens:
    print(f"Token: ch_id={t.get('channel_id')}, ws_id={t.get('workspace_id')}, expiry={t.get('token_expiry')}")

print(f"\nTotal Videos: {len(videos)}")
for v in videos:
    fname = os.path.basename(v.get("file_path")) if v.get("file_path") else "None"
    exists = os.path.exists(v.get("file_path")) if v.get("file_path") else False
    print(f"VID: id={v['_id']}, ws_id={v.get('workspace_id')}, status={v.get('status')}, yt_id={v.get('youtube_video_id')}, file_exists={exists}, title={repr(v.get('title'))}")
