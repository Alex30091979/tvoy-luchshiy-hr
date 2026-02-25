"""Async database for FastAPI (optional)."""
from __future__ import annotations

from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import declarative_base

from libs.common.config import get_settings
from libs.common.models.base import Base
from libs.common.models.db_models import (  # noqa: F401
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

_async_engine = None
_async_session_factory = None


def get_async_engine():
    global _async_engine
    if _async_engine is None:
        _async_engine = create_async_engine(
            get_settings().database_url,
            pool_pre_ping=True,
            echo=get_settings().debug,
        )
    return _async_engine


def get_async_session_factory():
    global _async_session_factory
    if _async_session_factory is None:
        _async_session_factory = async_sessionmaker(
            get_async_engine(),
            class_=AsyncSession,
            autocommit=False,
            autoflush=False,
            expire_on_commit=False,
        )
    return _async_session_factory()


async def get_async_session() -> AsyncGenerator[AsyncSession, None]:
    factory = get_async_session_factory()
    async with factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()
