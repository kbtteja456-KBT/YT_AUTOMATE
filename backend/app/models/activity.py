"""Real-time activity feed event models for dashboard streaming."""

from datetime import datetime, timezone
from typing import Any, Optional
from pydantic import Field
from backend.app.models.base import MongoBaseModel


class ActivityEvent(MongoBaseModel):
    """Immutable, timestamped event emitted during agent and pipeline execution."""
    event_type: str = Field(description="EVENT_TYPE e.g. STAGE_UPDATE, QC_AUDIT, PUBLISH_VERIFIED")
    level: str = Field(default="INFO", description="INFO, SUCCESS, WARNING, ERROR")
    agent_name: Optional[str] = None
    job_id: Optional[str] = None
    stage: Optional[str] = None
    message: str = Field(description="Clear human-readable event description")
    details: dict[str, Any] = Field(default_factory=dict)
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
