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

async def publish():
    print("=========================================================")
    print("PUBLISHING SINDHU'S PENDING SHORT TO YOUTUBE (UC9LB0BwUOR3c43i7OEoDswg)")
    print("=========================================================")

    db = SyncMongoDB.get_db()
    video_id = ObjectId("6aa93a63cbf9cc578f574aad")
    v = db.videos.find_one({"_id": video_id})
    if not v:
        print("Video not found!")
        return

    fpath = v.get("file_path")
    print(f"Video file: {fpath} (Exists: {os.path.exists(fpath)})")
    if not os.path.exists(fpath):
        print("File does not exist!")
        return

    tok = db.oauth_tokens.find_one({"channel_id": "UC9LB0BwUOR3c43i7OEoDswg"})
    if not tok:
        print("Token not found!")
        return

    encrypted_rt = tok.get("encrypted_refresh_token") or tok.get("refresh_token")
    refresh_token = decrypt_token(encrypted_rt)
    print("Refreshing access token...")
    token_resp = await GoogleOAuthManager.refresh_access_token(refresh_token)
    access_token = token_resp["access_token"]
    print("Access token obtained successfully!")

    creds = GoogleOAuthManager.get_google_credentials(access_token, refresh_token)
    yt_provider = YouTubeClientProvider(credentials=creds)

    print(f"Uploading '{v.get('title')}'...")
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

    print(f"\n🎉 SUCCESS! Published to YouTube!")
    print(f"Video ID: {yt_id}")
    print(f"Shorts URL: {yt_url}")

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
    print("Updated video in database to PUBLISHED.")

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
        print("Updated publishing job in database to PUBLISHED.")

if __name__ == "__main__":
    asyncio.run(publish())
