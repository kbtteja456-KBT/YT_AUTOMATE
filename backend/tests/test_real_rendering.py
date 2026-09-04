"""End-to-end integration test: Real FFmpeg rendering, real TTS, real ASS subtitles, and real QC audit."""

import pytest
from pathlib import Path

from backend.app.models.video import Storyboard, Scene, VisualType, Script
from backend.app.models.style_profile import StyleProfile
from backend.app.providers.storage.local_storage import LocalStorageProvider
from backend.app.providers.media.stock_media import StockMediaEngine
from backend.app.providers.tts.edge_tts_provider import EdgeTTSProvider
from backend.app.agents.caption import CaptionAgent
from backend.app.agents.editor import EditorAgent
from backend.app.agents.qc import QCAgent
from backend.app.core.ffmpeg_utils import probe_video_metadata


@pytest.mark.anyio
async def test_end_to_end_real_rendering_and_qc(tmp_path):
    """Render a real 1080x1920 MP4 using real Edge-TTS, real FFmpeg, and audit with QCAgent."""
    storage = LocalStorageProvider(base_dir=str(tmp_path))
    stock_engine = StockMediaEngine(media_dir=str(tmp_path / "assets"))
    tts = EdgeTTSProvider()

    job_id = "real_render_test_777"

    # 1. Synthesize real audio for a short 5-second test narration
    test_script = Script(
        topic="5 AI Tools Every Student Must Know",
        hook="Stop scrolling right now.",
        problem="Research takes hours.",
        value="Use these two tools to finish in seconds.",
        payoff="You get your weekends back.",
        cta="Save this video.",
        full_narration="Stop scrolling right now. Research takes hours. Use these two tools to finish in seconds. Save this video.",
        target_duration_sec=6.0
    )

    voice_file = storage.get_path("audio", f"voice_{job_id}.mp3")
    audio_path = await tts.synthesize_speech(
        text=test_script.full_narration,
        output_filepath=voice_file,
        voice_id="en-US-ChristopherNeural"
    )
    assert Path(audio_path).exists()
    assert Path(audio_path).stat().st_size > 0

    # 2. Acquire 2 real 1080x1920 procedural scenes
    scenes_dir = str(tmp_path / "scenes")
    scene1 = await stock_engine.search_and_acquire("Stop Scrolling Right Now", duration_sec=3.0, target_dir=scenes_dir)
    scene1.scene_id = 1
    scene1.start = 0.0
    scene1.end = 3.0

    scene2 = await stock_engine.search_and_acquire("Consensus AI Scientific Search", duration_sec=3.5, target_dir=scenes_dir)
    scene2.scene_id = 2
    scene2.start = 3.0
    scene2.end = 6.5

    storyboard = Storyboard(scenes=[scene1, scene2], total_duration=6.5)

    # 3. Build synchronized ASS subtitles
    mock_stt = None
    from backend.app.models.video import CaptionSegment, CaptionWord
    segments = [
        CaptionSegment(
            text="STOP SCROLLING RIGHT NOW",
            start=0.0,
            end=3.0,
            words=[
                CaptionWord(word="STOP", start=0.0, end=0.6),
                CaptionWord(word="SCROLLING", start=0.6, end=1.5),
                CaptionWord(word="RIGHT", start=1.5, end=2.0),
                CaptionWord(word="NOW", start=2.0, end=3.0)
            ]
        ),
        CaptionSegment(
            text="RESEARCH TAKES HOURS",
            start=3.0,
            end=6.0,
            words=[
                CaptionWord(word="RESEARCH", start=3.0, end=4.5),
                CaptionWord(word="TAKES", start=4.5, end=5.2),
                CaptionWord(word="HOURS", start=5.2, end=6.0)
            ]
        )
    ]
    caption_agent = CaptionAgent(stt_provider=mock_stt, storage_provider=storage)
    ass_file = storage.get_path("captions", f"captions_{job_id}.ass")
    ass_path = caption_agent.build_ass_subtitles(segments, ass_file)
    assert Path(ass_path).exists()

    # 4. Render 1080x1920 MP4 with EditorAgent (FFmpeg)
    editor = EditorAgent(storage_provider=storage)
    rendered_video_path = await editor.render_video(
        storyboard=storyboard,
        audio_path=audio_path,
        captions_ass_path=ass_path,
        job_id=job_id
    )

    assert Path(rendered_video_path).exists()
    assert Path(rendered_video_path).stat().st_size > 10000

    # 5. Probe rendered video with FFmpeg
    meta = probe_video_metadata(rendered_video_path)
    assert meta["width"] == 1080
    assert meta["height"] == 1920
    assert meta["audio_present"] is True
    assert "264" in meta["video_codec"]
    assert "aac" in meta["audio_codec"]
    assert meta["duration"] > 0.0

    # 6. Audit with QCAgent
    qc_agent = QCAgent(ai_provider=None)
    qc_report = await qc_agent.audit_video(
        video_path=rendered_video_path,
        min_duration=2.0,  # Scaled min duration for test Short
        max_duration=15.0
    )

    assert qc_report.score >= 90.0
    assert qc_report.passed is True
    assert qc_report.resolution_valid is True
    assert qc_report.audio_present is True
