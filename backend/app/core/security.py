"""Security utilities: AES-256 token encryption and SHA-256 content hashing."""

import os
import hashlib
from typing import Optional
from cryptography.fernet import Fernet

from backend.app.config import settings

MISSING_ENCRYPTION_KEY_ERROR = (
    "ENCRYPTION_KEY is not set. Generate one with:\n"
    "python -c \"from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())\"\n"
    "and set it in your .env file. This value must stay constant — changing it "
    "will invalidate all previously stored OAuth tokens."
)


def get_encryption_key() -> bytes:
    """Retrieve the Fernet key from environment or settings. Fails loudly if missing."""
    key = (settings.encryption_key or os.getenv("ENCRYPTION_KEY", "")).strip()
    if not key:
        raise RuntimeError(MISSING_ENCRYPTION_KEY_ERROR)
    if isinstance(key, str):
        key = key.encode("utf-8")
    return key


def encrypt_token(plain_token: str, key: Optional[bytes] = None) -> str:
    """Encrypt a sensitive token (e.g. OAuth refresh token) using AES-256 Fernet."""
    if not plain_token:
        return ""
    fernet = Fernet(key or get_encryption_key())
    encrypted_bytes = fernet.encrypt(plain_token.encode("utf-8"))
    return encrypted_bytes.decode("utf-8")


def decrypt_token(encrypted_token: str, key: Optional[bytes] = None) -> str:
    """Decrypt an encrypted token back to plaintext."""
    if not encrypted_token:
        return ""
    fernet = Fernet(key or get_encryption_key())
    decrypted_bytes = fernet.decrypt(encrypted_token.encode("utf-8"))
    return decrypted_bytes.decode("utf-8")


def compute_content_hash(data: str | bytes) -> str:
    """Compute SHA-256 hex digest for data deduplication and idempotency."""
    if isinstance(data, str):
        data = data.encode("utf-8")
    return hashlib.sha256(data).hexdigest()


def compute_file_hash(file_path: str) -> str:
    """Compute SHA-256 hex digest of a file on disk."""
    hasher = hashlib.sha256()
    with open(file_path, "rb") as f:
        while chunk := f.read(65536):
            hasher.update(chunk)
    return hasher.hexdigest()
