"""Update published YouTube Shorts with viral hashtags and high-CTR titles.

Usage:
  python scripts/update_youtube_titles.py          # Dry-run: preview title changes
  python scripts/update_youtube_titles.py --apply  # Live: update on YouTube & MongoDB
"""

import sys
import os
import argparse
import asyncio
from datetime import datetime, timezone
from pathlib import Path

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from backend.app.core.db import SyncMongoDB
from backend.app.core.security import decrypt_token
from backend.app.core.oauth import GoogleOAuthManager
from backend.app.providers.youtube.youtube_client import YouTubeClientProvider
from backend.app.agents.title import format_viral_title


async def update_titles(apply: bool = False, limit: int = 20):
    print("=" * 70)
    print(f"YOUTUBE SHORTS VIRAL METADATA SYNC (Mode: {'LIVE APPLY' if apply else 'PREVIEW / DRY-RUN'})")
    print("=" * 70)

    db = SyncMongoDB.get_db()
    videos = list(db.videos.find({"status": "PUBLISHED"}).sort("created_at", -1).limit(limit))

    if not videos:
        print("No published videos found in database.")
        return

    print(f"Found {len(videos)} published videos.\n")

    # Cache youtube clients per channel
    yt_clients: dict[str, YouTubeClientProvider] = {}

    async def get_yt_client(ch_id: str) -> YouTubeClientProvider:
        if ch_id in yt_clients:
            return yt_clients[ch_id]

        tok = db.oauth_tokens.find_one({"channel_id": ch_id})
        if not tok:
            # Fallback to any token
            tok = db.oauth_tokens.find_one()
        if not tok:
            raise RuntimeError(f"No OAuth token found for channel {ch_id}")

        encrypted_rt = tok.get("encrypted_refresh_token") or tok.get("refresh_token")
        refresh_token = decrypt_token(encrypted_rt)
        token_resp = await GoogleOAuthManager.refresh_access_token(refresh_token)
        creds = GoogleOAuthManager.get_google_credentials(token_resp["access_token"], refresh_token)
        client = YouTubeClientProvider(credentials=creds)
        yt_clients[ch_id] = client
        return client

    # Default channel for owner uploads
    default_channel = "UC9LB0BwUOR3c43i7OEoDswg"

    updated_count = 0
    skipped_count = 0

    for i, v in enumerate(videos, 1):
        vid_id = v.get("youtube_video_id")
        old_title = v.get("title", "").strip()
        hashtags = v.get("hashtags") or []
        tags = v.get("tags") or []

        new_title = format_viral_title(old_title, hashtags)

        print(f"[{i}/{len(videos)}] Video ID: {vid_id}")
        print(f"  OLD: {old_title} ({len(old_title)} chars)")
        print(f"  NEW: {new_title} ({len(new_title)} chars)")

        if old_title == new_title:
            print("  Status: Already has optimal viral hashtags. Skipping.")
            skipped_count += 1
            print("-" * 70)
            continue

        if not vid_id:
            print("  Status: Missing YouTube Video ID. Skipping YouTube API update.")
            if apply:
                db.videos.update_one({"_id": v["_id"]}, {"$set": {"title": new_title, "updated_at": datetime.now(timezone.utc)}})
                print("  Updated in local MongoDB.")
            print("-" * 70)
            continue

        if apply:
            ch_id = v.get("channel_id") or default_channel
            try:
                client = await get_yt_client(ch_id)
                # Ensure tags include Shorts and viral keywords
                enhanced_tags = list(dict.fromkeys(tags + ["Shorts", "viral", "trending"]))
                await client.update_video_metadata(
                    youtube_video_id=vid_id,
                    title=new_title,
                    tags=enhanced_tags
                )
                db.videos.update_one(
                    {"_id": v["_id"]},
                    {
                        "$set": {
                            "title": new_title,
                            "tags": enhanced_tags,
                            "updated_at": datetime.now(timezone.utc)
                        }
                    }
                )
                print("  Status: Successfully updated on YouTube and MongoDB! 🎉")
                updated_count += 1
            except Exception as e:
                err_str = str(e)
                if "insufficientPermissions" in err_str or "insufficient authentication scopes" in err_str:
                    db.videos.update_one(
                        {"_id": v["_id"]},
                        {
                            "$set": {
                                "title": new_title,
                                "updated_at": datetime.now(timezone.utc)
                            }
                        }
                    )
                    print("  Status: YouTube OAuth token was granted with upload-only scope. Updated title in MongoDB.")
                    print("          Note: To update already-published videos on YouTube, reconnect your channel with the newly added force-ssl scope or update them in YouTube Studio.")
                else:
                    print(f"  Status: Error updating video: {e}")
        else:
            print("  Status: Pending apply. (Run with --apply to push live)")

        print("-" * 70)

    print(f"\nSummary: {updated_count} updated live, {skipped_count} already optimal.")
    if not apply:
        print("To push these viral titles to YouTube live, run:")
        print("  python scripts/update_youtube_titles.py --apply")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Update published YouTube Shorts titles with viral hashtags.")
    parser.add_argument("--apply", action="store_true", help="Apply updates directly to YouTube and MongoDB")
    parser.add_argument("--limit", type=int, default=20, help="Number of recent videos to inspect")
    args = parser.parse_args()

    asyncio.run(update_titles(apply=args.apply, limit=args.limit))
