"""Structured logging configuration."""
from __future__ import annotations

import logging
import sys
from typing import Any

import structlog


def get_logger(name: str) -> structlog.stdlib.BoundLogger:
    """Return a structured logger for the given module name."""
    return structlog.get_logger(name)


def setup_logging(level: str = "INFO", json_logs: bool = False) -> None:
    """Configure structlog and standard logging."""
    shared_processors: list[Any] = [
        structlog.contextvars.merge_contextvars,
        structlog.processors.add_log_level,
        structlog.processors.StackInfoRenderer(),
        structlog.processors.UnicodeDecoder(),
    ]
    if json_logs:
        shared_processors.append(structlog.processors.format_exc_info)
        processors = shared_processors + [structlog.processors.JSONRenderer()]
    else:
        processors = shared_processors + [
            structlog.dev.ConsoleRenderer(colors=True),
        ]
    structlog.configure(
        processors=processors,
        wrapper_class=structlog.make_filtering_bound_logger(logging.getLevelName(level.upper())),
        context_class=dict,
        logger_factory=structlog.PrintLoggerFactory(file=sys.stdout),
        cache_logger_on_first_use=True,
    )
    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=getattr(logging, level.upper(), logging.INFO),
    )
