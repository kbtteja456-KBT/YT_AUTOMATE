"""Persistent Celery Beat schedule definitions for 2 daily Shorts."""

from celery.schedules import crontab
from backend.app.celery_app.celery import celery_app

celery_app.conf.beat_schedule = {
    # Morning Video Pre-generation: 01:00 Daily
    "pregenerate-morning-short": {
        "task": "backend.app.celery_app.tasks.pregenerate_slot_task",
        "schedule": crontab(hour=1, minute=0),
        "args": (1,),
    },
    # Morning Video Publish Gate: 07:00 Daily
    "publish-morning-short": {
        "task": "backend.app.celery_app.tasks.publish_slot_task",
        "schedule": crontab(hour=7, minute=0),
        "args": (1,),
    },
    # Evening Video Pre-generation: 12:00 Daily
    "pregenerate-evening-short": {
        "task": "backend.app.celery_app.tasks.pregenerate_slot_task",
        "schedule": crontab(hour=12, minute=0),
        "args": (2,),
    },
    # Evening Video Publish Gate: 18:00 Daily
    "publish-evening-short": {
        "task": "backend.app.celery_app.tasks.publish_slot_task",
        "schedule": crontab(hour=18, minute=0),
        "args": (2,),
    },
    # Recovery & Maintenance Reconciler: Every 30 Minutes
    "periodic-system-reconciliation": {
        "task": "backend.app.celery_app.tasks.reconcile_system_jobs_task",
        "schedule": crontab(minute="*/30"),
    },
}
