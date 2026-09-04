"""Configuration and settings models."""

from typing import Optional
from pydantic import Field
from backend.app.models.base import MongoBaseModel


class ScheduleConfig(MongoBaseModel):
    """Daily publishing schedule configuration."""
    slot1_time: str = Field(default="07:00", description="Morning publish time HH:MM (24h)")
    slot2_time: str = Field(default="18:00", description="Evening publish time HH:MM (24h)")
    timezone: str = Field(default="Asia/Kolkata", description="IANA timezone name")
    daily_video_limit: int = Field(default=2, ge=1, le=5)
    grace_period_minutes: int = Field(default=30, description="Minutes after publish time before slot is marked MISSED")
    buffer_max_size: int = Field(default=2, description="Maximum pre-generated videos in buffer")


class VoiceConfig(MongoBaseModel):
    """Text-to-speech voice parameters."""
    provider: str = Field(default="edge-tts", description="edge-tts, pyttsx3, or piper")
    voice_id: str = Field(default="en-US-ChristopherNeural", description="TTS Voice name/id")
    rate: str = Field(default="+0%", description="Speed adjustment e.g. +5%")
    pitch: str = Field(default="+0Hz", description="Pitch adjustment")
    volume: str = Field(default="+0%", description="Volume adjustment")


class ChannelSettings(MongoBaseModel):
    """Global system and channel operational settings."""
    channel_id: Optional[str] = None
    autopilot_enabled: bool = Field(default=True, description="Master switch for automated publishing")
    zero_cost_mode: bool = Field(default=True, description="Hard gate: blocks all paid API calls when True")
    paid_providers_enabled: bool = Field(default=False, description="Must be explicitly True for paid models")
    allowed_paid_providers: list[str] = Field(default_factory=list)
    
    niche: str = Field(default="AI & Productivity Tools", description="Content niche")
    target_audience: str = Field(default="Students and Tech Enthusiasts", description="Target viewer persona")
    language: str = Field(default="en", description="Target audio/caption language")
    
    schedule: ScheduleConfig = Field(default_factory=ScheduleConfig)
    voice: VoiceConfig = Field(default_factory=VoiceConfig)
    
    # Pre-generation windows
    morning_pregen_start: str = "01:00"
    morning_pregen_end: str = "06:30"
    evening_pregen_start: str = "12:00"
    evening_pregen_end: str = "17:30"
