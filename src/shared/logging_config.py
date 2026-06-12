# src/shared/logging_config.py
import logging
from typing import Any

import structlog

from src.settings.settings import get_settings


def _service_name_processor(_, __, event_dict: dict[str, Any]) -> dict[str, Any]:
    settings = get_settings()

    event_dict["service"] = settings.app_name
    return event_dict


def configure_logging() -> None:
    """Set up structlog"""
    settings = get_settings()

    renderer = (
        structlog.dev.ConsoleRenderer()
        if settings.debug
        else structlog.processors.JSONRenderer
    )

    min_level = logging.DEBUG if settings.debug else logging.INFO

    _initialize_logger("src", min_level)
    _initialize_logger("test", logging.DEBUG)

    structlog.configure(
        processors=[
            structlog.contextvars.merge_contextvars,
            structlog.processors.add_log_level,
            _service_name_processor,
            structlog.processors.TimeStamper(utc=True),
            renderer,
        ],
        logger_factory=structlog.PrintLoggerFactory(),
        wrapper_class=structlog.make_filtering_bound_logger(min_level),
    )


def _initialize_logger(logger_name: str, min_level: int | str):
    """Set a python logger min level."""
    handler = logging.StreamHandler()
    handler.setLevel(min_level)
    logger = logging.getLogger(logger_name)
    logger.addHandler(handler)
    logger.propagate = False
