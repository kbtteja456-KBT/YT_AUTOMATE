import sys, os
from datetime import datetime, timezone, timedelta
import zoneinfo

sys.path.insert(0, r"c:\Users\DELL\OneDrive\Desktop\yt")
from backend.app.core.db import SyncMongoDB

db = SyncMongoDB.get_db()
tz = zoneinfo.ZoneInfo("Asia/Kolkata")
now = datetime.now(tz)

print("=" * 70)
print(f"📊 AUTOPILOT VIDEO POSTING TIMELINESS & STATUS REPORT")
print(f"Report Generated At: {now.strftime('%Y-%m-%d %I:%M:%S %p')} IST")
print("=" * 70)

workspaces = {str(w["_id"]): w for w in db.workspaces.find({})}

# Let's inspect the last 5 days
days_to_check = [now.date() - timedelta(days=i) for i in range(5)]

for target_date in days_to_check:
    target_start_ist = datetime(target_date.year, target_date.month, target_date.day, 0, 0, 0, tzinfo=tz)
    target_end_ist = target_start_ist + timedelta(days=1)
    
    start_utc = target_start_ist.astimezone(timezone.utc)
    end_utc = target_end_ist.astimezone(timezone.utc)
    
    print(f"\n📅 DATE: {target_date.strftime('%Y-%m-%d (%A)')}")
    print("-" * 70)
    
    # Query jobs created/scheduled for this day
    jobs = list(db.publishing_jobs.find({
        "$or": [
            {"created_at": {"$gte": start_utc, "$lt": end_utc}},
            {"scheduled_at": {"$gte": start_utc, "$lt": end_utc}}
        ]
    }).sort("created_at", 1))
    
    if not jobs:
        print("  ⚠️ No publishing jobs recorded for this day.")
        continue
        
    for j in jobs:
        ws_id = str(j.get("workspace_id") or "")
        ws = workspaces.get(ws_id)
        ws_name = ws.get("name") if ws else "Platform Owner (Default Channel)"
        
        slot = j.get("slot_index")
        expected_time_str = "07:00 AM IST" if slot == 1 else "06:00 PM IST" if slot == 2 else f"Slot {slot}"
        
        state = j.get("state")
        created = j.get("created_at")
        created_ist = created.replace(tzinfo=timezone.utc).astimezone(tz) if created else None
        
        pub = j.get("published_at")
        pub_ist = pub.replace(tzinfo=timezone.utc).astimezone(tz) if (pub and isinstance(pub, datetime)) else None
        
        # Check associated video
        v = db.videos.find_one({"job_id": str(j["_id"])}) or (db.videos.find_one({"_id": j.get("video_id")}) if j.get("video_id") else None)
        yt_id = (v.get("youtube_video_id") if v else None) or j.get("youtube_video_id")
        title = (v.get("title") if v else None) or j.get("topic")
        
        if pub_ist:
            actual_time_str = pub_ist.strftime('%I:%M:%S %p IST')
        elif created_ist:
            actual_time_str = f"Created at {created_ist.strftime('%I:%M:%S %p IST')} (Pub time not stored in job)"
        else:
            actual_time_str = "N/A"
            
        print(f"  • Slot {slot} ({expected_time_str}) -> Workspace: [{ws_name}]")
        print(f"    - State: {state}")
        print(f"    - Video Title: {title}")
        print(f"    - YouTube ID: {yt_id if yt_id else 'None'}")
        print(f"    - Job Created At: {created_ist.strftime('%Y-%m-%d %I:%M:%S %p') if created_ist else 'N/A'}")
        print(f"    - Published At:   {pub_ist.strftime('%Y-%m-%d %I:%M:%S %p') if pub_ist else (actual_time_str if state == 'PUBLISHED' else 'Not Published')}")
        if j.get("error_message"):
            print(f"    - Error: {j.get('error_message')}")
