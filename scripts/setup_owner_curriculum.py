import sys
import os
sys.path.insert(0, os.getcwd())
from backend.app.core.db import SyncMongoDB
from datetime import datetime, timezone

db = SyncMongoDB.get_db()

db.workspaces.update_one(
    {"is_legacy_default": True},
    {"$set": {
        "content_template": "alan_becker_animation",
        "preferred_format": "alan_becker_animation",
        "settings.content_template": "alan_becker_animation",
        "settings.preferred_format": "alan_becker_animation",
        "updated_at": datetime.now(timezone.utc)
    }}
)

db.system_config.update_one(
    {"key": "python_visual_curriculum"},
    {"$set": {
        "current_episode": 1,
        "last_published_episode": 0,
        "series_title": "Python Visual Series (Alan Becker Style)",
        "updated_at": datetime.now(timezone.utc)
    }},
    upsert=True
)

ws = db.workspaces.find_one({"is_legacy_default": True})
curr = db.system_config.find_one({"key": "python_visual_curriculum"})
print("SUCCESS!")
print("Workspace Settings:", ws.get("settings"))
print("Curriculum Tracker:", curr)
