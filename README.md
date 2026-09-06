# AI YouTube Shorts Autopilot — Python Quiz Factory

Autonomous, production-ready system that generates, quality-controls, and publishes two
AI-verified Python quiz YouTube Shorts every day (07:00 and 18:00 Asia/Kolkata).

**Primary scheduler: GitHub Actions** (runs in Google's cloud — zero laptop uptime required).
**Secondary scheduler: Local laptop** (documented as fallback; uptime constraints apply — see warning below).

---

## How Videos Are Generated

Every video follows the real production pipeline — no generic tech topics, no hardcoded scores:

1. **IdeaAgent** — 38-concept Python quiz pool with 25-video anti-repetition memory
2. **ResearchAgent + FactCheckAgent** — code snippet sandboxed verification in isolated subprocess
3. **VoiceAgent** — licensed background music (Incompetech CC BY 4.0 / FMA CC0), normalized to -14 LUFS
4. **EditorAgent** — FFmpeg quiz card compositor (code + 4 answer options)
5. **QCAgent** — real quality score (never hardcoded); must pass ≥ 90/100 to publish
6. **YouTubeAgent** — real YouTube Data API v3 resumable uploader; hard-asserts real video ID

---

## Zero-Cost Guarantee (₹0 by Default)

The application enforces a strict **Zero-Cost Hard Mode** by default (`ZERO_COST_MODE=true`):
- **AI Reasoning**: Free OpenRouter models (`meta-llama/llama-3.3-70b-instruct:free`, `google/gemini-2.0-flash-exp:free`) or local Ollama
- **Voice / Speech (TTS)**: Microsoft Edge Neural TTS (100% free) with offline `pyttsx3` fallback
- **Transcription (STT)**: Local `faster-whisper` (CPU/GPU) for word-level timestamps
- **Stock Media**: Pexels Free Tier, Wikimedia Commons, procedural FFmpeg motion graphics
- **Background Music**: Incompetech (CC BY 4.0, attribution auto-appended to description) + FMA CC0 if `FMA_API_KEY` set
- **Rendering**: Local FFmpeg (Ken Burns pan/zoom, auto-audio-ducking, burned-in animated subtitles)
- **Publishing**: Official YouTube Data API v3 resumable uploader

Any attempt to call a paid provider while Zero-Cost Mode is active halts with:
`"Paid provider blocked by Zero-Cost Mode."`

---

## Music Licensing Policy

The system uses only legally verified royalty-free tracks:

| Source | License | Attribution Required? | How Used |
|---|---|---|---|
| Incompetech / Kevin MacLeod | CC BY 4.0 | **Yes** | Credit auto-appended to YouTube description |
| Free Music Archive (FMA) | CC0 Public Domain | No | Requires `FMA_API_KEY` in `.env` |
| FFmpeg procedural tone | Public domain (synthesized) | No | Used if no pool tracks available |

CC BY tracks automatically include this credit in every published video's description:
```
Music: "<track title>" by Kevin MacLeod (incompetech.com)
Licensed under Creative Commons: By Attribution 4.0
https://creativecommons.org/licenses/by/4.0/
```

---

## Primary Scheduler: GitHub Actions (Recommended)

> [!IMPORTANT]
> **GitHub Actions is the recommended deployment path.** It runs in Google's cloud on ephemeral
> Ubuntu runners — your laptop can be completely off and videos will still publish on schedule.

### Required GitHub Secrets

Go to your repo → **Settings → Secrets and variables → Actions** and add:

| Secret | Description |
|---|---|
| `MONGODB_URI` | MongoDB Atlas connection string (must be cloud-hosted — Atlas, NOT localhost) |
| `ENCRYPTION_KEY` | Fernet key: `python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"` |
| `GOOGLE_CLIENT_ID` | Google OAuth 2.0 Client ID |
| `GOOGLE_CLIENT_SECRET` | Google OAuth 2.0 Client Secret |
| `PEXELS_API_KEY` | Pexels free tier API key |
| `OPENROUTER_API_KEY` | OpenRouter free tier key |

> [!CAUTION]
> `MONGODB_URI` must point to **MongoDB Atlas** (or another cloud-hosted MongoDB reachable from
> GitHub's runners). A `localhost` or LAN URI will always fail in GitHub Actions because
> the ephemeral runner cannot reach your home network. OAuth tokens, anti-repetition history,
> and idempotency keys are all stored in this database — it must be persistent and cloud-reachable.

### Schedule

The workflow fires automatically at:

| Slot | Target Time (IST) | UTC Cron |
|---|---|---|
| Morning | 07:00 AM | `15 1`, `25 1`, `30 1 * * *` |
| Evening | 06:00 PM | `15 12`, `25 12`, `30 12 * * *` |

Multiple cron triggers ensure at least one runner starts on time despite GitHub's scheduling jitter.
MongoDB idempotency keys automatically skip duplicate runs if multiple runners fire.

### Manual Trigger

1. Go to your repo → **Actions → "24/7 Cloud YouTube Shorts Autopilot"**
2. Click **Run workflow**
3. Select slot (0 = auto-detect, 1 = morning, 2 = evening)
4. Click **Run workflow**

---

## Secondary / Fallback: Local Laptop

> [!WARNING]
> **Uptime requirement**: The laptop must remain **awake and plugged in** during:
> - `01:00 – 07:00 IST` (Morning slot pre-generation + publish window)
> - `12:00 – 18:00 IST` (Evening slot pre-generation + publish window)
>
> If the machine sleeps or powers off during these windows, that slot is recorded as `MISSED`
> in MongoDB (never faked or silently skipped). **Software cannot schedule tasks while the host
> is powered off.** Use GitHub Actions (above) or a VPS for guaranteed uptime.
>
> **VPS alternative**: Any cloud VPS (DigitalOcean Droplet $6/mo, Oracle Free Tier ARM instance)
> running Docker Compose provides 24/7 uptime without managing laptop power settings.

### Windows Power Settings (Required for Local Deployment)

To keep your laptop awake during scheduling windows:
```powershell
# Prevent sleep while plugged in (run as Administrator)
powercfg /change standby-timeout-ac 0
powercfg /change hibernate-timeout-ac 0
```

Or manually: **Control Panel → Power Options → Change plan settings → Never sleep** (plugged in).

### Run Locally (Manual / Testing)

```bash
# 1. Copy and fill environment
cp .env.example .env
# Set ENCRYPTION_KEY, MONGODB_URI (Atlas), GOOGLE_CLIENT_ID, GOOGLE_CLIENT_SECRET

# 2. Start all services
docker compose up -d

# 3. Manual trigger (Morning slot)
python run_slot_cli.py --slot 1

# 4. Manual trigger (Evening slot)  
python run_slot_cli.py --slot 2

# 5. Force re-publish (bypass today's published check)
python run_slot_cli.py --slot 1 --force
```

### Persistent Autostart on Reboot (Windows Task Scheduler)

```powershell
$action = New-ScheduledTaskAction -Execute "docker" -Argument "compose -f C:\Users\DELL\OneDrive\Desktop\yt\docker-compose.yml up -d"
$trigger = New-ScheduledTaskTrigger -AtStartup
Register-ScheduledTask -TaskName "YouTubeShortsAutopilot" -Action $action -Trigger $trigger -RunLevel Highest
```

---

## Daily Schedule & State Machine

| Slot | Pre-Generate Window | Publish Time (IST) | Behavior If Machine Asleep/Off |
|---|---|---|---|
| **Morning** | 01:00 – 06:30 AM | **07:00 AM** | Marked `MISSED` with timestamped audit |
| **Evening** | 12:00 – 05:30 PM | **06:00 PM** | Marked `MISSED` with timestamped audit |

---

## One-Command Deployment (Docker Compose)

```bash
cp .env.example .env
# Edit .env — required: ENCRYPTION_KEY, MONGODB_URI (Atlas), GOOGLE_CLIENT_ID, GOOGLE_CLIENT_SECRET
docker compose up -d
```

This starts 6 containers:
1. `yt_autopilot_backend`: FastAPI on port `8000`
2. `yt_autopilot_frontend`: React UI on port `3000`
3. `yt_autopilot_mongo`: MongoDB 7 (local dev only — use Atlas for production)
4. `yt_autopilot_redis`: Redis 7 task broker
5. `yt_autopilot_celery_worker`: Background rendering worker
6. `yt_autopilot_celery_beat`: Persistent cron scheduler

---

## Minimum Hardware Requirements

- **CPU**: Quad-Core (Intel i5 8th Gen+ / AMD Ryzen 5 3600+ / Apple Silicon)
- **RAM**: 16 GB recommended (8 GB minimum for Whisper + FFmpeg)
- **Disk**: ~20 GB free SSD space for audio/video assets

---

## Development & Testing

```bash
# Backend (without Docker)
uvicorn backend.app.main:app --host 127.0.0.1 --port 8000 --reload

# Frontend
cd frontend && npm run dev

# Run test suite
python -m pytest backend/tests -v

# Verify no mock in orchestrator, no legacy pipeline refs
grep -r "run_autopilot_pipeline\|MagicMock\|Pixabay Free Stack\|mluedke2" backend/ run_slot_cli.py
# Expected: zero results
```
