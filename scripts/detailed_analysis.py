import sys
import os
from datetime import datetime, timezone
from bson import ObjectId

sys.path.insert(0, r"c:\Users\DELL\OneDrive\Desktop\yt")
from backend.app.core.db import SyncMongoDB

def analyze():
    db = SyncMongoDB.get_db()
    
    users = {str(u["_id"]): u for u in db.users.find({})}
    workspaces = {str(w["_id"]): w for w in db.workspaces.find({})}
    tokens_by_channel = {t["channel_id"]: t for t in db.oauth_tokens.find({})}
    tokens_by_ws = {t.get("workspace_id"): t for t in db.oauth_tokens.find({})}
    
    print("=================================================================")
    print("                    USERS AND WORKSPACES                         ")
    print("=================================================================")
    for u_id, u in users.items():
        print(f"\nUSER: {u.get('email')} (ID: {u_id})")
        print(f"  Role: {'PLATFORM OWNER' if u.get('is_owner') else 'STANDARD USER'}")
        print(f"  Active: {u.get('is_active')}")
        
        # Find workspaces owned by user
        user_workspaces = [w for w in workspaces.values() if str(w.get("owner_id")) == u_id]
        if not user_workspaces:
            print("  No workspaces found for this user.")
        for ws in user_workspaces:
            ws_id = str(ws["_id"])
            ch_id = ws.get("connected_channel_id")
            token = tokens_by_channel.get(ch_id) or tokens_by_ws.get(ws_id)
            print(f"  -> WORKSPACE: '{ws.get('name')}' (ID: {ws_id})")
            print(f"     Autopilot Enabled: {ws.get('autopilot_enabled')}")
            print(f"     Niche: {ws.get('niche')}")
            print(f"     Connected Channel ID: {ch_id}")
            print(f"     OAuth Token Stored: {bool(token)}")
            if token:
                print(f"     OAuth Token Expiry: {token.get('token_expiry')} (Has Refresh Token: {bool(token.get('encrypted_refresh_token') or token.get('refresh_token'))})")
    
    print("\n=================================================================")
    print("                  ALL VIDEOS BY WORKSPACE                        ")
    print("=================================================================")
    all_videos = list(db.videos.find({}).sort("created_at", -1))
    print(f"Total videos in DB: {len(all_videos)}")
    
    # Group videos by workspace
    videos_by_ws = {}
    for v in all_videos:
        ws_id = str(v.get("workspace_id") or "NONE")
        videos_by_ws.setdefault(ws_id, []).append(v)
        
    for ws_id, vlist in videos_by_ws.items():
        ws = workspaces.get(ws_id, {})
        u = users.get(str(ws.get("owner_id")), {}) if ws else {}
        owner_str = f"{u.get('email', 'Unknown')} ({'OWNER' if u.get('is_owner') else 'USER'})"
        print(f"\n--- Workspace: '{ws.get('name', 'UNKNOWN')}' (ID: {ws_id}) ---")
        print(f"    Owner: {owner_str}")
        print(f"    Connected Channel: {ws.get('connected_channel_id')}")
        print(f"    Total Videos: {len(vlist)}")
        
        for v in vlist:
            v_id = str(v["_id"])
            status = v.get("status")
            yt_id = v.get("youtube_video_id")
            yt_url = v.get("youtube_url")
            fpath = v.get("file_path")
            fexists = os.path.exists(fpath) if fpath else False
            created = v.get("created_at")
            pub_at = v.get("youtube_published_at")
            
            print(f"    * Video ID: {v_id}")
            print(f"      Title: {v.get('title')}")
            print(f"      Status: {status} | YouTube ID: {yt_id} | Published At: {pub_at}")
            print(f"      File Path: {fpath} (Exists on disk: {fexists})")
            print(f"      Created At: {created}")
            
    print("\n=================================================================")
    print("                    UNPUBLISHED VIDEOS                           ")
    print("=================================================================")
    unpublished = [v for v in all_videos if v.get("status") != "PUBLISHED" or not v.get("youtube_video_id")]
    print(f"Total unpublished videos: {len(unpublished)}")
    for v in unpublished:
        ws_id = str(v.get("workspace_id") or "NONE")
        ws = workspaces.get(ws_id, {})
        u = users.get(str(ws.get("owner_id")), {}) if ws else {}
        fpath = v.get("file_path")
        fexists = os.path.exists(fpath) if fpath else False
        print(f"\n[UNPUBLISHED] Video ID: {v.get('_id')}")
        print(f"  Title: {v.get('title')}")
        print(f"  Status: {v.get('status')}")
        print(f"  Workspace: '{ws.get('name')}' (ID: {ws_id})")
        print(f"  User: {u.get('email')} (Is Owner: {u.get('is_owner')})")
        print(f"  Channel ID: {ws.get('connected_channel_id')}")
        print(f"  File Path: {fpath} (Exists locally: {fexists})")
        print(f"  Created At: {v.get('created_at')}")

    print("\n=================================================================")
    print("                    PUBLISHING JOBS                              ")
    print("=================================================================")
    jobs = list(db.publishing_jobs.find({}).sort("created_at", -1))
    print(f"Total publishing jobs: {len(jobs)}")
    for j in jobs:
        print(f"Job ID: {j.get('_id')} | Video ID: {j.get('video_id')} | State: {j.get('state')} | Scheduled: {j.get('scheduled_at')}")
        if j.get("error") or j.get("error_message"):
            print(f"  Error: {j.get('error') or j.get('error_message')}")

if __name__ == "__main__":
    analyze()
