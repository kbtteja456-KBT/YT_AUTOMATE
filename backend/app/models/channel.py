"""Data models for YouTube channel and OAuth token records."""

from datetime import datetime
from typing import Optional
from pydantic import Field
from backend.app.models.base import MongoBaseModel
from backend.app.core.security import encrypt_token, decrypt_token


class OAuthTokenRecord(MongoBaseModel):
    """Encrypted OAuth2 credentials stored securely at rest."""
    channel_id: str
    encrypted_refresh_token: str
    encrypted_access_token: str
    token_expiry: Optional[datetime] = None
    scopes: list[str] = Field(default_factory=list)
    token_type: str = "Bearer"

    def set_tokens(self, refresh_token: str, access_token: str) -> None:
        """Encrypt and store plaintext tokens."""
        self.encrypted_refresh_token = encrypt_token(refresh_token)
        self.encrypted_access_token = encrypt_token(access_token)

    def get_refresh_token(self) -> str:
        """Decrypt and return plaintext refresh token."""
        return decrypt_token(self.encrypted_refresh_token)

    def get_access_token(self) -> str:
        """Decrypt and return plaintext access token."""
        return decrypt_token(self.encrypted_access_token)


class YouTubeChannel(MongoBaseModel):
    """Connected YouTube Channel details."""
    channel_id: str
    title: str
    description: Optional[str] = None
    custom_url: Optional[str] = None
    subscriber_count: Optional[int] = None
    view_count: Optional[int] = None
    video_count: Optional[int] = None
    thumbnail_url: Optional[str] = None
    is_active: bool = True
    connected_at: datetime = Field(default_factory=datetime.utcnow)
    last_synced_at: Optional[datetime] = None
