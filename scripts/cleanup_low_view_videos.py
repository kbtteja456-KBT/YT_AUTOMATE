"""Script to clean up or unpublish videos with fewer than 100 views on Python Master channel."""

import sys
import os
import argparse
from pathlib import Path
from googleapiclient.errors import HttpError

sys.path.insert(0, os.getcwd())
from backend.app.core.db import SyncMongoDB
from backend.app.celery_app.tasks import _get_authenticated_youtube_provider
from backend.app.core.logging import logger

CHANNEL_ID = "UCBQAktpydJEze5CmEbeJBRQ"


def run_cleanup(mode: str = "dry_run", threshold: int = 100):
    db = SyncMongoDB.get_db()
    provider = _get_authenticated_youtube_provider(db)
    service = provider._get_service()

    print(f"Fetching uploaded videos for channel {CHANNEL_ID}...")
    # Fetch uploads playlist ID
    ch_req = service.channels().list(part="contentDetails", id=CHANNEL_ID)
    ch_res = ch_req.execute()
    items = ch_res.get("items", [])
    if not items:
        print("Channel not found.")
        return

    uploads_playlist_id = items[0]["contentDetails"]["relatedPlaylists"]["uploads"]
    
    # Paginate through all playlist items
    video_ids = []
    next_page_token = None
    while True:
        pl_req = service.playlistItems().list(
            part="contentDetails",
            playlistId=uploads_playlist_id,
            maxResults=50,
            pageToken=next_page_token
        )
        pl_res = pl_req.execute()
        for item in pl_res.get("items", []):
            video_ids.append(item["contentDetails"]["videoId"])
        next_page_token = pl_res.get("nextPageToken")
        if not next_page_token:
            break

    print(f"Total videos on channel: {len(video_ids)}")

    # Fetch statistics in batches of 50
    targets = []
    for i in range(0, len(video_ids), 50):
        batch = video_ids[i:i+50]
        v_req = service.videos().list(
            part="snippet,statistics,status",
            id=",".join(batch)
        )
        v_res = v_req.execute()
        for v in v_res.get("items", []):
            vid_id = v["id"]
            title = v.get("snippet", {}).get("title", "")
            views = int(v.get("statistics", {}).get("viewCount", 0))
            privacy = v.get("status", {}).get("privacyStatus", "public")
            if views < threshold:
                targets.append({
                    "id": vid_id,
                    "title": title,
                    "views": views,
                    "privacy": privacy
                })

    print(f"\nFound {len(targets)} videos with fewer than {threshold} views (out of {len(video_ids)} total).")

    if mode == "dry_run":
        print("\n[DRY RUN PREVIEW - NO CHANGES MADE]")
        for idx, t in enumerate(targets, 1):
            print(f"{idx:3d}. [{t['id']}] {t['views']} views | {t['title'][:60]}")
        return len(targets)

    if mode == "private":
        print(f"\n[SETTING {len(targets)} VIDEOS TO PRIVATE ON YOUTUBE...]")
        success = 0
        for idx, t in enumerate(targets, 1):
            try:
                service.videos().update(
                    part="status",
                    body={
                        "id": t["id"],
                        "status": {
                            "privacyStatus": "private"
                        }
                    }
                ).execute()
                print(f"[{idx}/{len(targets)}] Marked PRIVATE: {t['id']} ({t['title'][:40]})")
                success += 1
            except Exception as e:
                print(f"[{idx}/{len(targets)}] Failed to mark private {t['id']}: {e}")
        print(f"\nSuccessfully set {success}/{len(targets)} videos to PRIVATE.")
        return success

    if mode == "delete":
        print(f"\n[PERMANENTLY DELETING {len(targets)} VIDEOS FROM YOUTUBE & DATABASE...]")
        success = 0
        for idx, t in enumerate(targets, 1):
            vid_id = t["id"]
            try:
                service.videos().delete(id=vid_id).execute()
                # Remove from MongoDB
                db.videos.delete_many({"youtube_video_id": vid_id})
                db.publishing_jobs.delete_many({"youtube_video_id": vid_id})
                print(f"[{idx}/{len(targets)}] Deleted from YouTube & DB: {vid_id} ({t['title'][:40]})")
                success += 1
            except Exception as e:
                print(f"[{idx}/{len(targets)}] Failed to delete {vid_id}: {e}")
        print(f"\nSuccessfully deleted {success}/{len(targets)} videos.")
        return success


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", choices=["dry_run", "private", "delete"], default="dry_run")
    parser.add_argument("--threshold", type=int, default=100)
    args = parser.parse_args()
    run_cleanup(mode=args.mode, threshold=args.threshold)

