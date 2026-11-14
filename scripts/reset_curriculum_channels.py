"""Reset both channels for tomorrow morning Lesson 1 start:
Channel 1: Python Master -> Python Programming (Lesson 1)
Channel 2: Bhanu Teja -> C Programming (Lesson 1)
Both running Alan Becker Yellow Stickman SFX Visual Studio (No Voice, Rich SFX).
"""

import sys
import os
from datetime import datetime, timezone
from bson import ObjectId

sys.path.insert(0, os.getcwd())
from backend.app.core.db import SyncMongoDB

db = SyncMongoDB.get_db()
now = datetime.now(timezone.utc)
op_set = chr(36) + "set"

# 1. Reset Main Channel (Python) to Episode 1
db.system_config.update_one(
    {"key": "python_visual_curriculum"},
    {op_set: {"current_episode": 1, "last_published_episode": 0, "updated_at": now}},
    upsert=True
)
db.curriculum_tracker.update_one(
    {"niche": "Python Programming"},
    {op_set: {"current_episode": 1, "last_published_episode": 0, "updated_at": now}},
    upsert=True
)

# 2. Configure Second Channel for C Programming & reset to Episode 1
db.workspaces.update_one(
    {"_id": ObjectId("6a9fd659f2e1cbccfc7a8e84")},
    {op_set: {
        "name": "Bhanu Teja [C Programming Series]",
        "niche": "C Programming",
        "content_template": "c_programming_animation",
        "visual_style": "stickman_yellow_animation",
        "language": "en",
        "voice_provider": "none",
        "updated_at": now
    }}
)
db.curriculum_tracker.delete_many({"niche": "Python in Telugu"})
db.curriculum_tracker.update_one(
    {"niche": "C Programming"},
    {op_set: {"current_episode": 1, "last_published_episode": 0, "updated_at": now}},
    upsert=True
)

print("Curriculum trackers and workspaces updated successfully!")
print("Python Tracker:", db.curriculum_tracker.find_one({"niche": "Python Programming"}, {"_id": 0}))
print("C Tracker:", db.curriculum_tracker.find_one({"niche": "C Programming"}, {"_id": 0}))

