# AI YouTube Shorts Autopilot — Architecture & Technical Specification

## 1. System Overview

**AI YouTube Shorts Autopilot** is a fully automated, local-first, zero-cost-by-default video publishing engine designed to run 24/7 on a user's workstation (Windows, macOS, Linux). It creates and publishes two original, high-retention 1080x1920 vertical Shorts daily (07:00 and 18:00 Asia/Kolkata), pre-generating them in designated overnight and midday windows.

The application strictly forbids simulated operations. Every published video corresponds to real script generation, real speech synthesis, real transcription, real FFmpeg rendering, real Quality Control (QC) scoring, and real YouTube Data API v3 resumable uploading.

```
                                  +-----------------------+
                                  |   React + TS Frontend |
                                  |   (Port 3000 / Vite)  |
                                  +-----------+-----------+
                                              | HTTP / SSE
                                              v
+-----------------------------------------------------------------------------------------+
|                               FASTAPI BACKEND (Port 8000)                               |
|                                                                                         |
|  - REST API (/api/videos, /api/autopilot, /api/providers, /api/publishing, /api/style)  |
|  - OAuth 2.0 Google Flow & AES-256 Encrypted Token Storage                              |
|  - Real-Time Event Stream (Server-Sent Events)                                          |
|  - Server Restart Reconciler (on_event("startup"))                                      |
|  - System Resource Guard (CPU, RAM, Disk monitors)                                      |
+-----------------------------+-----------------------------------+-----------------------+
                              |                                   |
                              v                                   v
                   +---------------------+             +--------------------+
                   |   REDIS (Port 6379) |             |  MONGODB (27017)   |
                   |   Broker & Locks    |             |  State & Metadata  |
                   +----------+----------+             +---------+----------+
                              |                                   |
                              +-----------------+-----------------+
                                                |
                                                v
+-----------------------------------------------------------------------------------------+
|                              CELERY WORKER & CELERY BEAT                                |
|                                                                                         |
|  Beat Schedules:                                                                        |
|    - 01:00-06:30 Asia/Kolkata: Pre-generate Slot 1 (for 07:00 Publish)                  |
|    - 07:00 Asia/Kolkata: Publish Slot 1 (or mark MISSED)                                |
|    - 12:00-17:30 Asia/Kolkata: Pre-generate Slot 2 (for 18:00 Publish)                  |
|    - 18:00 Asia/Kolkata: Publish Slot 2 (or mark MISSED)                                |
|    - Hourly: Health audits, restart reconciliation, YouTube Analytics sync               |
|                                                                                         |
|  Full Autopilot Pipeline (State Machine):                                               |
|    IDEA -> RESEARCH -> FACT CHECK -> SCRIPT -> HOOK -> STORYBOARD ->                    |
|    VISUAL ASSET COLLECTION -> VOICE -> CAPTIONS -> EDITING -> QUALITY CONTROL ->        |
|    THUMBNAIL -> TITLE -> DESCRIPTION -> PUBLISH -> ANALYTICS -> LEARNING -> NEXT VIDEO  |
|                                                                                         |
|  Content Agents:                                                                        |
|    - IdeaAgent            - ResearchAgent       - FactCheckAgent                        |
|    - HookAgent            - ScriptAgent         - StoryboardAgent                       |
|    - MediaAgent           - VoiceAgent          - CaptionAgent                          |
|    - EditorAgent (FFmpeg) - QCAgent (Score>=90) - ThumbnailAgent                        |
|    - TitleAgent           - DescriptionAgent    - YouTubeAgent                          |
|    - AnalyticsAgent       - LearningAgent       - StyleAnalyzerAgent                    |
+-----------------------------------------------------------------------------------------+
```

---

## 2. Directory Layout

```
yt/
├── architecture.md
├── docker-compose.yml
├── Dockerfile.backend
├── Dockerfile.celery
├── Dockerfile.frontend
├── .env.example
├── README.md
├── scripts/
│   ├── setup_autostart_linux.sh
│   ├── setup_autostart_windows.ps1
│   └── setup_autostart_mac.sh
├── backend/
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py
│   │   ├── config.py
│   │   ├── core/
│   │   │   ├── __init__.py
│   │   │   ├── db.py               # Motor async client & PyMongo sync client
│   │   │   ├── security.py         # Fernet AES-256 encryption & SHA-256 hashing
│   │   │   ├── logging.py          # Structured logging
│   │   │   ├── errors.py           # Custom exception hierarchy
│   │   │   └── resources.py        # CPU/RAM/Disk safeguard
│   │   ├── models/
│   │   │   ├── __init__.py
│   │   │   ├── base.py
│   │   │   ├── user.py
│   │   │   ├── channel.py
│   │   │   ├── job.py              # PublishingJob & JobState enum
│   │   │   ├── video.py            # Video, Scene, Storyboard models
│   │   │   ├── thumbnail.py        # Custom thumbnail specifications
│   │   │   ├── settings.py         # ChannelSettings & AutopilotConfig
│   │   │   ├── style_profile.py    # Reference video pacing ratios
│   │   │   ├── activity.py         # Real-time event log items
│   │   │   └── provider.py         # Provider health & metrics
│   │   ├── providers/
│   │   │   ├── __init__.py
│   │   │   ├── base.py             # Abstract base interfaces & ZeroCost enforcement
│   │   │   ├── ai/                 # OpenRouter free-tier & local Ollama
│   │   │   ├── tts/                # Edge-TTS (free neural) & PyTTSx3 (offline)
│   │   │   ├── stt/                # Faster-Whisper local engine
│   │   │   ├── media/              # Free stock & procedural motion graphics
│   │   │   ├── search/             # DuckDuckGo & Wikipedia
│   │   │   ├── storage/            # Local media disk storage manager
│   │   │   └── youtube/            # Google OAuth2 & YouTube Data API v3
│   │   ├── agents/
│   │   │   ├── __init__.py
│   │   │   ├── base.py             # Base agent with memory and provider bindings
│   │   │   ├── idea.py
│   │   │   ├── research.py
│   │   │   ├── fact_check.py
│   │   │   ├── hook.py
│   │   │   ├── script.py
│   │   │   ├── storyboard.py
│   │   │   ├── media.py
│   │   │   ├── voice.py
│   │   │   ├── caption.py
│   │   │   ├── editor.py           # FFmpeg render orchestrator
│   │   │   ├── qc.py               # Quality Gate (Score >= 90)
│   │   │   ├── thumbnail.py        # Custom text-overlay/frame ThumbnailAgent
│   │   │   ├── title.py
│   │   │   ├── description.py
│   │   │   ├── youtube.py
│   │   │   ├── analytics.py
│   │   │   ├── learning.py
│   │   │   └── style_analyzer.py   # Reference video dual-segment pacing
│   │   ├── pipeline/
│   │   │   ├── __init__.py
│   │   │   ├── orchestrator.py     # State machine executor
│   │   │   ├── reconciliation.py   # Recovery from crashes & power off
│   │   │   └── pattern_interrupt.py # Retention pacing manager
│   │   ├── api/
│   │   │   ├── __init__.py
│   │   │   ├── routes_videos.py
│   │   │   ├── routes_jobs.py
│   │   │   ├── routes_activity.py
│   │   │   ├── routes_analytics.py
│   │   │   ├── routes_calendar.py
│   │   │   ├── routes_providers.py
│   │   │   ├── routes_autopilot.py
│   │   │   ├── routes_settings.py
│   │   │   ├── routes_youtube_auth.py
│   │   │   └── routes_style.py
│   │   └── celery_app/
│   │       ├── __init__.py
│   │       ├── celery.py
│   │       ├── tasks.py
│   │       └── beat_schedule.py
│   ├── requirements.txt
│   └── tests/
│       ├── __init__.py
│       ├── test_schemas.py
│       ├── test_providers.py
│       ├── test_zero_cost.py
│       ├── test_agents.py
│       ├── test_qc.py
│       └── test_reconciliation.py
└── frontend/
    ├── index.html
    ├── package.json
    ├── tsconfig.json
    ├── vite.config.ts
    └── src/
        ├── App.tsx
        ├── index.css
        ├── components/
        ├── pages/
        └── services/
```

---

## 3. MongoDB Schemas & Collections

Database Name: `youtube_autopilot`

### Collections Overview:
1. `users`: Local user credentials and application access.
2. `youtube_channels`: Channel ID, title, custom URL, subscriber count, avatar.
3. `oauth_tokens`: AES-256 encrypted refresh tokens, access tokens, expiry timestamps.
4. `channel_settings`: Schedule (07:00, 18:00), timezone (`Asia/Kolkata`), daily limit (2), niche, voice config, Zero-Cost Mode toggle.
5. `style_profiles`: Reference video metrics (`duration`, `segment_ratios`, `cut_frequency`, `caption_style`).
6. `content_ideas`: Historical idea bank with topic, tags, score, uniqueness hash.
7. `research`: Structured data with `FACT`, `SOURCE`, `INTERPRETATION`.
8. `scripts`: 30-60s script sections (Hook, Problem, Value, Payoff, CTA) and word counts.
9. `hooks`: Hook candidate variations with comparative scores.
10. `storyboards`: Ordered scenes with visual prompt, type, caption text, transition, and timing.
11. `scenes`: Individual visual assets, license tags, and download paths.
12. `media_assets`: Deduplicated cache of downloaded CC/free stock footage.
13. `voice_tracks`: Synthesized audio file paths, durations, waveforms, loudness metrics.
14. `captions`: Whisper-derived word-level and phrase-level timestamp objects.
15. `thumbnails`: Custom rendered thumbnail image path, overlay text, source frame timestamp.
16. `videos`: Rendered 1080x1920 MP4 metadata, file hash, duration, QC score, YouTube ID.
17. `publishing_jobs`: Pipeline execution state machine entries with idempotency keys.
18. `analytics`: Real metrics collected from YouTube Data/Analytics APIs.
19. `agent_runs`: Audit trail of every agent invocation, inputs, outputs, execution duration.
20. `agent_errors`: Error records, stack traces, and automatic remediation attempts.
21. `content_memory`: Channel-specific learning insights, high-retention patterns, topic fatigue counters.
22. `provider_usage`: Provider call counts, token tallies, latency, zero-cost verifications.

---

## 4. Provider Abstraction Layer & Zero-Cost Enforcement

### Provider Interfaces:
- `AIProvider`: Text reasoning, JSON generation, script synthesis.
  - Primary: `OpenRouterProvider` (`openrouter/free` models e.g. `meta-llama/llama-3.3-70b-instruct:free`, `google/gemini-2.0-flash-exp:free`).
  - Fallback: Local Ollama / Transformers.
- `TTSProvider`: Speech synthesis.
  - Primary: `EdgeTTSProvider` (free Microsoft Neural voices: `en-US-ChristopherNeural`, `en-US-JennyNeural`, `en-IN-PrabhatNeural`, `en-IN-NeerjaNeural`).
  - Fallback: `PyTTSx3Provider` (100% offline Windows SAPI5 / Linux eSpeak).
- `STTProvider`: Speech-to-text with word-level timestamps.
  - Primary: `WhisperProvider` (`faster-whisper` running locally on CPU/CUDA).
- `StockMediaProvider`: Free licensed asset sourcing.
  - Sources: DuckDuckGo CC, Wikimedia Commons, Pexels Free Tier, Pixabay Free Tier, and Procedural Motion Graphic Engine (Pillow + FFmpeg).
- `SearchProvider`: Real-time web fact discovery.
  - Sources: DuckDuckGo Search API, Wikipedia API.
- `StorageProvider`: File lifecycle on disk (`media_storage/temp`, `media_storage/rendered`, `media_storage/captions`).
- `YouTubeProvider`: Official Google OAuth2 & YouTube Data API v3 client.

### Hard Zero-Cost Guard:
Before any provider executes:
```python
if settings.zero_cost_mode and not provider.is_zero_cost:
    raise ZeroCostModeViolationError(
        f"Paid provider '{provider.name}' blocked by Zero-Cost Mode."
    )
```

---

## 5. Pipeline State Machine & Job Resumption

```
[CREATED]
    |
    v
[QUEUED]
    |
    v
[RESEARCHING]  ---> [FAILED] (retryable)
    |
    v
[SCRIPTING]
    |
    v
[STORYBOARDING]
    |
    v
[GENERATING_MEDIA]
    |
    v
[GENERATING_VOICE]
    |
    v
[GENERATING_CAPTIONS]
    |
    v
[RENDERING] (FFmpeg 1080x1920 MP4)
    |
    v
[QUALITY_CHECK] ---> [QC_FAILED] (auto-fix up to 3 times)
    | (Score >= 90)
    v
[GENERATING_THUMBNAIL] (Custom text-overlay card / extracted frame)
    |
    v
[READY] (Buffered until scheduled publish time)
    |
    v
[PUBLISHING] (YouTube Data API v3 Resumable Upload)
    |
    v
[PUBLISHED] (Real YouTube video ID confirmed)
```

### Server Restart Reconciliation Rule:
When FastAPI or Celery starts:
1. Scan for jobs stuck in intermediate states (`QUEUED`, `RESEARCHING`, ... `RENDERING`).
2. If the scheduled slot has already passed by more than the configured grace period (default: 30 minutes), mark the job as `MISSED`.
3. If within the pre-generation or grace window, resume from the last completed checkpoint without re-running finished stages.

---

## 6. ThumbnailAgent Specification (Phase 17 Enhancement)

To maximize Click-Through-Rate (CTR) on Shorts and channel shelves, the `ThumbnailAgent` generates a dedicated custom thumbnail card instead of relying on YouTube's arbitrary auto-picked frame:
1. **Frame Extraction**: Extracts the most visually dense frame from the video (typically at the hook payoff around 1.5s - 2.5s).
2. **Text Overlay Generation**: Creates bold, high-contrast, stroke-bordered text (maximum 3-4 punchy words) positioned safely away from YouTube Shorts UI badges (avoid bottom right timer badge and bottom left channel title).
3. **Card Composition**: Applies subtle contrast gradient, saturation boost (+10%), and writes a high-resolution 1080x1920 JPEG (`media_storage/thumbnails/<video_id>.jpg`).
4. **YouTube Upload**: Uploads thumbnail via `youtube.thumbnails().set(videoId=..., media_body=...)`.

---

## 7. Reference Video Style Analysis Specification

During initial onboarding, the user supplies a ~44-second vertical Short.
The `StyleAnalyzerAgent` processes the video using FFprobe and OpenCV:
1. Detects shot boundaries using frame difference metrics.
2. Identifies the split between the initial real-world handheld demo segment and the subsequent screen walkthrough segment (typically at 25-30% mark).
3. Calculates:
   - Total runtime
   - Shot count and average cut interval (e.g. 2.2 seconds per shot)
   - Real-footage to screen-recording ratio (e.g. 28% real : 72% screen)
   - Caption density (words per second) and screen placement
   - Hook pacing (time to first scene transition)
4. Saves values to `style_profile.json` as the structural template for future storyboards.
5. Absolute rule: Only pacing and structure are preserved. Zero footage, audio, or text from the reference video is ever reused.
