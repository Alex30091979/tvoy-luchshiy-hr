"""Database session and engine (sync for RQ workers, async for FastAPI)."""
from __future__ import annotations

from contextlib import contextmanager
from typing import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from libs.common.config import get_settings
from libs.common.models.base import Base
from libs.common.models.db_models import (  # noqa: F401 — for Base.metadata
    Article,
    Cluster,
    Job,
    Keyword,
    LinkSite,
    LinkTask,
    CaseTemplate,
    Performance,
    Setting,
)


def get_engine():
    settings = get_settings()
    return create_engine(
        settings.database_url_sync,
        pool_pre_ping=True,
        echo=settings.debug,
    )


def get_session_factory():
    engine = get_engine()
    return sessionmaker(engine, autocommit=False, autoflush=False, expire_on_commit=False)


_session_factory: sessionmaker[Session] | None = None


def get_sync_session() -> Session:
    global _session_factory
    if _session_factory is None:
        _session_factory = get_session_factory()
    return _session_factory()


@contextmanager
def session_scope() -> Generator[Session, None, None]:
    session = get_sync_session()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()
