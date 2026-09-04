"""Job state machine models and publishing job definitions."""

from datetime import datetime
from enum import Enum
from typing import Any, Optional
from pydantic import Field
from backend.app.models.base import MongoBaseModel, PyObjectId


class JobState(str, Enum):
    """Explicit pipeline state machine states."""
    CREATED = "CREATED"
    QUEUED = "QUEUED"
    RESEARCHING = "RESEARCHING"
    SCRIPTING = "SCRIPTING"
    STORYBOARDING = "STORYBOARDING"
    GENERATING_MEDIA = "GENERATING_MEDIA"
    GENERATING_VOICE = "GENERATING_VOICE"
    GENERATING_CAPTIONS = "GENERATING_CAPTIONS"
    RENDERING = "RENDERING"
    QUALITY_CHECK = "QUALITY_CHECK"
    GENERATING_THUMBNAIL = "GENERATING_THUMBNAIL"
    READY = "READY"
    PUBLISHING = "PUBLISHING"
    PUBLISHED = "PUBLISHED"
    
    # Failure / Terminal / Interrupted states
    FAILED = "FAILED"
    RETRYING = "RETRYING"
    CANCELLED = "CANCELLED"
    MISSED = "MISSED"
    QC_FAILED = "QC_FAILED"
    WAITING_FOR_FREE_PROVIDER = "WAITING_FOR_FREE_PROVIDER"


class JobStageLog(MongoBaseModel):
    """Execution metrics for an individual pipeline stage."""
    stage: JobState
    started_at: datetime
    completed_at: Optional[datetime] = None
    duration_ms: Optional[int] = None
    status: str = "COMPLETED"  # "COMPLETED", "FAILED", "RETRYING"
    details: Optional[dict[str, Any]] = None
    error: Optional[str] = None


class PublishingJob(MongoBaseModel):
    """Primary unit of work tracked in MongoDB."""
    channel_id: Optional[str] = None
    slot_index: int = Field(default=1, description="1 for Morning (07:00), 2 for Evening (18:00)")
    scheduled_at: datetime = Field(description="Exact scheduled publishing datetime in UTC")
    pregeneration_window_start: Optional[datetime] = None
    published_at: Optional[datetime] = None
    
    state: JobState = Field(default=JobState.CREATED)
    previous_state: Optional[JobState] = None
    idempotency_key: str = Field(description="Unique hash preventing duplicate job execution")
    
    video_id: Optional[str] = None
    topic: Optional[str] = None
    niche: Optional[str] = None
    
    retry_count: int = 0
    max_retries: int = 3
    qc_score: Optional[float] = None
    qc_attempt: int = 0
    
    stage_logs: list[JobStageLog] = Field(default_factory=list)
    last_completed_stage: Optional[JobState] = None
    
    error_message: Optional[str] = None
    is_buffered: bool = Field(default=False, description="True if rendered early and waiting for publish time")
