"""Real unit tests for Phases 10 & 11: StoryboardAgent, PatternInterruptEngine, and MediaAgent."""

import pytest
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock
from PIL import Image

from backend.app.models.style_profile import StyleProfile
from backend.app.models.video import Script, VisualType
from backend.app.pipeline.pattern_interrupt import PatternInterruptEngine
from backend.app.agents.storyboard import StoryboardAgent
from backend.app.agents.media import MediaAgent
from backend.app.providers.media.stock_media import StockMediaEngine
from backend.app.providers.storage.local_storage import LocalStorageProvider


def test_pattern_interrupt_engine_rhythm():
    """Verify PatternInterruptEngine plans cut intervals and alternating scene types."""
    profile = StyleProfile(
        hook_duration_sec=2.5,
        cut_frequency_sec=2.2,
        real_footage_ratio=0.30,
        screen_recording_ratio=0.70
    )
    engine = PatternInterruptEngine(profile)
    slots = engine.plan_scene_rhythm(total_duration=44.0)

    # Must have multiple scenes (never 1 static image for the Short)
    assert len(slots) >= 15
    assert slots[0]["start"] == 0.0
    assert slots[0]["end"] == 2.5
    assert slots[0]["is_hook"] is True
    assert slots[-1]["end"] == 44.0


@pytest.mark.anyio
async def test_storyboard_agent_scene_generation():
    """Verify StoryboardAgent creates sequential scenes with prompts and captions."""
    mock_ai = MagicMock()
    mock_ai.generate_structured = AsyncMock(return_value={
        "scenes": [
            {"scene_id": 1, "narration": "Stop scrolling right now.", "visual_type": "motion_graphic", "visual_prompt": "Bold glowing 3D text", "caption": "STOP SCROLLING", "transition": "cut"},
            {"scene_id": 2, "narration": "Manual research takes forever.", "visual_type": "stock_footage", "visual_prompt": "Frustrated student at laptop", "caption": "THE OLD WAY", "transition": "cut"},
            {"scene_id": 3, "narration": "Use Consensus instead.", "visual_type": "screen_recording", "visual_prompt": "Software UI searching scientific papers", "caption": "CONSENSUS AI", "transition": "zoom"}
        ]
    })

    agent = StoryboardAgent(ai_provider=mock_ai)
    script = Script(
        topic="5 AI Tools",
        hook="Stop scrolling right now.",
        problem="Research takes forever.",
        value="Use Consensus instead.",
        payoff="Done in seconds.",
        cta="Follow for more.",
        full_narration="Stop scrolling right now. Research takes forever. Use Consensus instead. Done in seconds. Follow for more.",
        target_duration_sec=10.0
    )

    storyboard = await agent.create_storyboard(script, total_duration=10.0)
    assert len(storyboard.scenes) > 1
    assert storyboard.scenes[0].caption != ""
    assert storyboard.scenes[0].visual_prompt != ""


@pytest.mark.anyio
async def test_media_agent_collects_real_scene_assets(tmp_path):
    """Verify MediaAgent acquires valid 1080x1920 files and populates license info."""
    storage = LocalStorageProvider(base_dir=str(tmp_path))
    stock_engine = StockMediaEngine(media_dir=str(tmp_path / "assets"))

    media_agent = MediaAgent(stock_provider=stock_engine, storage_provider=storage)

    # Mock simple storyboard with 2 scenes
    from backend.app.models.video import Storyboard, Scene
    scene1 = Scene(scene_id=1, start=0.0, end=2.5, narration="Hook", visual_type=VisualType.MOTION_GRAPHIC, visual_prompt="Opening Title Card")
    scene2 = Scene(scene_id=2, start=2.5, end=5.0, narration="Problem", visual_type=VisualType.SCREEN_RECORDING, visual_prompt="Software Walkthrough")
    storyboard = Storyboard(scenes=[scene1, scene2], total_duration=5.0)

    updated_sb = await media_agent.collect_scene_assets(storyboard, job_id="test_job_123")

    for sc in updated_sb.scenes:
        assert sc.asset_local_path is not None
        assert Path(sc.asset_local_path).exists()
        assert sc.license_info is not None

        # Verify image dimensions
        with Image.open(sc.asset_local_path) as img:
            assert img.width == 1080
            assert img.height == 1920
