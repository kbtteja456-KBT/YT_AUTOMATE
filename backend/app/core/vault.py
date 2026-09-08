"""BYOK (Bring Your Own Key) Vault providing AES-256 encryption at rest,
key masking for safe frontend display, and provider health verification.
"""

from datetime import datetime, timezone
from typing import Any, Optional, Tuple
import httpx

from backend.app.config import settings
from backend.app.core.security import encrypt_token, decrypt_token
from backend.app.core.logging import logger


def encrypt_api_key(raw_key: str) -> str:
    """Encrypt a tenant's plaintext API key using the server's master Fernet key."""
    return encrypt_token(raw_key.strip())


def decrypt_api_key(encrypted_key: str) -> str:
    """Decrypt an encrypted API key back to plaintext for runtime pipeline execution."""
    return decrypt_token(encrypted_key)


def mask_api_key(raw_key: str) -> str:
    """Mask an API key for safe UI display (e.g., 'sk-or-••••492a').
    
    Guarantees the raw secret is never transmitted back to the browser once saved.
    """
    clean = raw_key.strip()
    if not clean:
        return ""
    if len(clean) <= 8:
        return "••••" + clean[-2:]
    prefix = clean[:6] if clean.startswith("sk-") else clean[:3]
    suffix = clean[-4:]
    return f"{prefix}••••{suffix}"


async def verify_provider_api_key(provider: str, raw_key: str) -> Tuple[bool, str]:
    """Live verification check testing the API key against the upstream provider's auth endpoint."""
    provider_clean = provider.strip().lower()
    raw_key = raw_key.strip()

    if not raw_key:
        return False, "API key cannot be empty."

    try:
        if provider_clean in ["openrouter", "ai"]:
            # Verify OpenRouter key
            headers = {
                "Authorization": f"Bearer {raw_key}",
                "HTTP-Referer": "https://github.com/kbtteja456-KBT/YT_AUTOMATE",
                "X-Title": "YT_AUTOMATE Autopilot"
            }
            async with httpx.AsyncClient(timeout=8.0) as client:
                res = await client.get("https://openrouter.ai/api/v1/auth/key", headers=headers)
                if res.status_code == 200:
                    data = res.json().get("data", {})
                    label = data.get("label") or "Active Key"
                    return True, f"Valid OpenRouter key ({label})"
                else:
                    return False, f"OpenRouter returned status {res.status_code}: {res.text[:100]}"

        elif provider_clean in ["pexels", "stock_media"]:
            # Verify Pexels key
            headers = {"Authorization": raw_key}
            async with httpx.AsyncClient(timeout=8.0) as client:
                res = await client.get("https://api.pexels.com/v1/curated?per_page=1", headers=headers)
                if res.status_code == 200:
                    return True, "Valid Pexels key"
                else:
                    return False, f"Pexels returned status {res.status_code}"

        elif provider_clean in ["pixabay"]:
            # Verify Pixabay key
            async with httpx.AsyncClient(timeout=8.0) as client:
                res = await client.get(f"https://pixabay.com/api/?key={raw_key}&q=nature&per_page=3")
                if res.status_code == 200:
                    return True, "Valid Pixabay key"
                else:
                    return False, f"Pixabay returned status {res.status_code}"

        else:
            # Generic format check for unknown providers
            if len(raw_key) >= 12:
                return True, "Key saved"
            return False, "Key appears too short to be valid."

    except Exception as e:
        logger.warning(f"Key verification error for {provider}: {e}")
        return False, f"Connection error: {str(e)}"
