"""Structured logging configuration for AI YouTube Shorts Autopilot."""

import logging
import sys
from typing import Any


def setup_logging(level: str = "INFO") -> logging.Logger:
    """Configure structured console logging with timestamp and component tags."""
    logger = logging.getLogger("autopilot")
    if logger.handlers:
        return logger

    logger.setLevel(getattr(logging, level.upper(), logging.INFO))
    formatter = logging.Formatter(
        "[%(asctime)s] [%(levelname)s] [%(name)s] %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )

    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    return logger


logger = setup_logging()
