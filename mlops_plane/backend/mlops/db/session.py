# SPDX-License-Identifier: Proprietary
# Copyright 2026-present Citi MLOps Plane.

"""Async SQLAlchemy engine and session lifecycle."""

from __future__ import annotations

from collections.abc import AsyncIterator
from typing import Optional

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from mlops.config import get_settings


_engine: Optional[AsyncEngine] = None
_session_factory: Optional[async_sessionmaker[AsyncSession]] = None


def get_engine() -> AsyncEngine:
    """Return the process-wide async engine, building it on first use."""
    global _engine, _session_factory
    if _engine is None:
        init_engine()
    assert _engine is not None
    return _engine


def init_engine() -> AsyncEngine:
    """Construct the async engine + session factory from current settings."""
    global _engine, _session_factory
    settings = get_settings()
    _engine = create_async_engine(
        settings.db.dsn,
        echo = settings.db.echo,
        future = True,
        pool_pre_ping = True,
    )
    _session_factory = async_sessionmaker(
        bind = _engine,
        expire_on_commit = False,
        class_ = AsyncSession,
    )
    return _engine


async def shutdown_engine() -> None:
    """Dispose the engine cleanly on app shutdown."""
    global _engine, _session_factory
    if _engine is not None:
        await _engine.dispose()
    _engine = None
    _session_factory = None


def async_session_factory() -> async_sessionmaker[AsyncSession]:
    """Return the session factory, lazily initializing the engine if needed."""
    global _session_factory
    if _session_factory is None:
        init_engine()
    assert _session_factory is not None
    return _session_factory


async def get_db() -> AsyncIterator[AsyncSession]:
    """FastAPI dependency: yields a session, commits/rolls back, closes."""
    factory = async_session_factory()
    async with factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
