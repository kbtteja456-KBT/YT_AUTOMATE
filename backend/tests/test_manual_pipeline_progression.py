from datetime import datetime, timezone

import mongomock
from fastapi.testclient import TestClient
from unittest.mock import patch

from backend.app.main import app
from backend.app.celery_app.tasks import run_pipeline_task


def test_manual_generate_creates_job_and_task_advances_it_to_ready():
    mock_db = mongomock.MongoClient()["youtube_autopilot"]

    with patch("backend.app.core.db.SyncMongoDB.get_db", return_value=mock_db), \
         patch("backend.app.api.routes_videos.SyncMongoDB.get_db", return_value=mock_db), \
         patch("backend.app.celery_app.tasks.SyncMongoDB.get_db", return_value=mock_db), \
         patch("backend.app.celery_app.tasks.run_pipeline_task.delay", side_effect=lambda job_id: run_pipeline_task(job_id)), \
         patch("backend.app.api.routes_videos._dispatch_pipeline_job"):
        client = TestClient(app)
        response = client.post("/api/videos/generate", json={"topic": "AI tools", "target_duration_sec": 45.0, "slot_index": 1})

        assert response.status_code == 200, response.text
        payload = response.json()
        assert payload["status"] == "QUEUED"
        job_id = payload["job_id"]

        doc = mock_db.publishing_jobs.find_one({"_id": job_id})
        assert doc is not None
        assert doc["state"] == "CREATED"

        result = run_pipeline_task(job_id)
        assert result["status"] in {"READY", "FAILED"}

        doc_after = mock_db.publishing_jobs.find_one({"_id": job_id})
        assert doc_after is not None
        assert doc_after["state"] in {"READY", "FAILED"}
        assert doc_after.get("stage_logs")
        assert doc_after["state"] != "QUEUED"
