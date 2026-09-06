# ☁️ 24/7 Cloud External Triggering Guide: Zero-Laptop YouTube Shorts Autopilot

This guide explains how to configure a **100% free external cloud scheduler** (like [cron-job.org](https://cron-job.org)) to trigger your YouTube Shorts publishing every day at **07:00 AM IST** and **06:00 PM IST**, even when your laptop is completely powered off and disconnected.

---

## 🎯 Architecture Overview

```
cron-job.org (Free Cloud Scheduler)
      │
      │ HTTP POST (Asia/Kolkata 07:00 & 18:00)
      ▼
GitHub Repository Dispatch API
      │
      ▼
GitHub Actions Runner (Ubuntu Linux in Cloud)
      ├─ Pulls code & connects to MongoDB Atlas
      ├─ Acquires atomic slot concurrency lock (prevents duplicate runs)
      ├─ Generates Python Quiz / AI Tech Short
      ├─ Synthesizes voice & dynamic captions
      ├─ Renders 1080x1920 Short via FFmpeg
      ├─ Audits Quality Score (>= 90 required)
      ├─ Uploads via YouTube Data API v3
      └─ Verifies live YouTube video ID
```

---

## 📋 Step 1: Generate a GitHub Personal Access Token (PAT)

Your external scheduler needs permission to trigger workflows in your repository (`https://github.com/kbtteja456-KBT/YT_AUTOMATE`).

1. Log in to your GitHub account: [https://github.com](https://github.com).
2. Go to **Settings** -> **Developer settings** -> **Personal access tokens** -> **Tokens (classic)**:
   - Direct link: [https://github.com/settings/tokens/new](https://github.com/settings/tokens/new)
3. Fill in the token details:
   - **Note**: `YouTube Shorts Autopilot Cloud Trigger`
   - **Expiration**: `No expiration` (or your preferred duration)
   - **Select scopes**: Check **`repo`** (Full control of private repositories) or at minimum `repo:status` and `public_repo` (if public).
4. Click **Generate token**.
5. **Copy and save your token** (it looks like `ghp_xxxxxxxxxxxxxxxxxxxx`).
   *(Never commit this token into your code!)*

---

## ⏰ Step 2: Set Up Free Cron Jobs on cron-job.org

1. Create a free account at [https://cron-job.org](https://cron-job.org) and log in.
2. In the dashboard, click **CREATE CRONJOB**.

### Job 1: Morning Slot 1 (07:00 AM IST)
- **Title**: `YT Shorts - Morning Slot 1 (07:00 AM IST)`
- **URL**: `https://api.github.com/repos/kbtteja456-KBT/YT_AUTOMATE/dispatches`
- **Execution Schedule**:
  - Select **User-defined** or **Every day at**
  - **Time**: `06:55` or `07:00` (Recommend `06:55` so rendering completes by 07:00)
  - **Timezone**: Select **`Asia/Kolkata`**
- **Request Method**: `POST`
- **Request Headers**: (Click *Add Header* for each)
  - `Accept`: `application/vnd.github.v3+json`
  - `Authorization`: `Bearer YOUR_GITHUB_PAT_HERE` *(replace with token from Step 1)*
  - `Content-Type`: `application/json`
  - `User-Agent`: `CronJob-Autopilot`
- **Request Body**:
  ```json
  {"event_type": "publish_slot_1"}
  ```
- Click **CREATE**.

---

### Job 2: Evening Slot 2 (06:00 PM IST)
- **Title**: `YT Shorts - Evening Slot 2 (06:00 PM IST)`
- **URL**: `https://api.github.com/repos/kbtteja456-KBT/YT_AUTOMATE/dispatches`
- **Execution Schedule**:
  - **Time**: `17:55` or `18:00` (Recommend `17:55` so rendering completes by 18:00)
  - **Timezone**: Select **`Asia/Kolkata`**
- **Request Method**: `POST`
- **Request Headers**:
  - `Accept`: `application/vnd.github.v3+json`
  - `Authorization`: `Bearer YOUR_GITHUB_PAT_HERE`
  - `Content-Type`: `application/json`
  - `User-Agent`: `CronJob-Autopilot`
- **Request Body**:
  ```json
  {"event_type": "publish_slot_2"}
  ```
- Click **CREATE**.

---

## 🔒 Duplicate Protection & Concurrency Guarantee

Even if multiple triggers fire around the same time:
- External Webhook: 06:55 AM IST
- GitHub Backup Cron: 06:45 AM IST
- GitHub Backup Cron: 06:55 AM IST
- GitHub Backup Cron: 07:00 AM IST

**Your channel will ONLY publish ONE video.**

The MongoDB Atlas atomic locking system guarantees:
1. **Active Runner Lock**: If Runner 1 is already generating or rendering the video, subsequent runners detect the active lock and exit immediately with status `ALREADY_RUNNING`.
2. **Published Lock**: Once the video is published, any subsequent runner sees `ALREADY_PUBLISHED` and skips execution.
3. **Pre-Upload Duplicate Hash Detection**: Before uploading, the video file's SHA-256 hash is checked against all previously published videos to block duplicates.

---

## 🧪 Testing Your Cloud Trigger Right Now

You can test the external dispatch trigger directly from your terminal (or PowerShell) without waiting for 7 AM or 6 PM:

### Test Health Check:
```bash
curl -X POST https://api.github.com/repos/kbtteja456-KBT/YT_AUTOMATE/dispatches \
  -H "Accept: application/vnd.github.v3+json" \
  -H "Authorization: Bearer YOUR_GITHUB_PAT_HERE" \
  -H "Content-Type: application/json" \
  -H "User-Agent: Curl-Test" \
  -d '{"event_type": "health_check"}'
```

### Test Morning Slot:
```bash
curl -X POST https://api.github.com/repos/kbtteja456-KBT/YT_AUTOMATE/dispatches \
  -H "Accept: application/vnd.github.v3+json" \
  -H "Authorization: Bearer YOUR_GITHUB_PAT_HERE" \
  -H "Content-Type: application/json" \
  -H "User-Agent: Curl-Test" \
  -d '{"event_type": "publish_slot_1"}'
```

### Viewing Live Cloud Logs:
1. Open your repository on GitHub: [https://github.com/kbtteja456-KBT/YT_AUTOMATE](https://github.com/kbtteja456-KBT/YT_AUTOMATE).
2. Click on the **Actions** tab.
3. You will see the workflow run executing live with prominent stage banners:
   - `[STAGE: TRIGGERED]`
   - `[STAGE: GENERATING]`
   - `[STAGE: RENDERING]`
   - `[STAGE: QC]`
   - `[STAGE: UPLOADING]`
   - `[STAGE: PUBLISHED]`
