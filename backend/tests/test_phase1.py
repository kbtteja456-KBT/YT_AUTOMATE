"""Real unit tests for Phase 1: MongoDB schemas, security, and provider interfaces."""

import pytest
from datetime import datetime, timezone
from bson import ObjectId

from backend.app.core.errors import ZeroCostModeViolationError
from backend.app.core.security import (
    encrypt_token,
    decrypt_token,
    compute_content_hash,
)
from backend.app.models.base import MongoBaseModel
from backend.app.models.job import JobState, JobStageLog, PublishingJob
from backend.app.models.video import (
    Hook, Script, Scene, Storyboard, VisualType, QCReport, Video
)
from backend.app.models.thumbnail import ThumbnailSpec, ThumbnailCard
from backend.app.models.channel import OAuthTokenRecord, YouTubeChannel
from backend.app.models.settings import ChannelSettings, ScheduleConfig, VoiceConfig
from backend.app.models.style_profile import StyleProfile
from backend.app.models.provider import ProviderHealth, ProviderStatus, ProviderType
from backend.app.providers.base import (
    BaseProvider, AIProvider, TTSProvider, STTProvider,
    StockMediaProvider, SearchProvider, StorageProvider, YouTubeProvider, ThumbnailProvider
)


# --- 1. Security & Cryptography Tests ---

def test_aes256_token_encryption_and_decryption():
    """Verify that tokens are encrypted with AES-256 and decrypt back to the exact plaintext."""
    plaintext = "ya29.a0AfH6SMD_real_secret_oauth_refresh_token_xyz123"
    encrypted = encrypt_token(plaintext)
    assert encrypted != plaintext
    assert len(encrypted) > len(plaintext)
    
    decrypted = decrypt_token(encrypted)
    assert decrypted == plaintext


def test_content_hashing_determinism():
    """Verify deterministic SHA-256 content hashing for deduplication."""
    content1 = "5 AI Tools Students Need in 2026"
    content2 = "5 AI Tools Students Need in 2026"
    content3 = "Different Content"
    
    hash1 = compute_content_hash(content1)
    hash2 = compute_content_hash(content2)
    hash3 = compute_content_hash(content3)
    
    assert hash1 == hash2
    assert hash1 != hash3
    assert len(hash1) == 64


def test_oauth_record_token_helpers():
    """Verify OAuthTokenRecord encrypts at rest and decrypts on demand."""
    record = OAuthTokenRecord(
        channel_id="UC1234567890",
        encrypted_refresh_token="",
        encrypted_access_token="",
        scopes=["https://www.googleapis.com/auth/youtube.upload"]
    )
    record.set_tokens(
        refresh_token="my-secret-refresh-token",
        access_token="temporary-access-token"
    )
    
    assert record.encrypted_refresh_token != "my-secret-refresh-token"
    assert record.encrypted_access_token != "temporary-access-token"
    assert record.get_refresh_token() == "my-secret-refresh-token"
    assert record.get_access_token() == "temporary-access-token"


# --- 2. MongoDB Schema & Serialization Tests ---

def test_mongo_base_model_objectid_handling():
    """Verify MongoDB _id serialization and ObjectId conversion."""
    sample_oid = ObjectId()
    doc = MongoBaseModel(_id=str(sample_oid))
    mongo_dict = doc.to_mongo_dict()
    assert "_id" in mongo_dict
    assert isinstance(mongo_dict["_id"], ObjectId)
    assert str(mongo_dict["_id"]) == str(sample_oid)


def test_publishing_job_schema_and_state_machine():
    """Verify PublishingJob model validation and stage logs."""
    scheduled_time = datetime(2026, 9, 4, 7, 0, tzinfo=timezone.utc)
    job = PublishingJob(
        slot_index=1,
        scheduled_at=scheduled_time,
        idempotency_key="hash_2026_09_04_slot1",
        state=JobState.CREATED
    )
    assert job.state == JobState.CREATED
    assert job.slot_index == 1
    assert job.retry_count == 0
    
    # Transition to RESEARCHING
    stage_log = JobStageLog(
        stage=JobState.RESEARCHING,
        started_at=datetime.now(timezone.utc),
        status="COMPLETED",
        duration_ms=450
    )
    job.stage_logs.append(stage_log)
    job.state = JobState.RESEARCHING
    job.last_completed_stage = JobState.RESEARCHING
    
    dumped = job.model_dump()
    assert dumped["state"] == "RESEARCHING"
    assert len(dumped["stage_logs"]) == 1
    assert dumped["stage_logs"][0]["duration_ms"] == 450


def test_video_and_storyboard_schemas():
    """Verify Video, Scene, and Storyboard schema validation."""
    scene1 = Scene(
        scene_id=1,
        start=0.0,
        end=2.5,
        narration="Here is the opening hook that grabs immediate attention.",
        visual_type=VisualType.MOTION_GRAPHIC,
        visual_prompt="Bold typography with animated particles",
        caption="Stop scrolling right now"
    )
    storyboard = Storyboard(
        scenes=[scene1],
        total_duration=2.5,
        real_footage_ratio=0.28,
        screen_record_ratio=0.72
    )
    assert len(storyboard.scenes) == 1
    assert storyboard.scenes[0].transition == "cut"
    
    video = Video(
        title="5 AI Tools Every Student Must Know",
        description="Save hours on your assignments with these free AI tools.",
        tags=["ai", "students", "productivity"],
        width=1080,
        height=1920,
        fps=30,
        quality_score=94.5
    )
    assert video.width == 1080
    assert video.height == 1920
    assert video.quality_score == 94.5


def test_thumbnail_models():
    """Verify ThumbnailSpec and ThumbnailCard schemas."""
    spec = ThumbnailSpec(
        source_frame_timestamp=1.8,
        overlay_text="5 INSANE AI TOOLS",
        font_size=80,
        text_color="#FFFF00"
    )
    card = ThumbnailCard(
        file_path="/media/thumbnails/thumb_001.jpg",
        file_hash="abc123hash",
        spec=spec,
        uploaded_to_youtube=False
    )
    assert card.spec.overlay_text == "5 INSANE AI TOOLS"
    assert card.uploaded_to_youtube is False


def test_settings_zero_cost_mode_default():
    """Verify that Zero-Cost Mode is enabled by default in ChannelSettings."""
    settings_obj = ChannelSettings()
    assert settings_obj.zero_cost_mode is True
    assert settings_obj.paid_providers_enabled is False
    assert settings_obj.schedule.slot1_time == "07:00"
    assert settings_obj.schedule.slot2_time == "18:00"
    assert settings_obj.schedule.timezone == "Asia/Kolkata"
    assert settings_obj.schedule.daily_video_limit == 2


def test_style_profile_default_ratios():
    """Verify default dual-segment reference profile ratios."""
    profile = StyleProfile()
    assert profile.real_footage_ratio == 0.28
    assert profile.screen_recording_ratio == 0.72
    assert profile.total_duration_sec == 44.0
    assert profile.is_active is True


# --- 3. Zero-Cost Enforcement & Provider Interface Tests ---

class MockPaidProvider(BaseProvider):
    name = "mock_expensive_gpu_api"
    provider_type = ProviderType.AI
    is_zero_cost = False
    is_paid = True

    async def check_health(self) -> ProviderHealth:
        return ProviderHealth(
            provider_name=self.name,
            provider_type=self.provider_type,
            status=ProviderStatus.CONNECTED,
            is_zero_cost=False,
            is_paid=True
        )


class MockFreeProvider(BaseProvider):
    name = "mock_openrouter_free"
    provider_type = ProviderType.AI
    is_zero_cost = True
    is_paid = False

    async def check_health(self) -> ProviderHealth:
        return ProviderHealth(
            provider_name=self.name,
            provider_type=self.provider_type,
            status=ProviderStatus.CONNECTED,
            is_zero_cost=True,
            is_paid=False
        )


def test_zero_cost_mode_blocks_paid_provider():
    """Verify that Zero-Cost Mode strictly halts paid providers with expected message."""
    paid_provider = MockPaidProvider()
    
    # 1. Zero-cost mode ON -> Must raise ZeroCostModeViolationError
    with pytest.raises(ZeroCostModeViolationError) as exc_info:
        paid_provider.verify_zero_cost_compliance(zero_cost_mode=True)
    assert "Paid provider blocked by Zero-Cost Mode." in str(exc_info.value)
    
    # 2. Zero-cost mode OFF, but paid providers not explicitly enabled -> Must raise
    with pytest.raises(ZeroCostModeViolationError):
        paid_provider.verify_zero_cost_compliance(zero_cost_mode=False, paid_providers_enabled=False)


def test_free_provider_passes_zero_cost_compliance():
    """Verify that free providers pass zero-cost verification without exceptions."""
    free_provider = MockFreeProvider()
    # Should not raise any error
    free_provider.verify_zero_cost_compliance(zero_cost_mode=True)


def test_abstract_provider_instantiation_prevention():
    """Verify that abstract provider interfaces cannot be instantiated directly."""
    with pytest.raises(TypeError):
        AIProvider()  # type: ignore

    with pytest.raises(TypeError):
        TTSProvider()  # type: ignore

    with pytest.raises(TypeError):
        STTProvider()  # type: ignore

    with pytest.raises(TypeError):
        YouTubeProvider()  # type: ignore
