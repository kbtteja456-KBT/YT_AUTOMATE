# 🚀 Complete Deployment Guide: Vercel + Render + Daily 7 AM / 6 PM Autopilot

This guide walks you through deploying your **AI YouTube Shorts Autopilot**:
- **Frontend**: Deployed to **Vercel** (Global CDN, 100% Free).
- **Backend**: Deployed to **Render** via Docker (System FFmpeg, Python 3.11, Edge TTS, 100% Free).
- **Database**: **MongoDB Atlas** (Free Tier M0 Sandbox).
- **Daily Autopilot**: Automatically generates & publishes fresh, diverse Shorts at **07:00 AM** and **06:00 PM** IST every day.

---

## 📋 Prerequisites Checklist
1. **GitHub Account**: Your codebase committed and pushed to a GitHub repository.
2. **Vercel Account**: [https://vercel.com](https://vercel.com) (Free).
3. **Render Account**: [https://render.com](https://render.com) (Free).
4. **MongoDB Atlas Account**: [https://mongodb.com/atlas](https://mongodb.com/atlas) (Already configured in your `.env`!).

---

## Part 1: Deploy Backend to Render

1. Log in to [Render.com](https://dashboard.render.com).
2. Click **New +** in the top right and select **Web Service**.
3. Choose **Build and deploy from a Git repository** and connect your GitHub repo.
4. Fill in the service details:
   - **Name**: `youtube-shorts-autopilot-backend` (or any name you prefer)
   - **Region**: Choose the closest region (e.g. *Oregon* or *Frankfurt*)
   - **Branch**: `main` (or `master`)
   - **Runtime**: Select **Docker** (Render will automatically detect `Dockerfile.backend`).
   - **Instance Type**: **Free** ($0/month).
5. Scroll down to **Environment Variables** and add the following keys from your `.env`:

| Key | Value / Instructions |
| :--- | :--- |
| `ZERO_COST_MODE` | `true` |
| `TIMEZONE` | `Asia/Kolkata` |
| `MONGODB_URI` | `mongodb+srv://kbtteja456_db_user:%40bhanuteja@cluster0.oydktdy.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0` |
| `ENCRYPTION_KEY` | *(Your 32-byte urlsafe base64 key from `.env`)* |
| `GOOGLE_CLIENT_ID` | `952200459265-ddv16n86gm08tscu7hlutru1ug916k0s.apps.googleusercontent.com` |
| `GOOGLE_CLIENT_SECRET` | *(Your client secret from `.env`)* |
| `YOUTUBE_REDIRECT_URI` | `https://<YOUR-RENDER-APP-NAME>.onrender.com/api/auth/youtube/callback` |
| `PIXABAY_API_KEY` | *(Your Pixabay key from `.env`)* |
| `OPENROUTER_API_KEY` | *(Your OpenRouter key from `.env`)* |
| `AUTOPILOT_CRON_SECRET` | `autopilot_secret_bhanu_2026` *(or any password you choose)* |

6. Click **Deploy Web Service**.
7. Once deployed, Render will provide your public URL:
   `https://<your-render-app-name>.onrender.com`
8. **Update Google Cloud Console**:
   - Go to [Google Cloud Console Credentials](https://console.cloud.google.com/apis/credentials).
   - Click on your OAuth 2.0 Client ID.
   - Under **Authorized redirect URIs**, click **+ Add URI** and add:
     `https://<your-render-app-name>.onrender.com/api/auth/youtube/callback`
   - Click **Save**.

---

## Part 2: Deploy Frontend to Vercel

1. Log in to [Vercel.com](https://vercel.com).
2. Click **Add New...** -> **Project**.
3. Import your GitHub repository.
4. Configure Project Settings:
   - **Framework Preset**: `Vite` (auto-detected).
   - **Root Directory**: Click *Edit* and select **`frontend`**.
   - **Build Command**: `npm run build` (auto-detected).
   - **Output Directory**: `dist` (auto-detected).
5. Expand the **Environment Variables** section and add:

| Key | Value |
| :--- | :--- |
| `VITE_API_URL` | `https://<your-render-app-name>.onrender.com` *(from Part 1)* |

6. Click **Deploy**.
7. Within 60 seconds, your site will be live at `https://<your-app-name>.vercel.app`!

---

## Part 3: Daily Autonomous 7:00 AM & 6:00 PM Publishing

Your backend includes an **autonomous scheduler** (`cron_scheduler.py`) running inside the service. However, because Render's free tier spins down after 15 minutes of inactivity, we provide two foolproof, free ways to guarantee execution at 7 AM & 6 PM every single day:

### Option A: GitHub Actions (Built-in, Zero Setup)
A workflow has been pre-configured in [`.github/workflows/daily_autopilot.yml`](file:///c:/Users/DELL/OneDrive/Desktop/yt/.github/workflows/daily_autopilot.yml).
1. Go to your GitHub Repository -> **Settings** -> **Secrets and variables** -> **Actions**.
2. Add two repository secrets:
   - `RENDER_BACKEND_URL`: `https://<your-render-app-name>.onrender.com`
   - `AUTOPILOT_CRON_SECRET`: The same secret you set in Render (e.g. `autopilot_secret_bhanu_2026`).
3. GitHub Actions will automatically wake up your Render service and trigger publishing at:
   - **07:00 AM IST** (01:30 UTC) -> Slot 1
   - **06:00 PM IST** (12:30 UTC) -> Slot 2

### Option B: Free External Cron (cron-job.org)
1. Go to [cron-job.org](https://cron-job.org) and create a free account.
2. Create **Job 1 (Morning 7 AM IST)**:
   - **URL**: `https://<your-render-app-name>.onrender.com/api/autopilot/run-slot/1`
   - **Execution Schedule**: Every day at `07:00` (select Timezone: `Asia/Kolkata`)
   - **Request Method**: `POST`
   - **Headers**:
     - `Content-Type`: `application/json`
     - `x-autopilot-secret`: `your-autopilot-secret`
3. Create **Job 2 (Evening 6 PM IST)**:
   - **URL**: `https://<your-render-app-name>.onrender.com/api/autopilot/run-slot/2`
   - **Execution Schedule**: Every day at `18:00` (select Timezone: `Asia/Kolkata`)
   - **Request Method**: `POST`
   - **Headers**:
     - `Content-Type`: `application/json`
     - `x-autopilot-secret`: `your-autopilot-secret`

---

## 🎯 What Happens Every Day?
Every morning at 7:00 AM and every evening at 6:00 PM:
1. The pipeline automatically selects a **fresh, diverse topic** from the topic rotation pool (AI Tools, Coding Hacks, Future Inventions, Cybersecurity, Productivity).
2. Synthesizes a studio-grade neural voiceover via **Microsoft Edge Neural Speech**.
3. Downloads high-definition matching video clips from **Pixabay**.
4. Renders a full **1080x1920 vertical Short** with animated subtitles and background music using **FFmpeg**.
5. Publishes the video directly to your YouTube channel (**Bhanu Teja**) with tags and description.
6. The video immediately shows as **`Published to YouTube`** on your Vercel dashboard!
