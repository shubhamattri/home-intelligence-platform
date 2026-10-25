"""Async SQLAlchemy building blocks shared by services (DB-per-service)."""

from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    """Declarative base. Each service subclasses its own models from this."""


def make_engine(url: str) -> AsyncEngine:
    from sqlalchemy.ext.asyncio import create_async_engine

    return create_async_engine(url, pool_pre_ping=True)


def make_session_factory(engine: AsyncEngine) -> async_sessionmaker[AsyncSession]:
    return async_sessionmaker(engine, expire_on_commit=False)


__all__ = ["AsyncEngine", "AsyncSession", "Base", "make_engine", "make_session_factory"]
