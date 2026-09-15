import sys, os, time
from bson import ObjectId
sys.path.insert(0, r"c:\Users\DELL\OneDrive\Desktop\yt")
from backend.app.core.db import SyncMongoDB

def get_all_data():
    db = SyncMongoDB.get_db()
    
    for attempt in range(3):
        try:
            users = list(db.users.find({}))
            workspaces = list(db.workspaces.find({}))
            videos = list(db.videos.find({}))
            jobs = list(db.publishing_jobs.find({}))
            tokens = list(db.oauth_tokens.find({}))
            return users, workspaces, videos, jobs, tokens
        except Exception as e:
            print(f"Retry {attempt+1} after DB error: {e}")
            time.sleep(2)
    raise RuntimeError("Failed to fetch DB data after retries")

users, workspaces, videos, jobs, tokens = get_all_data()

print(f"Users: {len(users)}, Workspaces: {len(workspaces)}, Videos: {len(videos)}, Jobs: {len(jobs)}, Tokens: {len(tokens)}")

# Map workspaces to users
ws_map = {str(w["_id"]): w for w in workspaces}
user_map = {str(u["_id"]): u for u in users}

# Group videos by user/workspace
print("\n" + "="*80)
print("COMPREHENSIVE VIDEO AUDIT FOR ALL USERS AND OWNERS")
print("="*80)

for u in users:
    u_id = str(u["_id"])
    role = "PLATFORM OWNER" if u.get("is_owner") else "USER"
    print(f"\n[{role}] {u.get('email')} (ID: {u_id})")
    
    u_workspaces = [w for w in workspaces if str(w.get("owner_id")) == u_id]
    if not u_workspaces:
        print("   No workspaces created.")
        continue
        
    for ws in u_workspaces:
        ws_id = str(ws["_id"])
        ch_id = ws.get("connected_channel_id")
        ws_tokens = [t for t in tokens if t.get("channel_id") == ch_id or t.get("workspace_id") == ws_id]
        token_status = f"Connected ({ch_id})" if ws_tokens else "No OAuth token"
        print(f"  * Workspace: '{ws.get('name')}' (ID: {ws_id})")
        print(f"    Channel: {token_status} | Autopilot: {ws.get('autopilot_enabled')} | Niche: {ws.get('niche')}")
        
        ws_videos = [v for v in videos if str(v.get("workspace_id")) == ws_id]
        print(f"    Total Videos in Workspace: {len(ws_videos)}")
        
        published = [v for v in ws_videos if v.get("status") == "PUBLISHED" and v.get("youtube_video_id")]
        unpublished = [v for v in ws_videos if v not in published]
        
        print(f"    - Published: {len(published)}")
        print(f"    - Unpublished / Issues: {len(unpublished)}")
        
        for v in unpublished:
            v_id = str(v["_id"])
            status = v.get("status")
            yt_id = v.get("youtube_video_id")
            fpath = v.get("file_path")
            fexists = os.path.exists(fpath) if fpath else False
            
            # find job
            v_jobs = [j for j in jobs if str(j.get("_id")) == str(v.get("job_id")) or str(j.get("video_id")) == v_id]
            last_job = v_jobs[-1] if v_jobs else None
            job_state = last_job.get("state") if last_job else "NO_JOB"
            job_err = (last_job.get("error") or last_job.get("error_message")) if last_job else None
            
            print(f"      [!] Video: {v.get('title')}")
            print(f"          ID: {v_id} | Status: {status} | YT ID: {yt_id}")
            print(f"          File Exists Locally: {fexists} ({fpath})")
            print(f"          Job State: {job_state} | Error: {job_err}")
            print(f"          Created: {v.get('created_at')}")

# Videos with no workspace_id
orphan_videos = [v for v in videos if not v.get("workspace_id") or str(v.get("workspace_id")) not in ws_map]
if orphan_videos:
    print(f"\n[ORPHAN VIDEOS (No Workspace)] Total: {len(orphan_videos)}")
    for v in orphan_videos:
        print(f"  * ID: {v['_id']} | Title: {v.get('title')} | Status: {v.get('status')} | YT ID: {v.get('youtube_video_id')}")
