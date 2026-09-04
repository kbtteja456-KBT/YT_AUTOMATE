"""Celery package initialization."""

from backend.app.celery_app.celery import celery_app
import backend.app.celery_app.beat_schedule  # Register schedules

__all__ = ["celery_app"]
