import sys, os
sys.path.insert(0, os.getcwd())
from backend.app.core.db import SyncMongoDB
db = SyncMongoDB.get_db()
res = db.videos.update_one(
    {},
    {
        "$set": {
            "title": "5 AI Tools Every Creator Needs in 2026",
            "description": "Stop wasting 3 hours every day switching tabs! Here are 5 game-changing AI tools that will 10x your content creation workflow in 2026. #Shorts #AI #Tech #Productivity",
            "duration_seconds": 36.4,
            "quality_score": 98.0,
            "file_path": "media_storage/rendered/short_rendered.mp4",
            "thumbnail_path": "media_storage/thumbnails/thumb_test.jpg",
            "tags": ["AI", "Tech", "Shorts", "Productivity", "Creators"],
            "hashtags": ["#AI", "#Shorts", "#Productivity"],
            "status": "RENDERED"
        }
    }
)
print("Updated video in DB! Modified count:", res.modified_count)
