import sys, os
from datetime import datetime, timezone
from backend.app.core.db import SyncMongoDB

db = SyncMongoDB.get_db()
res = db.videos.update_one(
    {},
    {
        "$set": {
            "youtube_video_id": "WHWzGm6Td9Q",
            "youtube_url": "https://www.youtube.com/shorts/WHWzGm6Td9Q",
            "status": "PUBLISHED",
            "published_at": datetime.now(timezone.utc),
            "privacy_status": "public",
            "channel_id": "UCBQAktpydJEze5CmEbeJBRQ",
            "channel_title": "Bhanu Teja"
        }
    }
)
print("Updated video in DB! Modified count:", res.modified_count)

# Also force sync channel to pick up the updated video count
from backend.app.core.oauth import GoogleOAuthManager
from backend.app.core.security import decrypt_token
import asyncio

async def sync():
    tok = db.oauth_tokens.find_one({"channel_id": "UCBQAktpydJEze5CmEbeJBRQ"})
    if tok:
        rt = decrypt_token(tok["encrypted_refresh_token"])
        t = await GoogleOAuthManager.refresh_access_token(rt)
        p = await GoogleOAuthManager.fetch_channel_profile(t["access_token"])
        print("Channel live stats:", p["title"], "Subs:", p["subscriber_count"], "Videos:", p["video_count"])
        db.youtube_channels.update_one(
            {"channel_id": "UCBQAktpydJEze5CmEbeJBRQ"},
            {"$set": {
                "video_count": p.get("video_count", 0),
                "subscriber_count": p.get("subscriber_count", 0),
                "view_count": p.get("view_count", 0),
                "last_synced_at": datetime.now(timezone.utc)
            }}
        )
        print("Channel stats synced in DB!")

asyncio.run(sync())
