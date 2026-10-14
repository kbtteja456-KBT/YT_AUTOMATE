"""Unit tests verifying strict time-window enforcement for autonomous publishing slots."""

import pytest
import zoneinfo
from datetime import datetime

from backend.app.core.cron_scheduler import is_time_in_slot_window


def test_slot_1_morning_window_enforcement():
    tz = zoneinfo.ZoneInfo("Asia/Kolkata")

    # Middle of the night (2:48 AM) -> MUST BE BLOCKED
    allowed, msg = is_time_in_slot_window(1, datetime(2026, 10, 13, 2, 48, tzinfo=tz))
    assert not allowed
    assert "Too early" in msg

    # Early morning before window (6:30 AM) -> MUST BE BLOCKED
    allowed, msg = is_time_in_slot_window(1, datetime(2026, 10, 13, 6, 30, tzinfo=tz))
    assert not allowed
    assert "Too early" in msg

    # Pre-render window open (6:45 AM) -> ALLOWED
    allowed, msg = is_time_in_slot_window(1, datetime(2026, 10, 13, 6, 45, tzinfo=tz))
    assert allowed

    # Target publish time (7:00 AM) -> ALLOWED
    allowed, msg = is_time_in_slot_window(1, datetime(2026, 10, 13, 7, 0, tzinfo=tz))
    assert allowed

    # Morning catch-up (10:30 AM) -> ALLOWED
    allowed, msg = is_time_in_slot_window(1, datetime(2026, 10, 13, 10, 30, tzinfo=tz))
    assert allowed

    # Afternoon cutoff (2:30 PM) -> MUST BE BLOCKED
    allowed, msg = is_time_in_slot_window(1, datetime(2026, 10, 13, 14, 30, tzinfo=tz))
    assert not allowed
    assert "Past Morning Slot 1 window" in msg

    # Evening (6:00 PM) -> MUST BE BLOCKED
    allowed, msg = is_time_in_slot_window(1, datetime(2026, 10, 13, 18, 0, tzinfo=tz))
    assert not allowed


def test_slot_2_evening_window_enforcement():
    tz = zoneinfo.ZoneInfo("Asia/Kolkata")

    # Morning (7:10 AM) -> MUST BE BLOCKED
    allowed, msg = is_time_in_slot_window(2, datetime(2026, 10, 13, 7, 10, tzinfo=tz))
    assert not allowed
    assert "Too early" in msg

    # Afternoon (2:00 PM) -> MUST BE BLOCKED
    allowed, msg = is_time_in_slot_window(2, datetime(2026, 10, 13, 14, 0, tzinfo=tz))
    assert not allowed
    assert "Too early" in msg

    # Before window open (5:30 PM) -> MUST BE BLOCKED
    allowed, msg = is_time_in_slot_window(2, datetime(2026, 10, 13, 17, 30, tzinfo=tz))
    assert not allowed
    assert "Too early" in msg

    # Pre-render window open (5:45 PM) -> ALLOWED
    allowed, msg = is_time_in_slot_window(2, datetime(2026, 10, 13, 17, 45, tzinfo=tz))
    assert allowed

    # Target publish time (6:00 PM) -> ALLOWED
    allowed, msg = is_time_in_slot_window(2, datetime(2026, 10, 13, 18, 0, tzinfo=tz))
    assert allowed

    # Evening catch-up (9:30 PM) -> ALLOWED
    allowed, msg = is_time_in_slot_window(2, datetime(2026, 10, 13, 21, 30, tzinfo=tz))
    assert allowed
