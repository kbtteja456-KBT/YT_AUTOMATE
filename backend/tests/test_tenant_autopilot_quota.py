"""Unit tests for multi-tenant autopilot and 3-video trial quota enforcement."""

import pytest
from bson import ObjectId
from backend.app.core.db import SyncMongoDB
from backend.app.core.ledger import (
    check_and_acquire_trial_quota_atomic_sync,
    can_workspace_generate_sync
)
from backend.app.core.cron_scheduler import is_slot_published_today, get_slot_status_today


def test_sync_trial_quota_enforcement():
    db = SyncMongoDB.get_db()
    test_ws_id = str(ObjectId())

    # Create a fresh tenant workspace with 3 free trial videos
    db.workspaces.insert_one({
        "_id": ObjectId(test_ws_id),
        "name": "Trial Tenant Channel",
        "owner_id": "test_user_99",
        "is_legacy_default": False,
        "niche": "Tech Trends",
        "autopilot_enabled": True,
        "trial_quota": {
            "max_videos": 3,
            "videos_generated": 0,
            "is_exhausted": False
        }
    })

    try:
        # Can generate check before any videos
        can_gen, _ = can_workspace_generate_sync(test_ws_id)
        assert can_gen is True

        # Video 1: Allowed (owner pays)
        ok1, reason1 = check_and_acquire_trial_quota_atomic_sync(test_ws_id)
        assert ok1 is True
        assert "1/3" in reason1

        # Video 2: Allowed (owner pays)
        ok2, reason2 = check_and_acquire_trial_quota_atomic_sync(test_ws_id)
        assert ok2 is True
        assert "2/3" in reason2

        # Video 3: Allowed (owner pays) - hits cap
        ok3, reason3 = check_and_acquire_trial_quota_atomic_sync(test_ws_id)
        assert ok3 is True
        assert "3/3" in reason3

        # Video 4: Blocked without BYOK key!
        ok4, reason4 = check_and_acquire_trial_quota_atomic_sync(test_ws_id)
        assert ok4 is False
        assert "Free trial limit reached" in reason4

        # Verify autopilot was auto-paused
        ws_doc = db.workspaces.find_one({"_id": ObjectId(test_ws_id)})
        assert ws_doc["autopilot_enabled"] is False
        assert ws_doc["trial_quota"]["is_exhausted"] is True

        # Now add tenant's own BYOK OpenRouter key
        db.workspace_api_keys.insert_one({
            "workspace_id": test_ws_id,
            "provider": "openrouter",
            "encrypted_key": "encrypted_dummy_key",
            "is_valid": True
        })

        # Video 5: Now allowed because BYOK is present!
        can_gen_byok, reason_byok = can_workspace_generate_sync(test_ws_id)
        assert can_gen_byok is True
        assert "BYOK" in reason_byok

        ok5, reason5 = check_and_acquire_trial_quota_atomic_sync(test_ws_id)
        assert ok5 is True
        assert "BYOK" in reason5

    finally:
        db.workspaces.delete_one({"_id": ObjectId(test_ws_id)})
        db.workspace_api_keys.delete_one({"workspace_id": test_ws_id})


def test_owner_workspace_unlimited_exemption():
    db = SyncMongoDB.get_db()
    owner_ws = db.workspaces.find_one({"is_legacy_default": True})
    assert owner_ws is not None
    owner_ws_id = str(owner_ws["_id"])

    # Owner is always allowed without limit
    can_gen, _ = can_workspace_generate_sync(owner_ws_id)
    assert can_gen is True

    ok, reason = check_and_acquire_trial_quota_atomic_sync(owner_ws_id)
    assert ok is True
    assert "Legacy owner" in reason


def test_slot_status_scoped_to_workspace():
    test_ws_id = str(ObjectId())
    # Should be False for a fresh non-existent workspace today
    published = is_slot_published_today(1, "2026-09-08", workspace_id=test_ws_id)
    assert published is False

    status = get_slot_status_today(1, "2026-09-08", workspace_id=test_ws_id)
    assert status == "PENDING"
