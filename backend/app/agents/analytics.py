"""AnalyticsAgent gathering genuine YouTube Data and Analytics metrics."""

from typing import Any, Optional
from backend.app.agents.base import BaseAgent
from backend.app.core.logging import logger
from backend.app.providers.base import YouTubeProvider


class AnalyticsAgent(BaseAgent):
    """Monitors real YouTube video performance. Never fabricates 0s."""

    name = "AnalyticsAgent"

    def __init__(self, youtube_provider: YouTubeProvider):
        self.yt = youtube_provider

    async def collect_video_performance(self, youtube_video_id: str) -> dict[str, Any]:
        """Query real analytics for a published Short."""
        self.log(f"Fetching real performance metrics for video ID: {youtube_video_id}...")

        analytics = await self.yt.get_video_analytics(youtube_video_id)

        # Enforce NOT AVAILABLE for any missing metric
        for key in ["views", "likes", "comments", "retention_pct"]:
            if key not in analytics or analytics[key] is None:
                analytics[key] = "NOT AVAILABLE"

        self.log(f"Analytics collected: views={analytics.get('views')}, likes={analytics.get('likes')}")
        return analytics
