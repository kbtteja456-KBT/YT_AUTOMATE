import sys
import os
sys.path.insert(0, os.getcwd())
from backend.app.core.db import SyncMongoDB
from datetime import datetime, timezone

db = SyncMongoDB.get_db()
now_utc = datetime.now(timezone.utc)
vid_id = 'X5QdGQCxH-w'
video_title = 'Python Visual Ep 1: How Variables & Memory Actually Work! #Shorts #Python #Animation'
yt_url = f'https://www.youtube.com/shorts/{vid_id}'

db.videos.update_one(
    {'youtube_video_id': vid_id},
    {'$set': {
        'title': video_title,
        'youtube_video_id': vid_id,
        'youtube_url': yt_url,
        'youtube_published_at': now_utc,
        'status': 'PUBLISHED',
        'slot_index': 1,
        'episode': 1,
        'series': 'python_visual_curriculum',
        'created_at': now_utc
    }},
    upsert=True
)

db.publishing_jobs.update_one(
    {'slot_index': 1, 'idempotency_key': {'$regex': '^autopilot_2026-11-14'}},
    {'$set': {
        'state': 'PUBLISHED',
        'youtube_video_id': vid_id,
        'youtube_url': yt_url,
        'youtube_published_at': now_utc,
        'updated_at': now_utc
    }}
)

print('MongoDB records updated successfully for Episode 1!')
print('Video link:', yt_url)

