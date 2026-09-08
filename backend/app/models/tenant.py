"""Data models for multi-tenant users, workspaces, API key vault, and usage ledger."""

from datetime import datetime, timezone
from enum import Enum
from typing import Any, Optional
from pydantic import Field, EmailStr
from backend.app.models.base import MongoBaseModel, PyObjectId


class TrialQuota(MongoBaseModel):
    """Hard-capped trial usage allowances per workspace."""
    max_videos: int = Field(default=3, description="Hard cap on total videos generated on trial")
    videos_generated: int = Field(default=0)
    max_ai_tokens: int = Field(default=60000, description="Approx. 3 full videos worth of LLM prompts")
    ai_tokens_used: int = Field(default=0)
    max_tts_seconds: int = Field(default=360, description="Approx. 3-4 minutes of neural speech synthesis")
    tts_seconds_used: int = Field(default=0)
    is_exhausted: bool = Field(default=False)


class WorkspaceSchedule(MongoBaseModel):
    """Publishing schedule preferences for a workspace."""
    slot_1_time: str = Field(default="07:00")
    slot_2_time: str = Field(default="18:00")
    timezone: str = Field(default="Asia/Kolkata")
    videos_per_day: int = Field(default=2)


class Workspace(MongoBaseModel):
    """Primary tenant isolation boundary."""
    name: str
    slug: str
    owner_id: str = Field(description="User ID of workspace creator")
    is_legacy_default: bool = Field(default=False, description="True for the platform owner's original channel")
    autopilot_enabled: bool = Field(default=False)
    niche: str = Field(default="Python Programming")
    content_template: str = Field(default="quiz_card")
    visual_style: str = Field(default="hand_drawn_sketch")
    voice_id: str = Field(default="en-US-ChristopherNeural")
    schedule: WorkspaceSchedule = Field(default_factory=WorkspaceSchedule)
    trial_quota: TrialQuota = Field(default_factory=TrialQuota)
    connected_channel_id: Optional[str] = None


class User(MongoBaseModel):
    """Platform user account."""
    email: str
    password_hash: str
    full_name: Optional[str] = None
    is_owner: bool = Field(default=False, description="Platform superadmin/owner")
    is_active: bool = Field(default=True)
    default_workspace_id: Optional[str] = None


class WorkspaceAPIKey(MongoBaseModel):
    """Encrypted API credentials stored in BYOK vault."""
    workspace_id: str
    provider: str  # "openrouter", "pexels", "pixabay", etc.
    encrypted_key: str
    key_mask: str  # e.g., "sk-or-••••3a19"
    is_valid: bool = True
    last_tested_at: Optional[datetime] = None


class UsageLedgerRecord(MongoBaseModel):
    """Strict cost and resource tracking ledger entry for billing audit."""
    workspace_id: str
    job_id: Optional[str] = None
    provider: str
    operation: str
    units: int = 0
    unit_type: str = "tokens"  # "tokens", "seconds", "request"
    estimated_cost_usd: float = 0.0
    used_platform_key: bool = False
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
