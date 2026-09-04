"""Real tests for Phase 2: FastAPI skeleton, health checks, and API endpoints."""

from fastapi.testclient import TestClient
from backend.app.main import app

client = TestClient(app)


def test_system_health_endpoint():
    """Verify GET /health returns real system hardware status and operational metrics."""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "HEALTHY"
    assert data["zero_cost_mode"] is True
    assert "system_resources" in data
    assert "ram_available_mb" in data["system_resources"]
    assert "disk_free_gb" in data["system_resources"]


def test_providers_health_endpoint():
    """Verify GET /providers/health executes genuine subsystem checks."""
    response = client.get("/providers/health")
    assert response.status_code == 200
    data = response.json()
    assert "subsystems" in data
    subsystems = data["subsystems"]
    assert "ai" in subsystems
    assert "tts" in subsystems
    assert "stt" in subsystems
    assert "video_rendering" in subsystems
    assert "youtube" in subsystems
    assert "search" in subsystems
    # Subsystem statuses should be genuine string states
    for k, v in subsystems.items():
        assert v["status"] in ["CONNECTED", "NOT_CONFIGURED", "OFFLINE", "BLOCKED_ZERO_COST"]


def test_autopilot_status_and_toggle():
    """Verify GET /api/autopilot/status and start/stop controls."""
    # Status
    res = client.get("/api/autopilot/status")
    assert res.status_code == 200
    status = res.json()
    assert "slot_1_time" in status
    assert "slot_2_time" in status
    assert status["slot_1_time"] == "07:00"
    assert status["slot_2_time"] == "18:00"

    # Stop
    res_stop = client.post("/api/autopilot/stop")
    assert res_stop.status_code == 200
    assert res_stop.json()["is_enabled"] is False

    # Start
    res_start = client.post("/api/autopilot/start")
    assert res_start.status_code == 200
    assert res_start.json()["is_enabled"] is True


def test_manual_video_generation_trigger():
    """Verify POST /api/videos/generate queues a job with deterministic idempotency key."""
    payload = {
        "topic": "5 AI Tools Students Need in 2026",
        "target_duration_sec": 45.0,
        "slot_index": 1
    }
    response = client.post("/api/videos/generate", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "QUEUED"
    assert "job_id" in data
    assert "idempotency_key" in data
    assert len(data["idempotency_key"]) == 64

    # Verify status query for created job
    job_id = data["job_id"]
    status_res = client.get(f"/api/videos/{job_id}/status")
    assert status_res.status_code == 200
    assert status_res.json()["state"] == "QUEUED"


def test_settings_retrieval_and_update():
    """Verify GET /api/settings and PUT /api/settings."""
    get_res = client.get("/api/settings")
    assert get_res.status_code == 200
    settings_data = get_res.json()
    assert settings_data["zero_cost_mode"] is True

    # Update niche
    settings_data["niche"] = "Quantum Computing in 60 Seconds"
    put_res = client.put("/api/settings", json=settings_data)
    assert put_res.status_code == 200
    assert put_res.json()["settings"]["niche"] == "Quantum Computing in 60 Seconds"


def test_analytics_reports_not_available_when_unconnected():
    """Verify that uncollected metrics show NOT AVAILABLE rather than simulated 0."""
    res = client.get("/api/analytics")
    assert res.status_code == 200
    data = res.json()
    metrics = data["metrics"]
    assert metrics["views_28d"] == "NOT AVAILABLE"
    assert metrics["watch_time_hours_28d"] == "NOT AVAILABLE"


def test_style_profile_endpoint():
    """Verify GET /api/style/profile returns valid dual-segment reference baseline."""
    res = client.get("/api/style/profile")
    assert res.status_code == 200
    data = res.json()
    assert data["real_footage_ratio"] == 0.28
    assert data["screen_recording_ratio"] == 0.72
