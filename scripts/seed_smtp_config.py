import sys
import os
from datetime import datetime, timezone

sys.path.insert(0, r"c:\Users\DELL\OneDrive\Desktop\yt")
from backend.app.core.db import SyncMongoDB
from backend.app.config import settings

def seed_smtp():
    db = SyncMongoDB.get_db()
    smtp_doc = {
        "key": "smtp_config",
        "smtp_host": settings.smtp_host or "smtp.gmail.com",
        "smtp_port": settings.smtp_port or 587,
        "smtp_user": (settings.smtp_user or "kbtteja456@gmail.com").strip(),
        "smtp_password": (settings.smtp_password or "veoqqgwswqqrekrd").strip().replace(" ", ""),
        "smtp_from_name": settings.smtp_from_name or "YouTube Shorts Autopilot",
        "updated_at": datetime.now(timezone.utc)
    }
    db.system_config.update_one({"key": "smtp_config"}, {"$set": smtp_doc}, upsert=True)
    print("✅ Successfully seeded SMTP credentials into MongoDB 'system_config' collection.")
    saved = db.system_config.find_one({"key": "smtp_config"})
    print(f"Stored user: {saved.get('smtp_user')}, port: {saved.get('smtp_port')}, pass set: {bool(saved.get('smtp_password'))}")

if __name__ == "__main__":
    seed_smtp()
