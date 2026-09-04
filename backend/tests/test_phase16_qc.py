"""Real unit tests for Phase 16: Quality Control Agent and Hard Gate Scoring."""

import pytest
from unittest.mock import patch, MagicMock
from backend.app.agents.qc import QCAgent
from backend.app.models.video import QCReport


@pytest.mark.anyio
async def test_qc_agent_perfect_video_passes_threshold():
    """Verify that a compliant 1080x1920 vertical Short scores 100/100 and passes QC."""
    mock_meta = {
        "width": 1080,
        "height": 1920,
        "duration": 45.0,
        "video_codec": "h264",
        "audio_codec": "aac",
        "audio_present": True
    }
    mock_defects = {
        "has_black_frames": False,
        "has_frozen_frames": False,
        "has_prolonged_silence": False,
        "max_volume_db": -2.5,
        "is_clipping": False
    }

    qc = QCAgent(ai_provider=MagicMock())

    with patch("backend.app.agents.qc.probe_video_metadata", return_value=mock_meta), \
         patch("backend.app.agents.qc.audit_video_defects", return_value=mock_defects):

        report = await qc.audit_video("mock_rendered_video.mp4")
        assert report.score == 100.0
        assert report.passed is True
        assert report.resolution_valid is True
        assert report.duration_valid is True
        assert report.audio_present is True
        assert len(report.remediation_notes) == 0


@pytest.mark.anyio
async def test_qc_agent_rejects_horizontal_resolution():
    """Verify that wrong aspect ratio (e.g. 1920x1080 horizontal) fails the >=90 threshold."""
    mock_meta = {
        "width": 1920,
        "height": 1080,  # Horizontal!
        "duration": 45.0,
        "video_codec": "h264",
        "audio_codec": "aac",
        "audio_present": True
    }
    mock_defects = {
        "has_black_frames": False,
        "has_frozen_frames": False,
        "has_prolonged_silence": False,
        "max_volume_db": -2.5,
        "is_clipping": False
    }

    qc = QCAgent(ai_provider=MagicMock())

    with patch("backend.app.agents.qc.probe_video_metadata", return_value=mock_meta), \
         patch("backend.app.agents.qc.audit_video_defects", return_value=mock_defects):

        report = await qc.audit_video("mock_rendered_video.mp4")
        # Loses 20 points for resolution -> score is 80.0
        assert report.score == 80.0
        assert report.passed is False
        assert report.resolution_valid is False
        assert any("Invalid resolution" in note for note in report.remediation_notes)


@pytest.mark.anyio
async def test_qc_agent_rejects_silent_video():
    """Verify that missing audio track causes failure."""
    mock_meta = {
        "width": 1080,
        "height": 1920,
        "duration": 45.0,
        "video_codec": "h264",
        "audio_codec": "",
        "audio_present": False  # Missing audio!
    }
    mock_defects = {
        "has_black_frames": False,
        "has_frozen_frames": False,
        "has_prolonged_silence": True,
        "max_volume_db": -99.0,
        "is_clipping": False
    }

    qc = QCAgent(ai_provider=MagicMock())

    with patch("backend.app.agents.qc.probe_video_metadata", return_value=mock_meta), \
         patch("backend.app.agents.qc.audit_video_defects", return_value=mock_defects):

        report = await qc.audit_video("mock_rendered_video.mp4")
        assert report.score <= 75.0
        assert report.passed is False
        assert report.audio_present is False
        assert any("Audio stream missing" in note for note in report.remediation_notes)
