"""Publish Lesson 1 & Lesson 2 directly to Channel 2 (@bhanuteja-n8x).
Target Channel ID: UC9LB0BwUOR3c43i7OEoDswg
Target Workspace ID: 6a9fd659f2e1cbccfc7a8e84
"""

import os
import sys
import asyncio
from pathlib import Path
from datetime import datetime, timezone
from googleapiclient.http import MediaFileUpload

sys.path.insert(0, os.getcwd())
from backend.app.core.db import SyncMongoDB
from backend.app.core.security import decrypt_token
from backend.app.core.oauth import GoogleOAuthManager
from backend.app.providers.youtube.youtube_client import YouTubeClientProvider

CHANNEL_ID = "UC9LB0BwUOR3c43i7OEoDswg"
WORKSPACE_ID = "6a9fd659f2e1cbccfc7a8e84"


async def publish_video(yt_provider, service, video_path: str, thumb_path: str, title: str, description: str, tags: list):
    print(f"\n==================================================")
    print(f"UPLOADING TO CHANNEL 2: {title}")
    print(f"File: {video_path}")
    print(f"==================================================")

    res = await yt_provider.upload_short(
        video_filepath=video_path,
        title=title,
        description=description,
        tags=tags,
        privacy_status="public"
    )

    vid_id = res.get("video_id")
    url = res.get("url")
    print(f"🎉 SUCCESS! Published Short ID: {vid_id}")
    print(f"Shorts URL: {url}")

    # Set custom thumbnail
    if thumb_path and os.path.exists(thumb_path) and vid_id:
        try:
            service.thumbnails().set(
                videoId=vid_id,
                media_body=MediaFileUpload(thumb_path, mimetype="image/jpeg")
            ).execute()
            print("📸 Custom Thumbnail uploaded successfully!")
        except Exception as e:
            print(f"Thumbnail upload notice: {e}")

    return res


async def main():
    db = SyncMongoDB.get_db()
    token_doc = db.oauth_tokens.find_one({"channel_id": CHANNEL_ID})
    if not token_doc:
        print("ERROR: No token found for Channel 2!")
        return

    rt = decrypt_token(token_doc["encrypted_refresh_token"])
    token_resp = await GoogleOAuthManager.refresh_access_token(rt)
    creds = GoogleOAuthManager.get_google_credentials(token_resp["access_token"], rt)
    yt = YouTubeClientProvider(credentials=creds)
    service = yt._get_service()

    # Verify channel
    ch_info = service.channels().list(part="snippet,statistics", mine=True).execute()["items"][0]
    print(f"Target YouTube Channel: '{ch_info['snippet']['title']}' (ID: {ch_info['id']})")

    # 1. Publish Lesson 1
    ep1_video = "media_storage/rendered/channel2_telugu_ep1.mp4"
    ep1_thumb = "media_storage/thumbnails/channel2_telugu_ep1.jpg"
    ep1_title = "Python in Telugu Ep 1: Variables & Memory ఎలా పనిచేస్తాయి? ⚡ #Shorts #Telugu #Python"
    ep1_desc = """పైథాన్ తెలుగు మాస్టర్ సిరీస్ - ఎపిసోడ్ 1: Variables & Memory!
కంప్యూటర్ మెమొరీ లో వేరియబుల్స్ ఎలా క్రియేట్ అవుతాయి? x = 10 మరియు x = 25 రీఅసైన్మెంట్ ఎలా జరుగుతుందో యెల్లో స్టిక్ మాన్ యానిమేషన్ తో క్లియర్ గా తెలుసుకోండి!

🔥 Follow for Lesson 2: The 4 Core Python Data Types!

#PythonInTelugu #TeluguCoding #LearnPythonTelugu #PythonShorts #CodingInTelugu #PythonTeluguTutorial #ProgrammingTelugu"""
    ep1_tags = ["Python In Telugu", "Telugu Coding", "Learn Python Telugu", "Python Shorts", "Coding In Telugu", "Python Telugu Tutorial", "Programming In Telugu", "Variables", "Computer Science"]

    res1 = await publish_video(yt, service, ep1_video, ep1_thumb, ep1_title, ep1_desc, ep1_tags)

    now_utc = datetime.now(timezone.utc)
    db.videos.insert_one({
        "channel_id": CHANNEL_ID,
        "workspace_id": WORKSPACE_ID,
        "title": ep1_title,
        "youtube_video_id": res1["video_id"],
        "youtube_url": res1["url"],
        "status": "PUBLISHED",
        "published_at": now_utc,
        "episode_number": 1,
        "niche": "Python in Telugu",
        "language": "te"
    })

    # Small pause between uploads
    await asyncio.sleep(5)

    # 2. Publish Lesson 2
    ep2_video = "media_storage/rendered/channel2_telugu_ep2.mp4"
    ep2_thumb = "media_storage/thumbnails/channel2_telugu_ep2.jpg"
    ep2_title = "Python in Telugu Ep 2: 4 Core Data Types (int, float, str, bool) ⚡ #Shorts #Telugu #Python"
    ep2_desc = """పైథాన్ తెలుగు మాస్టర్ సిరీస్ - ఎపిసోడ్ 2: 4 Core Data Types!
Integer, Float, String, మరియు Boolean వేరియబుల్స్ ఎలా ఉపయోగించాలి? type() ఫంక్షన్ తో మెమొరీ క్లాసిఫికేషన్ ఎలా చెక్ చేయాలి?

🔥 Follow for Lesson 3: Taking User Input with input()!

#PythonInTelugu #TeluguCoding #LearnPythonTelugu #PythonShorts #CodingInTelugu #PythonTeluguTutorial #ProgrammingTelugu #DataTypes"""
    ep2_tags = ["Python In Telugu", "Telugu Coding", "Learn Python Telugu", "Python Shorts", "Data Types", "Coding In Telugu", "Python Telugu Tutorial", "Programming In Telugu"]

    res2 = await publish_video(yt, service, ep2_video, ep2_thumb, ep2_title, ep2_desc, ep2_tags)

    db.videos.insert_one({
        "channel_id": CHANNEL_ID,
        "workspace_id": WORKSPACE_ID,
        "title": ep2_title,
        "youtube_video_id": res2["video_id"],
        "youtube_url": res2["url"],
        "status": "PUBLISHED",
        "published_at": datetime.now(timezone.utc),
        "episode_number": 2,
        "niche": "Python in Telugu",
        "language": "te"
    })

    # Update curriculum tracker for Channel 2
    op = chr(36) + "set"
    db.curriculum_tracker.update_one(
        {"niche": "Python in Telugu"},
        {op: {
            "current_episode": 3,
            "last_published_episode": 2,
            "last_published_video_id": res2["video_id"],
            "updated_at": datetime.now(timezone.utc)
        }},
        upsert=True
    )
    print("\n✅ SUCCESS: Channel 2 curriculum tracker updated to Episode 3!")


if __name__ == "__main__":
    asyncio.run(main())

