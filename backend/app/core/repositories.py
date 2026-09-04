"""Repository data access layer for MongoDB collections."""

import inspect
from datetime import datetime, timezone
from typing import Optional, Any
from bson import ObjectId

from backend.app.models.job import PublishingJob, JobState, JobStageLog
from backend.app.models.video import Video
from backend.app.models.settings import ChannelSettings
from backend.app.models.activity import ActivityEvent
from backend.app.models.style_profile import StyleProfile
from backend.app.models.channel import YouTubeChannel, OAuthTokenRecord


class JobRepository:
    """Handles CRUD and state updates for PublishingJob documents."""

    def __init__(self, db: Any):
        self.collection = db["publishing_jobs"]

    async def _maybe_await(self, value: Any) -> Any:
        """Support both async Motor and sync PyMongo collection methods."""
        if inspect.isawaitable(value):
            return await value
        return value

    async def create_job(self, job: PublishingJob) -> PublishingJob:
        """Insert new publishing job."""
        doc = job.to_mongo_dict()
        res = await self._maybe_await(self.collection.insert_one(doc))
        job.id = str(res.inserted_id)
        return job

    async def get_job_by_id(self, job_id: str) -> Optional[PublishingJob]:
        """Fetch job by string id or ObjectId."""
        query = {"_id": ObjectId(job_id) if ObjectId.is_valid(job_id) else job_id}
        data = await self._maybe_await(self.collection.find_one(query))
        if data:
            data["_id"] = str(data["_id"])
            return PublishingJob.model_validate(data)
        return None

    async def get_job_by_idempotency_key(self, key: str) -> Optional[PublishingJob]:
        """Fetch job by idempotency key to prevent duplicates."""
        data = await self._maybe_await(self.collection.find_one({"idempotency_key": key}))
        if data:
            data["_id"] = str(data["_id"])
            return PublishingJob.model_validate(data)
        return None

    async def update_job_state(
        self,
        job_id: str,
        new_state: JobState,
        error_message: Optional[str] = None,
        qc_score: Optional[float] = None
    ) -> None:
        """Update job state and status metadata."""
        query = {"_id": ObjectId(job_id) if ObjectId.is_valid(job_id) else job_id}
        update_fields: dict[str, Any] = {
            "state": new_state.value,
            "updated_at": datetime.now(timezone.utc)
        }
        if error_message is not None:
            update_fields["error_message"] = error_message
        if qc_score is not None:
            update_fields["qc_score"] = qc_score

        await self._maybe_await(self.collection.update_one(query, {"$set": update_fields}))

    async def append_stage_log(self, job_id: str, log: JobStageLog) -> None:
        """Append stage execution audit log to job."""
        query = {"_id": ObjectId(job_id) if ObjectId.is_valid(job_id) else job_id}
        await self._maybe_await(self.collection.update_one(
            query,
            {
                "$push": {"stage_logs": log.to_mongo_dict()},
                "$set": {
                    "last_completed_stage": log.stage.value,
                    "updated_at": datetime.now(timezone.utc)
                }
            }
        ))

    async def get_in_progress_jobs(self) -> list[PublishingJob]:
        """Fetch jobs that were running when system crashed or restarted."""
        in_progress_states = [
            JobState.QUEUED.value,
            JobState.RESEARCHING.value,
            JobState.SCRIPTING.value,
            JobState.STORYBOARDING.value,
            JobState.GENERATING_MEDIA.value,
            JobState.GENERATING_VOICE.value,
            JobState.GENERATING_CAPTIONS.value,
            JobState.RENDERING.value,
            JobState.QUALITY_CHECK.value,
            JobState.GENERATING_THUMBNAIL.value
        ]
        cursor = self.collection.find({"state": {"$in": in_progress_states}})
        jobs = []
        async for doc in cursor:
            doc["_id"] = str(doc["_id"])
            jobs.append(PublishingJob.model_validate(doc))
        return jobs

    async def count_published_today(self, channel_id: Optional[str] = None) -> int:
        """Count videos published today to enforce daily_video_limit."""
        today_start = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
        query: dict[str, Any] = {
            "state": JobState.PUBLISHED.value,
            "published_at": {"$gte": today_start}
        }
        if channel_id:
            query["channel_id"] = channel_id
        return await self.collection.count_documents(query)


class VideoRepository:
    """Handles CRUD for rendered Video assets."""

    def __init__(self, db: Any):
        self.collection = db["videos"]

    async def _maybe_await(self, value: Any) -> Any:
        """Support both async and sync collection methods."""
        if inspect.isawaitable(value):
            return await value
        return value

    async def create_video(self, video: Video) -> Video:
        """Insert completed video record."""
        doc = video.to_mongo_dict()
        res = await self._maybe_await(self.collection.insert_one(doc))
        video.id = str(res.inserted_id)
        return video

    async def get_video_by_id(self, video_id: str) -> Optional[Video]:
        """Fetch video by id."""
        query = {"_id": ObjectId(video_id) if ObjectId.is_valid(video_id) else video_id}
        data = await self._maybe_await(self.collection.find_one(query))
        if data:
            data["_id"] = str(data["_id"])
            return Video.model_validate(data)
        return None

    async def get_video_by_hash(self, file_hash: str) -> Optional[Video]:
        """Fetch video by SHA-256 hash to prevent duplicate uploads."""
        data = await self._maybe_await(self.collection.find_one({"file_hash": file_hash}))
        if data:
            data["_id"] = str(data["_id"])
            return Video.model_validate(data)
        return None

    async def list_recent_videos(self, limit: int = 20) -> list[Video]:
        """List recently rendered and published videos."""
        cursor = self.collection.find().sort("created_at", -1).limit(limit)
        videos = []
        if hasattr(cursor, '__aiter__'):
            async for doc in cursor:
                doc["_id"] = str(doc["_id"])
                videos.append(Video.model_validate(doc))
            return videos
        for doc in cursor:
            doc["_id"] = str(doc["_id"])
            videos.append(Video.model_validate(doc))
        return videos


class SettingsRepository:
    """Manages channel and autopilot settings document."""

    def __init__(self, db: Any):
        self.collection = db["channel_settings"]

    async def _maybe_await(self, value: Any) -> Any:
        """Support both async and sync collection methods."""
        if inspect.isawaitable(value):
            return await value
        return value

    async def get_settings(self) -> ChannelSettings:
        """Retrieve settings or create default."""
        data = await self._maybe_await(self.collection.find_one({}))
        if data:
            data["_id"] = str(data["_id"])
            return ChannelSettings.model_validate(data)
        default_settings = ChannelSettings()
        await self._maybe_await(self.collection.insert_one(default_settings.to_mongo_dict()))
        return default_settings

    async def save_settings(self, settings: ChannelSettings) -> None:
        """Upsert settings."""
        doc = settings.to_mongo_dict()
        await self._maybe_await(self.collection.update_one({}, {"$set": doc}, upsert=True))


class ActivityRepository:
    """Handles audit activity event records."""

    def __init__(self, db: Any):
        self.collection = db["activity"]

    async def _maybe_await(self, value: Any) -> Any:
        """Support both async and sync collection methods."""
        if inspect.isawaitable(value):
            return await value
        return value

    async def log_event(self, event: ActivityEvent) -> ActivityEvent:
        """Append event to live audit feed."""
        doc = event.to_mongo_dict()
        res = await self._maybe_await(self.collection.insert_one(doc))
        event.id = str(res.inserted_id)
        return event

    async def get_recent_events(self, limit: int = 50) -> list[ActivityEvent]:
        """Retrieve recent events in descending order."""
        cursor = self.collection.find().sort([("timestamp", -1), ("_id", -1)]).limit(limit)
        events = []
        if hasattr(cursor, '__aiter__'):
            async for doc in cursor:
                doc["_id"] = str(doc["_id"])
                events.append(ActivityEvent.model_validate(doc))
            return events
        for doc in cursor:
            doc["_id"] = str(doc["_id"])
            events.append(ActivityEvent.model_validate(doc))
        return events


class StyleProfileRepository:
    """Manages active reference video style blueprint."""

    def __init__(self, db: Any):
        self.collection = db["style_profiles"]

    async def _maybe_await(self, value: Any) -> Any:
        """Support both async and sync collection methods."""
        if inspect.isawaitable(value):
            return await value
        return value

    async def get_active_profile(self) -> StyleProfile:
        """Retrieve active style profile or default."""
        data = await self._maybe_await(self.collection.find_one({"is_active": True}))
        if data:
            data["_id"] = str(data["_id"])
            return StyleProfile.model_validate(data)
        default_profile = StyleProfile()
        await self._maybe_await(self.collection.insert_one(default_profile.to_mongo_dict()))
        return default_profile

    async def save_profile(self, profile: StyleProfile) -> None:
        """Save style profile."""
        doc = profile.to_mongo_dict()
        await self._maybe_await(self.collection.update_one(
            {"name": profile.name},
            {"$set": doc},
            upsert=True
        ))
