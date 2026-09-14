"""Tests for the post-publication email notification system."""

import pytest
from datetime import datetime, timezone
from unittest.mock import patch, MagicMock
from bson import ObjectId

from backend.app.core.notifications import (
    format_published_time,
    build_email_content,
    send_video_published_email,
    notify_workspace_owner_video_published
)
from backend.app.config import settings


def test_format_published_time():
    """Test formatting of timestamps into local timezone string."""
    dt = datetime(2026, 9, 14, 1, 30, 0, tzinfo=timezone.utc)
    # 01:30 UTC is 07:00 AM IST
    res = format_published_time(dt, tz_name="Asia/Kolkata")
    assert "September 14, 2026" in res
    assert "07:00:00 AM" in res


def test_build_email_content_contains_all_details():
    """Test that email body contains title, link, time, and channel info."""
    text, html = build_email_content(
        to_email="creator@example.com",
        video_title="10 Python Secrets You Must Know",
        video_url="https://www.youtube.com/shorts/sample123",
        published_time_str="Monday, September 14, 2026 at 07:00:00 AM (IST)",
        channel_title="Python Master",
        workspace_name="Python Workspace"
    )

    # Verify plain text content
    assert "10 Python Secrets You Must Know" in text
    assert "https://www.youtube.com/shorts/sample123" in text
    assert "Monday, September 14, 2026 at 07:00:00 AM (IST)" in text
    assert "Python Master" in text

    # Verify HTML content
    assert "10 Python Secrets You Must Know" in html
    assert "https://www.youtube.com/shorts/sample123" in html
    assert "Monday, September 14, 2026 at 07:00:00 AM (IST)" in html
    assert "Python Master" in html
    assert "Watch on YouTube" in html


def test_send_email_graceful_when_smtp_not_configured():
    """Test that when SMTP credentials are empty, notification returns False gracefully."""
    with patch.object(settings, "smtp_user", ""), patch.object(settings, "smtp_password", ""):
        res = send_video_published_email(
            to_email="user@example.com",
            video_title="Test Short",
            video_url="https://www.youtube.com/shorts/test",
            published_time=datetime.now(timezone.utc)
        )
        assert res is False


def test_send_email_success_with_mock_smtp():
    """Test successful email dispatch using mocked SMTP server."""
    with patch.object(settings, "smtp_user", "notifier@gmail.com"), \
         patch.object(settings, "smtp_password", "secretapppass123"), \
         patch.object(settings, "smtp_host", "smtp.gmail.com"), \
         patch.object(settings, "smtp_port", 587), \
         patch.object(settings, "smtp_use_tls", True), \
         patch("smtplib.SMTP") as mock_smtp_cls:

        mock_server = MagicMock()
        mock_smtp_cls.return_value.__enter__.return_value = mock_server

        res = send_video_published_email(
            to_email="pranith@gmail.com",
            video_title="Java Banker's Rounding Explained",
            video_url="https://www.youtube.com/shorts/sampleJava",
            published_time=datetime.now(timezone.utc),
            channel_title="Pranith Tech"
        )

        assert res is True
        mock_server.starttls.assert_called_once()
        mock_server.login.assert_called_once_with("notifier@gmail.com", "secretapppass123")
        mock_server.send_message.assert_called_once()

        # Check message attributes
        sent_msg = mock_server.send_message.call_args[0][0]
        assert sent_msg["To"] == "pranith@gmail.com"
        assert "Java Banker's Rounding Explained" in sent_msg["Subject"]


def test_send_email_handles_smtp_exception_safely():
    """Test that SMTP network/auth failures never raise exceptions to caller."""
    with patch.object(settings, "smtp_user", "notifier@gmail.com"), \
         patch.object(settings, "smtp_password", "secretapppass123"), \
         patch("smtplib.SMTP") as mock_smtp_cls:

        mock_server = MagicMock()
        mock_server.login.side_effect = Exception("SMTP Authentication Error")
        mock_smtp_cls.return_value.__enter__.return_value = mock_server

        # Must return False and not raise
        res = send_video_published_email(
            to_email="sindhu@gmail.com",
            video_title="C Quiz",
            video_url="https://www.youtube.com/shorts/cquiz"
        )
        assert res is False


def test_notify_workspace_owner_resolves_user_and_sends():
    """Test resolving user from database and triggering send_video_published_email."""
    dummy_ws_id = str(ObjectId())
    dummy_user_id = str(ObjectId())

    mock_db = MagicMock()
    mock_db.workspaces.find_one.return_value = {
        "_id": ObjectId(dummy_ws_id),
        "owner_id": dummy_user_id,
        "name": "Sindhu's Workspace",
        "connected_channel_id": "UC12345678",
        "schedule": {"timezone": "Asia/Kolkata"}
    }
    mock_db.users.find_one.return_value = {
        "_id": ObjectId(dummy_user_id),
        "email": "sindhu@gmail.com",
        "full_name": "Sindhu"
    }
    mock_db.youtube_channels.find_one.return_value = {
        "channel_id": "UC12345678",
        "title": "Sindhu Coding"
    }

    with patch("backend.app.core.db.SyncMongoDB.get_db", return_value=mock_db), \
         patch("backend.app.core.notifications.send_video_published_email") as mock_send:

        mock_send.return_value = True

        res = notify_workspace_owner_video_published(
            workspace_id=dummy_ws_id,
            video_title="C Pointers in 60 Seconds",
            video_url="https://www.youtube.com/shorts/cpointers",
            published_time=datetime.now(timezone.utc)
        )

        assert res is True
        mock_send.assert_called_once()
        call_kwargs = mock_send.call_args[1]
        assert call_kwargs["to_email"] == "sindhu@gmail.com"
        assert call_kwargs["video_title"] == "C Pointers in 60 Seconds"
        assert call_kwargs["video_url"] == "https://www.youtube.com/shorts/cpointers"
        assert call_kwargs["channel_title"] == "Sindhu Coding"
        assert call_kwargs["cc_email"] == "kbtteja456@gmail.com"
