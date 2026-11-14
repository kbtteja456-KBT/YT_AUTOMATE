import sys
import os
import json

sys.path.insert(0, os.getcwd())
from backend.app.core.db import SyncMongoDB

db = SyncMongoDB.get_db()

with open('media_storage/latest_analytics_snapshot.json', 'r') as f:
    data = json.load(f)

pm_vids = [v for v in data.values() if v.get('channelId') == 'UCBQAktpydJEze5CmEbeJBRQ']
below_100_ids = [v['id'] for v in pm_vids if v.get('views', 0) < 100]

res_v = db.videos.delete_many({'youtube_video_id': {'$in': below_100_ids}})
res_j = db.publishing_jobs.delete_many({'youtube_video_id': {'$in': below_100_ids}})

print(f"Purged {res_v.deleted_count} video records from MongoDB db.videos.")
print(f"Purged {res_j.deleted_count} job records from MongoDB db.publishing_jobs.")

