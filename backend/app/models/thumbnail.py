"""Data models for custom thumbnail generation."""

from typing import Optional
from pydantic import Field
from backend.app.models.base import MongoBaseModel


class ThumbnailSpec(MongoBaseModel):
    """Configuration for custom thumbnail generation."""
    source_frame_timestamp: float = Field(default=2.0, description="Timestamp in video from which to extract base frame")
    overlay_text: str = Field(description="Bold high-CTR hook words (max 3-5 words)")
    font_size: int = 72
    text_color: str = "#FFFF00"  # High visibility yellow or white
    stroke_color: str = "#000000"
    stroke_width: int = 6
    bg_gradient: bool = True
    saturation_boost: float = 1.15
    contrast_boost: float = 1.10
    output_width: int = 1080
    output_height: int = 1920


class ThumbnailCard(MongoBaseModel):
    """Result of rendered thumbnail card."""
    video_id: Optional[str] = None
    job_id: Optional[str] = None
    file_path: str
    file_hash: str
    spec: ThumbnailSpec
    uploaded_to_youtube: bool = False
