"""MongoDB connection managers for async (FastAPI/Motor) and sync (Celery/PyMongo)."""

import os
from typing import Optional, Any
from urllib.parse import unquote, quote_plus
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
from pymongo import MongoClient, ASCENDING, DESCENDING
from pymongo.database import Database

from backend.app.config import settings
from backend.app.core.logging import logger


def sanitize_mongodb_uri(uri: str) -> str:
    """Ensure username and password in MongoDB URI are properly RFC 3986 URL-encoded."""
    if not uri or "://" not in uri:
        return uri
    try:
        scheme, rest = uri.split("://", 1)
        if "@" in rest:
            userinfo, host_and_rest = rest.rsplit("@", 1)
            if ":" in userinfo:
                user, password = userinfo.split(":", 1)
                clean_user = quote_plus(unquote(user))
                clean_pass = quote_plus(unquote(password))
                return f"{scheme}://{clean_user}:{clean_pass}@{host_and_rest}"
        return uri
    except Exception:
        return uri


class AsyncMongoDB:
    """Singleton connection holder for asynchronous Motor database."""
    client: Optional[AsyncIOMotorClient] = None
    db: Optional[AsyncIOMotorDatabase] = None

    @classmethod
    async def connect(cls, uri: Optional[str] = None, db_name: Optional[str] = None) -> None:
        """Initialize async Motor MongoDB connection and build indices."""
        target_uri = sanitize_mongodb_uri(uri or settings.mongodb_uri)
        target_db = db_name or settings.mongodb_db_name

        try:
            cls.client = AsyncIOMotorClient(target_uri, serverSelectionTimeoutMS=2000)
            cls.db = cls.client[target_db]
            await cls.create_indices()
            logger.info(f"Connected to Async MongoDB: {target_db}")
        except Exception as e:
            logger.warning(f"Async MongoDB connection note: {e}")

    @classmethod
    async def create_indices(cls) -> None:
        """Create necessary indexes for performance and data integrity."""
        if cls.db is None:
            return

        # 1. Publishing Jobs
        await cls.db.publishing_jobs.create_index(
            [("idempotency_key", ASCENDING)], unique=True
        )
        await cls.db.publishing_jobs.create_index([("scheduled_at", ASCENDING)])
        await cls.db.publishing_jobs.create_index([("state", ASCENDING)])

        # 2. Videos
        await cls.db.videos.create_index(
            [("file_hash", ASCENDING)], unique=True, sparse=True
        )
        await cls.db.videos.create_index(
            [("youtube_video_id", ASCENDING)], unique=True, sparse=True
        )
        await cls.db.videos.create_index([("created_at", DESCENDING)])

        # 3. Activity Feed
        await cls.db.activity.create_index([("timestamp", DESCENDING)])

        # 4. OAuth Tokens
        await cls.db.oauth_tokens.create_index(
            [("channel_id", ASCENDING)], unique=True
        )

        # 5. Content Ideas
        await cls.db.content_ideas.create_index([("topic", ASCENDING)])

    @classmethod
    async def disconnect(cls) -> None:
        """Close Motor client."""
        if cls.client:
            cls.client.close()
            cls.client = None
            cls.db = None
            logger.info("Closed Async MongoDB connection.")

    @classmethod
    def get_db(cls) -> AsyncIOMotorDatabase:
        """Get active async database instance, connecting if needed."""
        if cls.db is None:
            cls.client = AsyncIOMotorClient(settings.mongodb_uri, serverSelectionTimeoutMS=5000)
            cls.db = cls.client[settings.mongodb_db_name]
        return cls.db


class SyncMongoDB:
    """Singleton connection holder for synchronous PyMongo database (used in Celery)."""
    client: Optional[MongoClient] = None
    db: Optional[Database] = None

    @classmethod
    def connect(cls, uri: Optional[str] = None, db_name: Optional[str] = None) -> Database:
        """Initialize synchronous PyMongo connection."""
        target_uri = sanitize_mongodb_uri(uri or settings.mongodb_uri)
        target_db = db_name or settings.mongodb_db_name

        if cls.client is None:
            cls.client = MongoClient(target_uri, serverSelectionTimeoutMS=15000)
            cls.db = cls.client[target_db]
            logger.info(f"Connected to Sync PyMongo: {target_db}")
        return cls.db

    @classmethod
    def disconnect(cls) -> None:
        """Close PyMongo client."""
        if cls.client:
            cls.client.close()
            cls.client = None
            cls.db = None
            logger.info("Closed Sync PyMongo connection.")

    @classmethod
    def get_db(cls) -> Database:
        """Get active sync database instance."""
        if cls.db is None:
            return cls.connect()
        return cls.db
