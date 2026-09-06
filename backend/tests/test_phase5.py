"""Real unit tests for Phase 5: Google OAuth 2.0 and token encryption."""

import pytest
from unittest.mock import patch, AsyncMock
from fastapi.testclient import TestClient

from backend.app.main import app
from backend.app.core.oauth import GoogleOAuthManager, DEFAULT_SCOPES
from backend.app.core.errors import YouTubeAPIError
from backend.app.core.security import decrypt_token, encrypt_token

client = TestClient(app)


def test_authorization_url_generation():
    """Verify Google OAuth URL contains required offline access, consent prompt, and scopes."""
    client_id = "test-client-id-123.apps.googleusercontent.com"
    redirect_uri = "http://localhost:8000/api/auth/youtube/callback"

    auth_url = GoogleOAuthManager.get_authorization_url(
        client_id=client_id,
        redirect_uri=redirect_uri
    )

    assert "accounts.google.com/o/oauth2/v2/auth" in auth_url
    assert "access_type=offline" in auth_url
    assert "prompt=consent" in auth_url
    assert f"client_id={client_id}" in auth_url
    assert "youtube.upload" in auth_url


def test_authorization_url_missing_client_id():
    """Verify exception is raised when client_id is absent."""
    with patch("backend.app.core.oauth.settings.google_client_id", ""):
        with pytest.raises(YouTubeAPIError):
            GoogleOAuthManager.get_authorization_url(client_id="")


@pytest.mark.anyio
async def test_token_exchange_and_encryption():
    """Verify authorization code is exchanged and refresh token is encrypted."""
    mock_token_resp = {
        "access_token": "mock_access_token_abc",
        "refresh_token": "mock_secret_refresh_token_xyz_12345",
        "expires_in": 3600,
        "token_type": "Bearer",
        "scope": "https://www.googleapis.com/auth/youtube.upload"
    }

    with patch("httpx.AsyncClient.post") as mock_post:
        mock_post.return_value = AsyncMock(status_code=200, json=lambda: mock_token_resp)

        tokens = await GoogleOAuthManager.exchange_code_for_tokens(
            code="mock_auth_code_999",
            client_id="cid",
            client_secret="csec",
            redirect_uri="http://localhost:8000/callback"
        )

        assert tokens["access_token"] == "mock_access_token_abc"
        assert tokens["refresh_token"] == "mock_secret_refresh_token_xyz_12345"

        # Encrypt token
        encrypted = encrypt_token(tokens["refresh_token"])
        assert encrypted != tokens["refresh_token"]
        # Decrypt token
        decrypted = decrypt_token(encrypted)
        assert decrypted == tokens["refresh_token"]


@pytest.mark.anyio
async def test_channel_profile_parsing():
    """Verify YouTube Data API channel response parsing."""
    mock_api_resp = {
        "items": [
            {
                "id": "UC_AI_AUTOPILOT_TEST",
                "snippet": {
                    "title": "AI Tech Insights",
                    "description": "Daily automated shorts",
                    "customUrl": "@aitechinsights"
                },
                "statistics": {
                    "subscriberCount": "14200",
                    "viewCount": "890000",
                    "videoCount": "42"
                }
            }
        ]
    }

    with patch("httpx.AsyncClient.get") as mock_get:
        mock_get.return_value = AsyncMock(status_code=200, json=lambda: mock_api_resp)

        profile = await GoogleOAuthManager.fetch_channel_profile("valid_token")
        assert profile["channel_id"] == "UC_AI_AUTOPILOT_TEST"
        assert profile["title"] == "AI Tech Insights"
        assert profile["subscriber_count"] == 14200
        assert profile["view_count"] == 890000
        assert profile["video_count"] == 42


def test_youtube_connect_endpoint():
    """Verify POST /api/auth/youtube/connect returns authorization url."""
    with patch("backend.app.core.oauth.settings.google_client_id", "my-test-client-id.apps.googleusercontent.com"):
        res = client.post("/api/auth/youtube/connect")
        assert res.status_code == 200
        data = res.json()
        assert "auth_url" in data
        assert "accounts.google.com" in data["auth_url"]


def test_youtube_channel_endpoint_unconnected():
    """Verify GET /api/auth/youtube/channel reports not connected cleanly."""
    with patch("backend.app.api.routes_youtube_auth.AsyncMongoDB.get_db") as mock_get_db:
        mock_db = AsyncMock()
        mock_db.youtube_channels.find_one = AsyncMock(return_value=None)
        mock_get_db.return_value = mock_db
        res = client.get("/api/auth/youtube/channel")
        assert res.status_code == 200
        data = res.json()
        assert data["is_connected"] is False
        assert data["channel"] is None
