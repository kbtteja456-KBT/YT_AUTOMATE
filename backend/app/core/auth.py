"""Authentication and security utilities providing bcrypt password hashing,
JWT token generation, and FastAPI security dependencies.
"""

from datetime import datetime, timezone, timedelta
from typing import Any, Optional, Dict
import bcrypt
import jwt
from bson import ObjectId
from fastapi import Depends, HTTPException, Security, status, Header
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from backend.app.config import settings
from backend.app.core.db import AsyncMongoDB, SyncMongoDB
from backend.app.core.logging import logger

security_scheme = HTTPBearer(auto_error=False)

JWT_ALGORITHM = "HS256"
JWT_EXPIRATION_DAYS = 7


def get_jwt_secret() -> str:
    """Retrieve secret key for signing JWTs, derived safely from server encryption key."""
    sec = settings.encryption_key or settings.autopilot_cron_secret or "insecure_default_secret_key_change_me"
    return sec


def hash_password(plain_password: str) -> str:
    """Hash a plaintext password with bcrypt (work factor 12)."""
    salt = bcrypt.gensalt(rounds=12)
    hashed = bcrypt.hashpw(plain_password.encode("utf-8"), salt)
    return hashed.decode("utf-8")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a plaintext password against a bcrypt hash."""
    try:
        return bcrypt.checkpw(plain_password.encode("utf-8"), hashed_password.encode("utf-8"))
    except Exception:
        return False


def create_access_token(user_id: str, email: str, is_owner: bool = False, workspace_id: Optional[str] = None) -> str:
    """Create a signed JWT token valid for 7 days."""
    now = datetime.now(timezone.utc)
    payload = {
        "sub": user_id,
        "email": email,
        "is_owner": is_owner,
        "workspace_id": workspace_id,
        "iat": now,
        "exp": now + timedelta(days=JWT_EXPIRATION_DAYS),
    }
    return jwt.encode(payload, get_jwt_secret(), algorithm=JWT_ALGORITHM)


def decode_access_token(token: str) -> Dict[str, Any]:
    """Decode and validate a JWT access token."""
    try:
        payload = jwt.decode(token, get_jwt_secret(), algorithms=[JWT_ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Session token has expired. Please log in again.",
            headers={"WWW-Authenticate": "Bearer"}
        )
    except jwt.InvalidTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication token.",
            headers={"WWW-Authenticate": "Bearer"}
        )


async def get_current_user(
    auth_credentials: Optional[HTTPAuthorizationCredentials] = Security(security_scheme)
) -> Dict[str, Any]:
    """FastAPI dependency resolving the authenticated User document from the Authorization header."""
    if not auth_credentials or not auth_credentials.credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required.",
            headers={"WWW-Authenticate": "Bearer"}
        )

    payload = decode_access_token(auth_credentials.credentials)
    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token payload.")

    db = AsyncMongoDB.get_db()
    try:
        user = await db.users.find_one({"_id": ObjectId(user_id)})
    except Exception:
        user = await db.users.find_one({"_id": user_id})

    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User account not found.")

    if not user.get("is_active", True):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="User account is deactivated.")

    user["id"] = str(user["_id"])
    return user


async def get_optional_current_user(
    auth_credentials: Optional[HTTPAuthorizationCredentials] = Security(security_scheme)
) -> Optional[Dict[str, Any]]:
    """FastAPI dependency that returns the User document if authenticated, or None if anonymous."""
    if not auth_credentials or not auth_credentials.credentials:
        return None
    try:
        return await get_current_user(auth_credentials)
    except HTTPException:
        return None


async def get_current_workspace(
    user: Dict[str, Any] = Depends(get_current_user),
    x_workspace_id: Optional[str] = Header(None)
) -> Dict[str, Any]:
    """FastAPI dependency resolving the active Workspace document for the authenticated user."""
    db = AsyncMongoDB.get_db()
    target_ws_id = x_workspace_id or user.get("default_workspace_id")

    ws = None
    if target_ws_id:
        try:
            ws = await db.workspaces.find_one({"_id": ObjectId(target_ws_id)})
        except Exception:
            ws = await db.workspaces.find_one({"_id": target_ws_id})

    # If user is owner and no specific workspace requested, default to legacy owner workspace
    if not ws and user.get("is_owner"):
        ws = await db.workspaces.find_one({"is_legacy_default": True})

    # Fallback to any workspace owned by this user
    if not ws:
        user_id_str = str(user["_id"])
        ws = await db.workspaces.find_one({"owner_id": user_id_str})

    if not ws:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No workspace found for user.")

    ws["id"] = str(ws["_id"])
    return ws
