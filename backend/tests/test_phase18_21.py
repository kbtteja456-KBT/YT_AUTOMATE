"""Real unit tests for Phases 18-21: Analytics, Learning, StyleAnalyzer, and Pipeline Orchestration."""

import pytest
from unittest.mock import AsyncMock, MagicMock
from pathlib import Path

from backend.app.agents.analytics import AnalyticsAgent
from backend.app.agents.learning import LearningAgent
from backend.app.agents.style_analyzer import StyleAnalyzerAgent
from backend.app.pipeline.orchestrator import PipelineOrchestrator
from backend.app.models.video import Script, Storyboard, Scene, VisualType, QCReport
from backend.app.models.thumbnail import ThumbnailCard, ThumbnailSpec
from backend.app.models.job import JobState


@pytest.mark.anyio
async def test_analytics_agent_not_available_metrics():
    """Verify AnalyticsAgent handles missing metrics with NOT AVAILABLE."""
    mock_yt = MagicMock()
    mock_yt.get_video_analytics = AsyncMock(return_value={"views": 1500, "likes": None})

    analytics_agent = AnalyticsAgent(youtube_provider=mock_yt)
    metrics = await analytics_agent.collect_video_performance("vid_xyz_99")

    assert metrics["views"] == 1500
    assert metrics["likes"] == "NOT AVAILABLE"
    assert metrics["comments"] == "NOT AVAILABLE"


@pytest.mark.anyio
async def test_learning_agent_retention_patterns():
    """Verify LearningAgent extracts topic suggestions without claiming virality."""
    mock_ai = MagicMock()
    mock_ai.generate_structured = AsyncMock(return_value={
        "high_retention_topics": ["Quantum AI", "Agentic Coding"],
        "recommended_hook_style": "Curiosity gap under 2.5s",
        "recommended_duration_sec": 44.0,
        "notes": "Historical data shows high completion rate on fast tool comparisons."
    })

    learner = LearningAgent(ai_provider=mock_ai)
    insights = await learner.extract_retention_insights(
        historical_videos=[{"title": "AI Tools", "retention": 85}],
        channel_niche="Tech"
    )

    assert "Quantum AI" in insights["high_retention_topics"]
    assert insights["recommended_duration_sec"] == 44.0


@pytest.mark.anyio
async def test_pipeline_orchestrator_execution_flow(tmp_path):
    """Verify PipelineOrchestrator advances through the complete state machine."""
    mock_idea = MagicMock()
    mock_idea.generate_daily_topic = AsyncMock(return_value={"topic": "5 AI Tools"})

    mock_research = MagicMock()
    from backend.app.models.video import ResearchReport, ResearchItem
    mock_rep = ResearchReport(
        topic="5 AI Tools",
        niche="Tech",
        items=[ResearchItem(fact="Tool A is fast", source="source", interpretation="interp")],
        key_takeaway="Fast tools"
    )
    mock_research.conduct_research = AsyncMock(return_value=mock_rep)

    mock_fact = MagicMock()
    mock_fact.verify_and_prune = AsyncMock(return_value=mock_rep)

    mock_hook = MagicMock()
    from backend.app.models.video import Hook
    mock_h = Hook(text="Stop scrolling right now.", selected=True, total_score=9.5)
    mock_hook.generate_and_score_hooks = AsyncMock(return_value=[mock_h])

    mock_script = MagicMock()
    mock_sc = Script(
        topic="5 AI Tools",
        hook="Stop scrolling right now.",
        problem="Problem",
        value="Value",
        payoff="Payoff",
        cta="CTA",
        full_narration="Full text.",
        target_duration_sec=45.0
    )
    mock_script.generate_script = AsyncMock(return_value=mock_sc)

    mock_storyboard = MagicMock()
    mock_sb = Storyboard(
        scenes=[Scene(scene_id=1, start=0.0, end=45.0, narration="Full text", visual_type=VisualType.MOTION_GRAPHIC, visual_prompt="Prompt")],
        total_duration=45.0
    )
    mock_storyboard.create_storyboard = AsyncMock(return_value=mock_sb)

    mock_media = MagicMock()
    mock_media.collect_scene_assets = AsyncMock(return_value=mock_sb)

    mock_voice = MagicMock()
    mock_voice.generate_voiceover = AsyncMock(return_value=str(tmp_path / "voice.mp3"))

    mock_caption = MagicMock()
    mock_caption.generate_captions = AsyncMock(return_value=(str(tmp_path / "captions.ass"), []))

    mock_editor = MagicMock()
    fake_video = tmp_path / "short_rendered.mp4"
    fake_video.write_bytes(b"mock_video_bytes_12345")
    mock_editor.render_video = AsyncMock(return_value=str(fake_video))

    mock_qc = MagicMock()
    mock_qc_report = QCReport(score=96.0, passed=True, resolution_valid=True, duration_valid=True, audio_present=True)
    mock_qc.audit_video = AsyncMock(return_value=mock_qc_report)

    mock_thumb = MagicMock()
    fake_thumb = ThumbnailCard(
        file_path=str(tmp_path / "thumb.jpg"),
        file_hash="hash",
        spec=ThumbnailSpec(source_frame_timestamp=2.0, overlay_text="AI TOOLS")
    )
    mock_thumb.generate_custom_thumbnail = AsyncMock(return_value=fake_thumb)

    mock_title = MagicMock()
    mock_title.generate_title_and_tags = AsyncMock(return_value={"title": "5 AI Tools", "tags": ["AI"], "hashtags": ["#AI"]})

    mock_desc = MagicMock()
    mock_desc.generate_description = AsyncMock(return_value="Description text")

    orchestrator = PipelineOrchestrator(
        idea_agent=mock_idea,
        research_agent=mock_research,
        fact_check_agent=mock_fact,
        hook_agent=mock_hook,
        script_agent=mock_script,
        storyboard_agent=mock_storyboard,
        media_agent=mock_media,
        voice_agent=mock_voice,
        caption_agent=mock_caption,
        editor_agent=mock_editor,
        qc_agent=mock_qc,
        thumbnail_agent=mock_thumb,
        title_agent=mock_title,
        description_agent=mock_desc
    )

    result = await orchestrator.execute_job(job_id="orch_test_001")
    assert result["status"] == "READY"
    assert result["quality_score"] == 96.0
    assert result["title"] == "5 AI Tools"
