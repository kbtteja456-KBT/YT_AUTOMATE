"""Base Agent class providing provider bindings, audit logging, and memory access."""

import time
from abc import ABC
from typing import Any, Optional
from datetime import datetime, timezone

from backend.app.core.logging import logger
from backend.app.providers.base import AIProvider, SearchProvider


class BaseAgent(ABC):
    """Abstract base class for all content pipeline agents."""

    name: str = "base_agent"

    def __init__(self, ai_provider: AIProvider, search_provider: Optional[SearchProvider] = None):
        self.ai = ai_provider
        self.search = search_provider

    def log(self, message: str, level: str = "INFO") -> None:
        """Structured logging tagged with agent identity."""
        log_fn = getattr(logger, level.lower(), logger.info)
        log_fn(f"[{self.name}] {message}")
