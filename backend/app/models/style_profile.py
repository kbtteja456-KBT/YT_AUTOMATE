"""Data models for reference video style profiles and pacing extraction."""

from typing import Optional
from pydantic import Field
from backend.app.models.base import MongoBaseModel


class StyleProfile(MongoBaseModel):
    """Pacing and structural blueprint extracted from reference video or default template."""
    name: str = "hybrid_pacing_template"
    reference_video_path: Optional[str] = None
    
    total_duration_sec: float = Field(default=44.0, description="Reference baseline video duration")
    segment_count: int = Field(default=16, description="Number of detected scene cuts")
    
    # Dual-segment rhythm
    real_footage_ratio: float = Field(
        default=0.28,
        description="Ratio of handheld/real footage demo segment (typically ~25-30% mark)"
    )
    screen_recording_ratio: float = Field(
        default=0.72,
        description="Ratio of software walkthrough/screen recording segment"
    )
    
    cut_frequency_sec: float = Field(
        default=2.3,
        description="Average interval in seconds between visual scene changes"
    )
    hook_duration_sec: float = Field(
        default=2.8,
        description="Duration of opening scene before first pattern interrupt"
    )
    
    # Caption styling parameters
    caption_words_per_segment: int = 3
    caption_highlight_color: str = "#00FFA3"  # Vibrant mint green
    caption_base_color: str = "#FFFFFF"
    caption_font_family: str = "Impact"
    caption_safe_margin_bottom_pct: float = 0.22  # Avoid Shorts bottom UI
    caption_safe_margin_top_pct: float = 0.12     # Avoid Shorts header
    
    is_active: bool = True
