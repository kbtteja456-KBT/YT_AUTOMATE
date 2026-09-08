"""Unit and integration tests for multi-tenant SaaS architecture:
- Owner migration and backward compatibility
- User registration and workspace isolation
- BYOK Vault encryption and masking
- Atomic trial quota enforcement and race condition protection
- Kill-switch verification
"""

import asyncio
import os
import pytest
from bson import ObjectId

from backend.app.core.db import SyncMongoDB, AsyncMongoDB
from backend.app.core.auth import hash_password, verify_password, create_access_token, decode_access_token
from backend.app.core.vault import encrypt_api_key, decrypt_api_key, mask_api_key
from backend.app.core.ledger import check_and_acquire_trial_quota_atomic, is_platform_trial_disabled
from backend.app.core.migration import OWNER_EMAIL, get_or_create_legacy_workspace


def test_password_hashing():
    pwd = "@bhanuteja89"
    hashed = hash_password(pwd)
    assert hashed != pwd
    assert verify_password(pwd, hashed) is True
    assert verify_password("wrongpassword", hashed) is False


def test_jwt_token_flow():
    token = create_access_token("user123", "test@example.com", is_owner=False, workspace_id="ws123")
    payload = decode_access_token(token)
    assert payload["sub"] == "user123"
    assert payload["email"] == "test@example.com"
    assert payload["workspace_id"] == "ws123"
    assert payload["is_owner"] is False


def test_byok_vault_encryption():
    raw_key = "sk-or-v1-9876543210abcdef12345678"
    encrypted = encrypt_api_key(raw_key)
    assert encrypted != raw_key
    decrypted = decrypt_api_key(encrypted)
    assert decrypted == raw_key

    masked = mask_api_key(raw_key)
    assert masked == "sk-or-••••5678"
    assert "9876543210abcdef" not in masked


def test_owner_migration_logic():
    db = SyncMongoDB.get_db()
    legacy_ws = get_or_create_legacy_workspace(db, owner_id="test_owner_id")
    assert legacy_ws is not None
    assert legacy_ws["is_legacy_default"] is True
    assert legacy_ws["trial_quota"]["max_videos"] >= 999999


def test_trial_quota_atomic_enforcement():
    async def _run():
        await AsyncMongoDB.connect()
        db = AsyncMongoDB.get_db()

        # Create a test tenant workspace with cap of 3 videos
        test_ws_doc = {
            "name": "Test Tenant Workspace",
            "slug": "test-tenant-slug",
            "owner_id": "test_user_tenant",
            "is_legacy_default": False,
            "autopilot_enabled": True,
            "trial_quota": {
                "max_videos": 3,
                "videos_generated": 0,
                "is_exhausted": False
            }
        }
        res = await db.workspaces.insert_one(test_ws_doc)
        test_ws_id = str(res.inserted_id)

        # 1st request -> Allowed
        ok1, reason1 = await check_and_acquire_trial_quota_atomic(test_ws_id, is_video_generation=True)
        assert ok1 is True

        # 2nd request -> Allowed
        ok2, reason2 = await check_and_acquire_trial_quota_atomic(test_ws_id, is_video_generation=True)
        assert ok2 is True

        # 3rd request -> Allowed
        ok3, reason3 = await check_and_acquire_trial_quota_atomic(test_ws_id, is_video_generation=True)
        assert ok3 is True

        # 4th request -> MUST BE BLOCKED
        ok4, reason4 = await check_and_acquire_trial_quota_atomic(test_ws_id, is_video_generation=True)
        assert ok4 is False
        assert "Free trial limit reached" in reason4

        # Verify workspace was auto-paused
        ws_after = await db.workspaces.find_one({"_id": ObjectId(test_ws_id)})
        assert ws_after["autopilot_enabled"] is False
        assert ws_after["trial_quota"]["is_exhausted"] is True

        # Cleanup test workspace
        await db.workspaces.delete_one({"_id": ObjectId(test_ws_id)})
        await AsyncMongoDB.disconnect()

    asyncio.run(_run())


def test_kill_switch():
    async def _run():
        os.environ["DISABLE_PLATFORM_KEY_TRIALS"] = "true"
        assert is_platform_trial_disabled() is True

        allowed, reason = await check_and_acquire_trial_quota_atomic("any_id")
        assert allowed is False
        assert "currently disabled" in reason

        # Reset
        os.environ["DISABLE_PLATFORM_KEY_TRIALS"] = "false"
        assert is_platform_trial_disabled() is False

    asyncio.run(_run())


def test_auth_endpoints_api():
    from fastapi.testclient import TestClient
    from backend.app.main import app

    with TestClient(app) as client:
        # Test registration with a unique dummy email
        import time
        test_email = f"user_{int(time.time())}@example.com"
        reg_resp = client.post("/api/auth/register", json={
            "email": test_email,
            "password": "strongPassword123!",
            "full_name": "Test Runner"
        })
        assert reg_resp.status_code == 200, reg_resp.text
        data = reg_resp.json()
        assert "access_token" in data
        assert data["user"]["email"] == test_email
        assert data["workspace"]["is_legacy_default"] is False
        assert data["workspace"]["trial_quota"]["max_videos"] == 3

        # Test login with same email
        login_resp = client.post("/api/auth/login", json={
            "email": test_email,
            "password": "strongPassword123!"
        })
        assert login_resp.status_code == 200
        token = login_resp.json()["access_token"]

        # Test /api/auth/me with Bearer token
        me_resp = client.get("/api/auth/me", headers={"Authorization": f"Bearer {token}"})
        assert me_resp.status_code == 200
        me_data = me_resp.json()
        assert me_data["user"]["email"] == test_email
        assert me_data["workspace"]["trial_quota"]["max_videos"] == 3

        # Test tenant YouTube channel isolation: tenant must NOT see owner's channel
        chan_resp = client.get("/api/auth/youtube/channel", headers={"Authorization": f"Bearer {token}"})
        assert chan_resp.status_code == 200
        chan_data = chan_resp.json()
        assert chan_data["is_connected"] is False
        assert chan_data["channel"] is None

        # Test tenant videos isolation: tenant must NOT see owner's videos
        vids_resp = client.get("/api/videos", headers={"Authorization": f"Bearer {token}"})
        assert vids_resp.status_code == 200
        assert vids_resp.json() == []

