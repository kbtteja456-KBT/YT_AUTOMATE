"""Celery application instance and queue configuration."""

import os
from celery import Celery
from kombu import Queue
from backend.app.config import settings

celery_app = Celery(
    "youtube_shorts_autopilot",
    broker=settings.redis_url,
    backend=settings.redis_url,
    include=["backend.app.celery_app.tasks"]
)

celery_app.conf.update(
    timezone=settings.timezone,
    enable_utc=True,
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    task_track_started=True,
    task_acks_late=True,
    worker_prefetch_multiplier=1,
    task_queues=(
        Queue("default", routing_key="default.#"),
        Queue("video_rendering", routing_key="render.#"),
    ),
    task_default_queue="default",
    task_routes={
        "backend.app.celery_app.tasks.run_pipeline_task": {"queue": "video_rendering"},
    }
)
