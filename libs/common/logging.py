"""Logging facade — uses structlog if available, else standard logging."""
from __future__ import annotations

import logging
from typing import Any

try:
    import structlog
    _USE_STRUCTLOG = True
except ImportError:
    _USE_STRUCTLOG = False


def get_logger(name: str) -> Any:
    if _USE_STRUCTLOG:
        return structlog.get_logger(name)
    return logging.getLogger(name)
