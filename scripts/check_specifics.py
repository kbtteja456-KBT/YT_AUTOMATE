import sys, os
from bson import ObjectId
sys.path.insert(0, r"c:\Users\DELL\OneDrive\Desktop\yt")
from backend.app.core.db import SyncMongoDB

db = SyncMongoDB.get_db()

print("--- DETAILED CHECK ON 6aa3f339e45e4b28f92f1483 ---")
v1 = db.videos.find_one({"_id": ObjectId("6aa3f339e45e4b28f92f1483")})
print("Video 1:", {k: v for k, v in v1.items() if k not in ["qc_report"]})

print("\n--- DETAILED CHECK ON 6aa0b6c547ebf92a8c81ec91 ---")
v2 = db.videos.find_one({"_id": ObjectId("6aa0b6c547ebf92a8c81ec91")})
print("Video 2:", {k: v for k, v in v2.items() if k not in ["qc_report"]})

print("\n--- DETAILED CHECK ON 6aa93a63cbf9cc578f574aad ---")
v3 = db.videos.find_one({"_id": ObjectId("6aa93a63cbf9cc578f574aad")})
print("Video 3:", {k: v for k, v in v3.items() if k not in ["qc_report"]})
if v3 and v3.get("file_path"):
    print("File exists:", os.path.exists(v3["file_path"]), "path:", v3["file_path"])

print("\n--- RECENT JOBS (LAST 10) ---")
for j in db.publishing_jobs.find({}).sort("created_at", -1).limit(10):
    print("Job:", j.get("_id"), j.get("state"), j.get("scheduled_at"), j.get("error") or j.get("error_message"))
