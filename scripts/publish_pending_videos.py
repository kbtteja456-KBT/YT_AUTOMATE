import sys
import os
import asyncio
from datetime import datetime, timezone
from bson import ObjectId

sys.path.insert(0, r"c:\Users\DELL\OneDrive\Desktop\yt")
from backend.app.core.db import SyncMongoDB
from backend.app.core.security import decrypt_token, compute_file_hash
from backend.app.core.oauth import GoogleOAuthManager
from backend.app.providers.youtube.youtube_client import YouTubeClientProvider
from backend.app.models.job import JobState

async def publish_pranith_video():
    print("\n========================================================")
    print("PUBLISHING PRANITH'S VIDEO TO YOUTUBE CHANNEL UChQZp8FPA7kAr4rM16uuG2A")
    print("========================================================")
    db = SyncMongoDB.get_db()
    video_id = ObjectId("6aa943fc98a6355a7735d461")
    v = db.videos.find_one({"_id": video_id})
    if not v:
        print("Video not found!")
        return
        
    fpath = v.get("file_path")
    if not os.path.exists(fpath):
        print(f"File not found at {fpath}!")
        return

    ws_id = v.get("workspace_id")
    tok = db.oauth_tokens.find_one({"workspace_id": ws_id}) or db.oauth_tokens.find_one({"channel_id": "UChQZp8FPA7kAr4rM16uuG2A"})
    if not tok:
        print("No OAuth token found for Pranith's workspace!")
        return

    encrypted_rt = tok.get("encrypted_refresh_token") or tok.get("refresh_token")
    refresh_token = decrypt_token(encrypted_rt)
    print("Refreshing access token...")
    token_resp = await GoogleOAuthManager.refresh_access_token(refresh_token)
    access_token = token_resp["access_token"]
    print("Access token refreshed successfully!")

    creds = GoogleOAuthManager.get_google_credentials(access_token, refresh_token)
    yt_provider = YouTubeClientProvider(credentials=creds)

    print(f"Uploading '{v.get('title')}' ({fpath})...")
    upload_res = await yt_provider.upload_short(
        video_filepath=fpath,
        title=v.get("title"),
        description=v.get("description"),
        tags=v.get("tags") or [],
        privacy_status="public"
    )

    yt_id = upload_res.get("video_id")
    yt_url = upload_res.get("url")
    file_hash = upload_res.get("file_hash") or compute_file_hash(fpath)

    print(f"🎉 SUCCESS! Published to YouTube: {yt_id} -> {yt_url}")

    now = datetime.now(timezone.utc)
    db.videos.update_one(
        {"_id": video_id},
        {
            "$set": {
                "status": "PUBLISHED",
                "youtube_video_id": yt_id,
                "youtube_url": yt_url,
                "youtube_published_at": now,
                "file_hash": file_hash,
                "privacy_status": "public",
                "updated_at": now
            }
        }
    )
    print(f"Updated video {video_id} to PUBLISHED.")

    # Update any associated job
    if v.get("job_id"):
        db.publishing_jobs.update_one(
            {"_id": ObjectId(v["job_id"]) if ObjectId.is_valid(v["job_id"]) else v["job_id"]},
            {
                "$set": {
                    "state": JobState.PUBLISHED.value,
                    "youtube_video_id": yt_id,
                    "youtube_url": yt_url,
                    "published_at": now,
                    "updated_at": now,
                    "error_message": None
                }
            }
        )
        print("Updated publishing job to PUBLISHED.")

def fix_owner_video_status():
    print("\n========================================================")
    print("FIXING OWNER VIDEO (6aa3f339e45e4b28f92f1483) DB STATUS")
    print("========================================================")
    db = SyncMongoDB.get_db()
    video_id = ObjectId("6aa3f339e45e4b28f92f1483")
    v = db.videos.find_one({"_id": video_id})
    if v:
        print(f"Current status: {v.get('status')}, YT ID: {v.get('youtube_video_id')}")
        db.videos.update_one(
            {"_id": video_id},
            {
                "$set": {
                    "status": "PUBLISHED",
                    "youtube_published_at": v.get("created_at") or datetime.now(timezone.utc),
                    "updated_at": datetime.now(timezone.utc)
                }
            }
        )
        print(f"Updated owner video {video_id} to status: PUBLISHED.")

if __name__ == "__main__":
    fix_owner_video_status()
    asyncio.run(publish_pranith_video())
