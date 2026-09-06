"""Data models for videos, scripts, research, storyboards, and scenes."""

from datetime import datetime
from enum import Enum
from typing import Any, Optional
from pydantic import Field
from backend.app.models.base import MongoBaseModel, PyObjectId


class VisualType(str, Enum):
    USER_MEDIA = "user_media"
    SCREEN_RECORDING = "screen_recording"
    STOCK_FOOTAGE = "stock_footage"
    GENERATED_IMAGE = "generated_image"
    MOTION_GRAPHIC = "motion_graphic"
    ANIMATED_IMAGE = "animated_image"
    QUIZ_CARD_QUESTION = "quiz_card_question"
    QUIZ_CARD_REVEAL = "quiz_card_reveal"


class ResearchItem(MongoBaseModel):
    """Factual claim separated strictly into fact, source, and interpretation."""
    fact: str
    source: str
    interpretation: str
    verified: bool = True
    confidence: float = 1.0


class ResearchReport(MongoBaseModel):
    """Comprehensive research output for a selected video topic."""
    topic: str
    niche: str
    items: list[ResearchItem] = Field(default_factory=list)
    key_takeaway: str = ""
    content_format: str = "general"
    question_code: Optional[str] = None
    options: list[str] = Field(default_factory=list)
    correct_option: Optional[str] = None
    explanation: Optional[str] = None
    concept_tag: Optional[str] = None
    verified_output: Optional[str] = None


class Hook(MongoBaseModel):
    """Scored hook candidate designed for the critical 0-3 second retention window."""
    text: str
    curiosity_score: float = 0.0
    clarity_score: float = 0.0
    specificity_score: float = 0.0
    emotional_impact_score: float = 0.0
    retention_score: float = 0.0
    speed_score: float = 0.0
    total_score: float = 0.0
    selected: bool = False


class Script(MongoBaseModel):
    """Strictly structured 30-60 second narration."""
    topic: str
    hook: str
    problem: str
    value: str
    payoff: str
    cta: str
    full_narration: str
    target_duration_sec: float = 45.0
    word_count: int = 0
    content_format: str = "general"
    question_code: Optional[str] = None
    options: list[str] = Field(default_factory=list)
    correct_option: Optional[str] = None
    explanation: Optional[str] = None
    concept_tag: Optional[str] = None
    verified_output: Optional[str] = None


class CaptionWord(MongoBaseModel):
    """Word-level timestamp produced by Whisper STT."""
    word: str
    start: float
    end: float
    confidence: float = 1.0


class CaptionSegment(MongoBaseModel):
    """Sentence or phrase level caption container."""
    text: str
    start: float
    end: float
    words: list[CaptionWord] = Field(default_factory=list)


class Scene(MongoBaseModel):
    """Single visual scene mapped to a time range in the storyboard."""
    scene_id: int
    start: float
    end: float
    narration: str
    visual_type: VisualType = VisualType.MOTION_GRAPHIC
    visual_prompt: str
    caption: str = ""
    transition: str = "cut"
    sfx: Optional[str] = None
    asset_url: Optional[str] = None
    asset_local_path: Optional[str] = None
    license_info: Optional[str] = None
    attribution: Optional[str] = None


class Storyboard(MongoBaseModel):
    """Collection of ordered scenes creating the dynamic rhythm of the Short."""
    script_id: Optional[str] = None
    scenes: list[Scene] = Field(default_factory=list)
    total_duration: float = 0.0
    real_footage_ratio: float = 0.3
    screen_record_ratio: float = 0.7
    cut_frequency: float = 2.5


class QCReport(MongoBaseModel):
    """Detailed quality gate audit report."""
    score: float = 0.0
    passed: bool = False
    resolution_valid: bool = False
    duration_valid: bool = False
    audio_present: bool = False
    captions_synced: bool = False
    no_black_frames: bool = True
    no_frozen_frames: bool = True
    no_clipping: bool = True
    no_watermarks: bool = True
    bg_music_present: bool = True
    bg_music_normalized: bool = True
    quiz_cards_distinct: bool = True
    details: dict[str, Any] = Field(default_factory=dict)
    remediation_notes: list[str] = Field(default_factory=list)


class Video(MongoBaseModel):
    """Primary completed video asset record."""
    job_id: Optional[str] = None
    title: str
    description: str
    tags: list[str] = Field(default_factory=list)
    hashtags: list[str] = Field(default_factory=list)
    
    file_path: Optional[str] = None
    file_hash: Optional[str] = None
    thumbnail_path: Optional[str] = None
    
    duration_seconds: float = 0.0
    width: int = 1080
    height: int = 1920
    fps: int = 30
    
    quality_score: float = 0.0
    qc_report: Optional[QCReport] = None
    
    youtube_video_id: Optional[str] = None
    youtube_url: Optional[str] = None
    youtube_published_at: Optional[datetime] = None
    privacy_status: str = "public"
