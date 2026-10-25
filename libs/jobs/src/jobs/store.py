"""Job stores. In-memory adapter for tests/dev, Redis adapter for the real queue.

Both satisfy the JobStore protocol so the API and worker are storage-agnostic.
"""

from __future__ import annotations

import asyncio
import json
import uuid
from typing import Any, Protocol

from .models import JobState, JobStatus

_QUEUE_KEY = "jobs:queue"


class JobStore(Protocol):
    async def enqueue(self, task: str, params: dict[str, Any]) -> str: ...
    async def get(self, job_id: str) -> JobStatus | None: ...
    async def reserve(self) -> JobStatus | None: ...
    async def complete(self, job_id: str, result: Any) -> None: ...
    async def fail(self, job_id: str, error: str) -> None: ...


def _new_id() -> str:
    return uuid.uuid4().hex


class InMemoryJobStore:
    def __init__(self) -> None:
        self._jobs: dict[str, JobStatus] = {}
        self._pending: asyncio.Queue[str] = asyncio.Queue()

    async def enqueue(self, task: str, params: dict[str, Any]) -> str:
        job_id = _new_id()
        self._jobs[job_id] = JobStatus(id=job_id, task=task, state=JobState.QUEUED, params=params)
        await self._pending.put(job_id)
        return job_id

    async def get(self, job_id: str) -> JobStatus | None:
        return self._jobs.get(job_id)

    async def reserve(self) -> JobStatus | None:
        try:
            job_id = self._pending.get_nowait()
        except asyncio.QueueEmpty:
            return None
        job = self._jobs[job_id]
        job.state = JobState.RUNNING
        return job

    async def complete(self, job_id: str, result: Any) -> None:
        job = self._jobs[job_id]
        job.state = JobState.DONE
        job.result = result

    async def fail(self, job_id: str, error: str) -> None:
        job = self._jobs[job_id]
        job.state = JobState.FAILED
        job.error = error


class RedisJobStore:
    """Redis-backed queue. Job data lives in a hash; ids flow through a list."""

    def __init__(self, redis: Any) -> None:
        self._r = redis

    @staticmethod
    def _key(job_id: str) -> str:
        return f"job:{job_id}"

    async def enqueue(self, task: str, params: dict[str, Any]) -> str:
        job_id = _new_id()
        await self._r.hset(
            self._key(job_id),
            mapping={
                "id": job_id,
                "task": task,
                "state": JobState.QUEUED.value,
                "params": json.dumps(params),
                "result": "",
                "error": "",
            },
        )
        await self._r.lpush(_QUEUE_KEY, job_id)
        return job_id

    async def get(self, job_id: str) -> JobStatus | None:
        data = await self._r.hgetall(self._key(job_id))
        if not data:
            return None
        return _from_hash(data)

    async def reserve(self) -> JobStatus | None:
        job_id = await self._r.rpop(_QUEUE_KEY)
        if job_id is None:
            return None
        job_id = job_id.decode() if isinstance(job_id, bytes) else job_id
        await self._r.hset(self._key(job_id), "state", JobState.RUNNING.value)
        return await self.get(job_id)

    async def complete(self, job_id: str, result: Any) -> None:
        await self._r.hset(
            self._key(job_id),
            mapping={"state": JobState.DONE.value, "result": json.dumps(result)},
        )

    async def fail(self, job_id: str, error: str) -> None:
        await self._r.hset(
            self._key(job_id), mapping={"state": JobState.FAILED.value, "error": error}
        )


def _from_hash(data: dict[Any, Any]) -> JobStatus:
    def val(key: str) -> str:
        v = data.get(key.encode()) if key.encode() in data else data.get(key)
        return v.decode() if isinstance(v, bytes) else (v or "")

    result_raw = val("result")
    return JobStatus(
        id=val("id"),
        task=val("task"),
        state=JobState(val("state")),
        params=json.loads(val("params") or "{}"),
        result=json.loads(result_raw) if result_raw else None,
        error=val("error") or None,
    )
