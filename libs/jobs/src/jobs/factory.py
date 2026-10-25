"""Choose a job store from config: Redis when a URL is set, else in-memory."""

from __future__ import annotations

from .store import InMemoryJobStore, JobStore, RedisJobStore


def make_store(redis_url: str | None) -> JobStore:
    if redis_url:
        import redis.asyncio as aioredis

        return RedisJobStore(aioredis.from_url(redis_url))
    return InMemoryJobStore()
