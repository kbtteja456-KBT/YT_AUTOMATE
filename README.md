# AI YouTube Shorts Autopilot (Local & Zero-Cost)

Autonomous, local-first, production-ready system running 24/7 on your own PC to generate, compose, Quality-Control, and publish two high-retention 1080x1920 YouTube Shorts every day (07:00 and 18:00 Asia/Kolkata).

---

## Zero-Cost Guarantee (₹0 by Default)

The application enforces a strict **Zero-Cost Hard Mode** by default (`ZERO_COST_MODE=true`):
- **AI Reasoning**: Free OpenRouter models (`openrouter/free`, `meta-llama/llama-3.3-70b-instruct:free`, `google/gemini-2.0-flash-exp:free`) or local Ollama.
- **Voice / Speech (TTS)**: Microsoft Edge Neural TTS (100% free, natural pacing, male & female voices in 100+ languages) with offline `pyttsx3` fallback.
- **Transcription (STT)**: Local `faster-whisper` running on CPU or GPU for word-level timestamps.
- **Stock Media**: Free licensed stock footage (Pexels Free Tier, Wikimedia Commons, Public Domain) and procedural typography/motion-graphics created directly in FFmpeg/Pillow.
- **Rendering**: Local FFmpeg engine (cuts, Ken Burns pan/zoom, auto-audio-ducking, burned-in animated subtitles).
- **YouTube Publishing**: Official Google YouTube Data API v3 resumable uploader.

Any attempt to call a paid provider while Zero-Cost Mode is active halts with:
`"Paid provider blocked by Zero-Cost Mode."`

---

## Daily Schedule & Pre-Generation Windows

| Slot | Target Publish Time (IST) | Pre-Generation Window | Behavior If Machine Asleep/Off |
| :--- | :--- | :--- | :--- |
| **Morning** | **07:00 AM** | 01:00 AM – 06:30 AM | Marked `MISSED` with timestamped audit |
| **Evening** | **06:00 PM** | 12:00 PM – 05:30 PM | Marked `MISSED` with timestamped audit |

> [!WARNING]
> **Sleep / Hibernate Advisory**: If your workstation is asleep or turned off during the scheduled window, that video will be recorded in the database as `MISSED` (never faked or silently skipped). We strongly recommend setting your PC's power plan to **Never Sleep** while plugged in, or adjusting the schedule in Settings to hours when your PC is active.

---

## Minimum Hardware Requirements

- **CPU**: Modern Quad-Core (Intel Core i5 8th Gen+ / AMD Ryzen 5 3600+ or Apple Silicon)
- **RAM**: 16 GB recommended (minimum 8 GB free for Whisper + FFmpeg)
- **Disk**: ~20 GB free space on SSD for temporary audio/video assets
- **OS**: Windows 10/11, Ubuntu 20.04+, or macOS 12+

---

## One-Command Deployment (Docker Compose)

### 1. Configure Environment
```bash
cp .env.example .env
# Fill in GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET for YouTube publishing
# (Optional: Add OPENROUTER_API_KEY for free-tier LLM models)
```

### 2. Start Services
```bash
docker compose up -d
```
This starts 6 persistent containers:
1. `yt_autopilot_backend`: FastAPI server on port `8000`
2. `yt_autopilot_frontend`: React UI on port `3000`
3. `yt_autopilot_mongo`: MongoDB 7 database on port `27017`
4. `yt_autopilot_redis`: Redis 7 task broker on port `6379`
5. `yt_autopilot_celery_worker`: Background video rendering worker with local FFmpeg
6. `yt_autopilot_celery_beat`: Persistent cron scheduler

---

## Persistent Autostart on Reboot

To guarantee the autopilot survives reboots, power cuts, and restarts:

### 1. Windows (Task Scheduler)
Create a scheduled task that starts Docker Compose automatically on system startup:
1. Open PowerShell as Administrator.
2. Run:
```powershell
$action = New-ScheduledTaskAction -Execute "docker" -Argument "compose -f C:\Users\DELL\OneDrive\Desktop\yt\docker-compose.yml up -d"
$trigger = New-ScheduledTaskTrigger -AtStartup
Register-ScheduledTask -TaskName "YouTubeShortsAutopilot" -Action $action -Trigger $trigger -RunLevel Highest
```

### 2. Linux (systemd)
Create `/etc/systemd/system/yt-autopilot.service`:
```ini
[Unit]
Description=AI YouTube Shorts Autopilot
Requires=docker.service
After=docker.service

[Service]
Type=oneshot
RemainAfterExit=yes
WorkingDirectory=/opt/yt
ExecStart=/usr/bin/docker compose up -d
ExecStop=/usr/bin/docker compose down

[Install]
WantedBy=multi-user.target
```
Enable and start:
```bash
sudo systemctl daemon-reload
sudo systemctl enable yt-autopilot
sudo systemctl start yt-autopilot
```

### 3. macOS (launchd)
Create `~/Library/LaunchAgents/com.user.yt-autopilot.plist`:
```xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.user.yt-autopilot</string>
    <key>ProgramArguments</key>
    <array>
        <string>/usr/local/bin/docker</string>
        <string>compose</string>
        <string>-f</string>
        <string>/Users/youruser/yt/docker-compose.yml</string>
        <string>up</string>
        <string>-d</string>
    </array>
    <key>RunAtLoad</key>
    <true/>
</dict>
</plist>
```
Load the agent:
```bash
launchctl load ~/Library/LaunchAgents/com.user.yt-autopilot.plist
```

---

## Development & Local Testing Without Docker

If running directly in Python:
```bash
# Terminal 1: Backend
uvicorn backend.app.main:app --host 127.0.0.1 --port 8000 --reload

# Terminal 2: Frontend
cd frontend && npm run dev
```

Run test suite:
```bash
python -m pytest backend/tests -v
```
