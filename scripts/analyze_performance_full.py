import sys
import os
import asyncio
from datetime import datetime, timezone
import json

sys.path.insert(0, r"c:\Users\DELL\OneDrive\Desktop\yt")
from backend.app.core.db import SyncMongoDB
from backend.app.core.security import decrypt_token
from backend.app.core.oauth import GoogleOAuthManager
from googleapiclient.discovery import build

async def main():
    db = SyncMongoDB.get_db()
    channels = list(db.youtube_channels.find({"is_active": True}))
    print(f"Found {len(channels)} active channels in DB.\n")
    
    # Also collect all videos in db
    all_videos = list(db.videos.find({"status": "PUBLISHED"}))
    print(f"Total published videos in DB: {len(all_videos)}")

    # Publishing jobs with video IDs
    jobs_with_yt = list(db.publishing_jobs.find({"state": "PUBLISHED", "youtube_video_id": {"$exists": True, "$ne": None}}))
    print(f"Total published jobs with YouTube ID: {len(jobs_with_yt)}")

    all_yt_ids = set()
    for v in all_videos:
        if v.get("youtube_video_id"):
            all_yt_ids.add(v["youtube_video_id"])
    for j in jobs_with_yt:
        if j.get("youtube_video_id"):
            all_yt_ids.add(j["youtube_video_id"])
            
    print(f"Unique YouTube Video IDs across DB: {len(all_yt_ids)}\n")

    # Get YouTube API service using the first valid channel token
    yt_service = None
    for ch in channels:
        ch_id = ch.get("channel_id")
        ws_id = ch.get("workspace_id")
        token_doc = db.oauth_tokens.find_one({"workspace_id": ws_id}) or db.oauth_tokens.find_one({"channel_id": ch_id})
        if not token_doc:
            continue
        encrypted_rt = token_doc.get("encrypted_refresh_token") or token_doc.get("refresh_token")
        if not encrypted_rt:
            continue
        try:
            rt = decrypt_token(encrypted_rt)
            t_resp = await GoogleOAuthManager.refresh_access_token(rt)
            creds = GoogleOAuthManager.get_google_credentials(t_resp.get("access_token"), rt)
            service = build("youtube", "v3", credentials=creds, cache_discovery=False)
            
            # Channel stats
            res = service.channels().list(part="snippet,statistics", id=ch_id).execute()
            if res.get("items"):
                ch_data = res["items"][0]
                snip = ch_data.get("snippet", {})
                stats = ch_data.get("statistics", {})
                print(f"------------------------------------------------------------------")
                print(f"CHANNEL: {snip.get('title')} ({ch_id})")
                print(f"  Subscribers: {stats.get('subscriberCount')}")
                print(f"  Total Views: {stats.get('viewCount')}")
                print(f"  Total Videos: {stats.get('videoCount')}")
                print(f"------------------------------------------------------------------")
            if not yt_service:
                yt_service = service
        except Exception as e:
            print(f"Error fetching channel {ch_id}: {e}")

    if not yt_service:
        print("❌ Could not obtain authenticated YouTube service.")
        return

    # Now let's fetch batch stats for all video IDs (up to 50 at a time)
    yt_ids_list = list(all_yt_ids)
    video_stats = {}
    print(f"\nFetching video stats from YouTube Data API in batches of 50...")
    for i in range(0, len(yt_ids_list), 50):
        batch = yt_ids_list[i:i+50]
        try:
            resp = yt_service.videos().list(part="snippet,statistics,contentDetails", id=",".join(batch)).execute()
            for item in resp.get("items", []):
                vid = item["id"]
                snip = item.get("snippet", {})
                st = item.get("statistics", {})
                video_stats[vid] = {
                    "id": vid,
                    "title": snip.get("title"),
                    "published_at": snip.get("publishedAt"),
                    "views": int(st.get("viewCount", 0)),
                    "likes": int(st.get("likeCount", 0)),
                    "comments": int(st.get("commentCount", 0)),
                    "tags": snip.get("tags", []),
                    "channelId": snip.get("channelId"),
                    "channelTitle": snip.get("channelTitle")
                }
        except Exception as e:
            print(f"Error batch fetching {i} to {i+50}: {e}")

    print(f"Successfully fetched live metrics for {len(video_stats)} videos from YouTube!\n")

    # Group video stats by channelTitle
    by_channel = {}
    for vid, data in video_stats.items():
        c_title = data.get("channelTitle", "Unknown Channel")
        by_channel.setdefault(c_title, []).append(data)

    for ch_name, vids in by_channel.items():
        vids_sorted = sorted(vids, key=lambda x: x["views"], reverse=True)
        total_views = sum(v["views"] for v in vids)
        total_likes = sum(v["likes"] for v in vids)
        total_comments = sum(v["comments"] for v in vids)
        avg_views = total_views / len(vids) if vids else 0
        
        # Categorize by views
        zero_views = [v for v in vids if v["views"] == 0]
        low_views = [v for v in vids if 0 < v["views"] < 100]
        medium_views = [v for v in vids if 100 <= v["views"] < 1000]
        high_views = [v for v in vids if v["views"] >= 1000]

        print("==================================================================")
        print(f"📊 PERFORMANCE AUDIT FOR: {ch_name}")
        print("==================================================================")
        print(f"Total Videos Tracked: {len(vids)}")
        print(f"Total Views:          {total_views:,}")
        print(f"Average Views/Video:  {avg_views:.1f}")
        print(f"Total Likes:          {total_likes:,}")
        print(f"Total Comments:       {total_comments:,}")
        print(f"Engagement Rate:      {((total_likes + total_comments) / total_views * 100) if total_views else 0:.2f}%")
        print("\nView Distribution:")
        print(f"  • 0 views:          {len(zero_views)} videos ({len(zero_views)/len(vids)*100:.1f}%)")
        print(f"  • 1 - 99 views:     {len(low_views)} videos ({len(low_views)/len(vids)*100:.1f}%)")
        print(f"  • 100 - 999 views:  {len(medium_views)} videos ({len(medium_views)/len(vids)*100:.1f}%)")
        print(f"  • 1000+ views:      {len(high_views)} videos ({len(high_views)/len(vids)*100:.1f}%)")

        print("\n🔥 TOP 5 BEST PERFORMING VIDEOS:")
        for v in vids_sorted[:5]:
            print(f"  [{v['views']} views, {v['likes']} likes, {v['comments']} comments] {v['title']} (https://youtu.be/{v['id']})")

        print("\n❄️ BOTTOM 5 WORST / RECENT PERFORMING VIDEOS:")
        for v in vids_sorted[-5:]:
            print(f"  [{v['views']} views, {v['likes']} likes, {v['comments']} comments] {v['title']} (https://youtu.be/{v['id']})")
        print("\n")

    # Save complete detailed data for in-depth analysis
    with open("media_storage/latest_analytics_snapshot.json", "w", encoding="utf-8") as f:
        json.dump(video_stats, f, indent=2)

if __name__ == "__main__":
    asyncio.run(main())

