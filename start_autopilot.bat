@echo off
cd /d "%~dp0"
title AI YouTube Shorts Autopilot Backend
set PYTHONUNBUFFERED=1
"C:\Users\DELL\AppData\Local\Programs\Python\Python314\python.exe" -m uvicorn backend.app.main:app --host 127.0.0.1 --port 8000 --log-level info
