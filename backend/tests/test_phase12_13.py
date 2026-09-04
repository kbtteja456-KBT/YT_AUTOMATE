"""Real unit tests for Phases 12 & 13: VoiceAgent (TTS) and CaptionAgent (STT/ASS)."""

import pytest
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock

from backend.app.models.video import Script, CaptionSegment, CaptionWord
from backend.app.agents.voice import VoiceAgent
from backend.app.agents.caption import CaptionAgent
from backend.app.providers.tts.edge_tts_provider import EdgeTTSProvider
from backend.app.providers.storage.local_storage import LocalStorageProvider


@pytest.mark.anyio
async def test_voice_agent_audio_synthesis(tmp_path):
    """Verify VoiceAgent coordinates with TTSProvider to create valid audio."""
    storage = LocalStorageProvider(base_dir=str(tmp_path))
    tts = EdgeTTSProvider()
    agent = VoiceAgent(tts_provider=tts, storage_provider=storage)

    script = Script(
        topic="Testing Speech",
        hook="Stop scrolling right now.",
        problem="You are wasting time.",
        value="This automated system does everything.",
        payoff="It saves you hours daily.",
        cta="Save this video.",
        full_narration="Stop scrolling right now. You are wasting time. This automated system does everything. It saves you hours daily. Save this video.",
        target_duration_sec=15.0
    )

    audio_path = await agent.generate_voiceover(script, job_id="test_voice_101")
    assert Path(audio_path).exists()
    assert Path(audio_path).stat().st_size > 3000


def test_caption_agent_ass_formatting(tmp_path):
    """Verify CaptionAgent builds compliant ASS subtitle file with safe margins."""
    storage = LocalStorageProvider(base_dir=str(tmp_path))
    mock_stt = MagicMock()
    agent = CaptionAgent(stt_provider=mock_stt, storage_provider=storage)

    assert agent._format_timestamp_ass(2.5) == "0:00:02.50"
    assert agent._format_timestamp_ass(65.12) == "0:01:05.12"

    segments = [
        CaptionSegment(
            text="STOP SCROLLING RIGHT NOW",
            start=0.0,
            end=2.2,
            words=[
                CaptionWord(word="STOP", start=0.0, end=0.6),
                CaptionWord(word="SCROLLING", start=0.6, end=1.4),
                CaptionWord(word="RIGHT", start=1.4, end=1.8),
                CaptionWord(word="NOW", start=1.8, end=2.2),
            ]
        )
    ]

    out_file = str(tmp_path / "captions" / "test.ass")
    ass_path = agent.build_ass_subtitles(segments, out_file)

    assert Path(ass_path).exists()
    content = Path(ass_path).read_text(encoding="utf-8")
    assert "PlayResX: 1080" in content
    assert "PlayResY: 1920" in content
    assert "MarginV: 420" in content
    assert "Dialogue:" in content
    assert "STOP SCROLLING RIGHT" in content


@pytest.mark.anyio
async def test_caption_agent_pipeline_execution(tmp_path):
    """Verify CaptionAgent end-to-end flow with STT provider."""
    storage = LocalStorageProvider(base_dir=str(tmp_path))
    mock_stt = MagicMock()
    mock_stt.transcribe_audio = AsyncMock(return_value=[
        CaptionSegment(
            text="Hello world",
            start=0.0,
            end=1.5,
            words=[
                CaptionWord(word="Hello", start=0.0, end=0.7),
                CaptionWord(word="world", start=0.7, end=1.5)
            ]
        )
    ])

    agent = CaptionAgent(stt_provider=mock_stt, storage_provider=storage)
    ass_path, segments = await agent.generate_captions("mock_audio.mp3", job_id="test_cap_102")

    assert Path(ass_path).exists()
    assert len(segments) == 1
    assert "HELLO WORLD" in Path(ass_path).read_text(encoding="utf-8")
