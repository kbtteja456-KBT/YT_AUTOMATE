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

async def publish_sindhu_video():
    db = SyncMongoDB.get_db()
    video_id = ObjectId("6aa93a63cbf9cc578f574aad")
    v = db.videos.find_one({"_id": video_id})
    if not v:
        print("Video not found!")
        return False
        
    fpath = v.get("file_path")
    if not os.path.exists(fpath):
        print(f"File not found at {fpath}!")
        return False

    ws_id = v.get("workspace_id")
    tok = db.oauth_tokens.find_one({"workspace_id": ws_id}) or db.oauth_tokens.find_one({"channel_id": "UC9LB0BwUOR3c43i7OEoDswg"})
    if not tok:
        print("No OAuth token document found!")
        return False

    encrypted_rt = tok.get("encrypted_refresh_token") or tok.get("refresh_token")
    if not encrypted_rt:
        print("No refresh token found in token doc!")
        return False

    try:
        refresh_token = decrypt_token(encrypted_rt)
        print("Attempting to refresh Google OAuth token...")
        token_resp = await GoogleOAuthManager.refresh_access_token(refresh_token)
        access_token = token_resp["access_token"]
        print("Access token refreshed successfully!")
    except Exception as e:
        print(f"Token refresh failed: {e}")
        return False

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
    return True

if __name__ == "__main__":
    success = asyncio.run(publish_sindhu_video())
    sys.exit(0 if success else 1)
