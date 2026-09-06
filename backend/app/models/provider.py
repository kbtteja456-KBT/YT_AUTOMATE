"""Provider health and usage tracking models."""

from datetime import datetime
from enum import Enum
from typing import Any, Optional
from pydantic import Field
from backend.app.models.base import MongoBaseModel


class ProviderType(str, Enum):
    AI = "AI"
    TTS = "TTS"
    STT = "STT"
    STOCK_MEDIA = "STOCK_MEDIA"
    SEARCH = "SEARCH"
    STORAGE = "STORAGE"
    YOUTUBE = "YOUTUBE"
    THUMBNAIL = "THUMBNAIL"
    MUSIC = "MUSIC"


class ProviderStatus(str, Enum):
    CONNECTED = "CONNECTED"
    DEGRADED = "DEGRADED"
    OFFLINE = "OFFLINE"
    BLOCKED_ZERO_COST = "BLOCKED_ZERO_COST"
    NOT_CONFIGURED = "NOT_CONFIGURED"


class ProviderHealth(MongoBaseModel):
    """Health check snapshot for each provider subsystem."""
    provider_name: str
    provider_type: ProviderType
    status: ProviderStatus
    is_zero_cost: bool = True
    is_paid: bool = False
    latency_ms: Optional[float] = None
    last_checked: datetime = Field(default_factory=datetime.utcnow)
    error_message: Optional[str] = None
    details: dict[str, Any] = Field(default_factory=dict)


class ProviderUsageRecord(MongoBaseModel):
    """Accounting entry for provider invocations to verify zero-cost compliance."""
    provider_name: str
    provider_type: ProviderType
    operation: str
    is_zero_cost: bool = True
    cost_incurred: float = Field(default=0.0, description="Cost in USD; must remain 0.0 in Zero-Cost Mode")
    tokens_prompt: Optional[int] = None
    tokens_completion: Optional[int] = None
    duration_ms: Optional[int] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)
