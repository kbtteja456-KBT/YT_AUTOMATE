"""API Key Vault endpoints allowing tenants to store, test, and view masked credentials."""

from datetime import datetime, timezone
from typing import Any, Optional, List
from fastapi import APIRouter, HTTPException, Depends, status
from pydantic import BaseModel, Field

from backend.app.core.db import AsyncMongoDB
from backend.app.core.auth import get_current_user, get_current_workspace
from backend.app.core.vault import encrypt_api_key, mask_api_key, verify_provider_api_key

router = APIRouter(prefix="/vault", tags=["vault"])

PROVIDER_ACQUISITION_GUIDES = {
    "openrouter": {
        "name": "OpenRouter AI (LLM)",
        "cost": "Free models available (e.g. Llama 3.3 70B:free, Nemotron 3.5:free)",
        "step_by_step": [
            "Go to https://openrouter.ai and sign up or log in.",
            "Click on your profile avatar in top right -> select 'Keys'.",
            "Click 'Create Key', choose a name (e.g. 'YT Shorts Autopilot'), and copy your key (sk-or-v1-...).",
            "Paste the key here. Free models require $0 account balance!"
        ],
        "signup_url": "https://openrouter.ai/keys"
    },
    "pexels": {
        "name": "Pexels Video API (Stock B-Roll)",
        "cost": "100% Free (200 requests/hour, 20,000/month)",
        "step_by_step": [
            "Visit https://www.pexels.com/api/ and click 'Get Started'.",
            "Log in or create a free Pexels account.",
            "Describe your app briefly (e.g. 'Automated video compilation') to get your instant API key.",
            "Copy the API key from your Pexels dashboard and paste it here."
        ],
        "signup_url": "https://www.pexels.com/api/"
    },
    "pixabay": {
        "name": "Pixabay API (Stock Media Fallback)",
        "cost": "100% Free (5,000 requests/hour)",
        "step_by_step": [
            "Visit https://pixabay.com/api/docs/ and log in.",
            "Scroll to the 'Search Images' section to see your personal API Key highlighted in green.",
            "Copy and paste that key here."
        ],
        "signup_url": "https://pixabay.com/api/docs/"
    }
}


class SaveKeyRequest(BaseModel):
    provider: str = Field(description="Provider name: 'openrouter', 'pexels', or 'pixabay'")
    api_key: str = Field(min_length=10, description="Raw secret API key")


@router.get("/keys")
async def list_workspace_keys(
    workspace: dict[str, Any] = Depends(get_current_workspace)
) -> dict[str, Any]:
    """Retrieve all masked keys configured for the active workspace, along with instructions."""
    db = AsyncMongoDB.get_db()
    ws_id = str(workspace["_id"])
    cursor = db.workspace_api_keys.find({"workspace_id": ws_id})
    keys = await cursor.to_list(length=20)

    key_dict = {}
    for k in keys:
        key_dict[k["provider"]] = {
            "key_mask": k.get("key_mask"),
            "is_valid": k.get("is_valid", True),
            "last_tested_at": k.get("last_tested_at"),
            "provider": k["provider"],
        }

    return {
        "workspace_id": ws_id,
        "configured_keys": key_dict,
        "acquisition_guides": PROVIDER_ACQUISITION_GUIDES
    }


@router.post("/keys")
async def save_or_update_key(
    req: SaveKeyRequest,
    workspace: dict[str, Any] = Depends(get_current_workspace)
) -> dict[str, Any]:
    """Verify, encrypt with master key, and save a provider API key in the workspace vault."""
    provider_name = req.provider.strip().lower()
    raw_key = req.api_key.strip()

    # 1. Live test with upstream provider
    is_valid, message = await verify_provider_api_key(provider_name, raw_key)
    if not is_valid:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Provider verification failed: {message}"
        )

    # 2. Encrypt at rest and mask for display
    encrypted = encrypt_api_key(raw_key)
    masked = mask_api_key(raw_key)

    # 3. Store in MongoDB
    db = AsyncMongoDB.get_db()
    ws_id = str(workspace["_id"])
    now = datetime.now(timezone.utc)

    doc = {
        "workspace_id": ws_id,
        "provider": provider_name,
        "encrypted_key": encrypted,
        "key_mask": masked,
        "is_valid": True,
        "last_tested_at": now,
        "updated_at": now,
    }

    await db.workspace_api_keys.update_one(
        {"workspace_id": ws_id, "provider": provider_name},
        {"$set": doc, "$setOnInsert": {"created_at": now}},
        upsert=True
    )

    return {
        "status": "SAVED",
        "provider": provider_name,
        "key_mask": masked,
        "message": f"Successfully connected and verified {provider_name.title()} key."
    }


@router.delete("/keys/{provider}")
async def delete_key(
    provider: str,
    workspace: dict[str, Any] = Depends(get_current_workspace)
) -> dict[str, Any]:
    """Remove a key from the workspace vault."""
    db = AsyncMongoDB.get_db()
    ws_id = str(workspace["_id"])
    provider_name = provider.strip().lower()

    res = await db.workspace_api_keys.delete_one({"workspace_id": ws_id, "provider": provider_name})
    if res.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Key not found.")

    return {"status": "DELETED", "provider": provider_name}
