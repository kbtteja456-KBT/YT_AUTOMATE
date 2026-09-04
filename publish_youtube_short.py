import asyncio
import os
import sys
import time
from pathlib import Path
from datetime import datetime, timezone

sys.path.insert(0, os.getcwd())

from backend.app.core.db import SyncMongoDB
from backend.app.core.security import decrypt_token, compute_file_hash
from backend.app.core.oauth import GoogleOAuthManager
from backend.app.providers.youtube.youtube_client import YouTubeClientProvider

async def main():
    print("==================================================")
    print("STARTING YOUTUBE SHORT PUBLISHING PIPELINE")
    print("==================================================")

    db = SyncMongoDB.get_db()

    # 1. Fetch channel and token
    channel = db.youtube_channels.find_one({"is_active": True})
    if not channel:
        print("ERROR: No active YouTube channel found in MongoDB!")
        return

    channel_id = channel["channel_id"]
    channel_title = channel.get("title", "Unknown")
    print(f"Target Channel: {channel_title} ({channel_id})")

    token_doc = db.oauth_tokens.find_one({"channel_id": channel_id})
    if not token_doc:
        print("ERROR: No OAuth token document found for channel!")
        return

    # 2. Decrypt refresh token & obtain fresh access token
    encrypted_rt = token_doc["encrypted_refresh_token"]
    refresh_token = decrypt_token(encrypted_rt)
    print("Refreshing Google OAuth access token...")
    token_resp = await GoogleOAuthManager.refresh_access_token(refresh_token)
    access_token = token_resp["access_token"]
    print("Access token refreshed successfully!")

    # 3. Create Google OAuth credentials
    creds = GoogleOAuthManager.get_google_credentials(access_token, refresh_token)
    yt_provider = YouTubeClientProvider(credentials=creds)

    # 4. Prepare video metadata
    video_file = Path("media_storage/rendered/short_rendered.mp4")
    if not video_file.exists():
        print(f"ERROR: Video file not found at {video_file}!")
        return

    video_size_mb = video_file.stat().st_size / (1024 * 1024)
    print(f"Uploading file: {video_file.name} ({video_size_mb:.2f} MB)")

    title = "5 AI Tools Every Creator Needs in 2026 #Shorts"
    description = (
        "Stop wasting 3 hours every day switching tabs! "
        "Here are 5 game-changing AI tools that will 10x your content creation workflow in 2026.\n\n"
        "1. Claude 3.5 Sonnet - Lightning-fast research\n"
        "2. Cursor AI - Autonomous coding\n"
        "3. Edge Neural TTS - Ultra-natural voiceovers\n"
        "4. Flux & Midjourney - Cinematic visuals\n"
        "5. FFmpeg Automation - Instant video rendering\n\n"
        "#Shorts #AI #Tech #Productivity #ContentCreation #ArtificialIntelligence"
    )
    tags = ["Shorts", "AI", "Tech", "Productivity", "ContentCreation", "ArtificialIntelligence", "YouTubeShorts", "Tools"]

    print("Uploading to YouTube with privacyStatus='public'...")
    upload_res = await yt_provider.upload_short(
        video_filepath=str(video_file),
        title=title,
        description=description,
        tags=tags,
        privacy_status="public"
    )

    video_id = upload_res["video_id"]
    youtube_url = upload_res["url"]
    file_hash = upload_res["file_hash"]

    print("\n==================================================")
    print("🎉 VIDEO SUCCESSFULLY PUBLISHED TO YOUTUBE!")
    print(f"Video ID: {video_id}")
    print(f"Shorts URL: {youtube_url}")
    print(f"Privacy: {upload_res['privacy_status']}")
    print("==================================================")

    # 5. Update video record in MongoDB
    now = datetime.now(timezone.utc)
    db.videos.update_one(
        {},
        {
            "$set": {
                "youtube_video_id": video_id,
                "youtube_url": youtube_url,
                "status": "PUBLISHED",
                "published_at": now,
                "privacy_status": "public",
                "file_hash": file_hash,
                "channel_id": channel_id,
                "channel_title": channel_title
            }
        }
    )
    print("Updated MongoDB video record with PUBLISHED status and YouTube URL!")

if __name__ == "__main__":
    asyncio.run(main())
