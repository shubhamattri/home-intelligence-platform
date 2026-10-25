from __future__ import annotations

from typing import Any

import pytest

from jobs import InMemoryJobStore, JobState, run_once


async def _echo(params: dict[str, Any]) -> dict[str, Any]:
    return {"echoed": params}


async def _boom(params: dict[str, Any]) -> None:
    raise RuntimeError("kaboom")


@pytest.mark.asyncio
async def test_enqueue_and_complete() -> None:
    store = InMemoryJobStore()
    tasks = {"echo": _echo}
    job_id = await store.enqueue("echo", {"x": 1})

    assert (await store.get(job_id)).state == JobState.QUEUED  # type: ignore[union-attr]
    handled = await run_once(store, tasks)
    assert handled

    done = await store.get(job_id)
    assert done is not None
    assert done.state == JobState.DONE
    assert done.result == {"echoed": {"x": 1}}


@pytest.mark.asyncio
async def test_failing_task_records_error() -> None:
    store = InMemoryJobStore()
    job_id = await store.enqueue("boom", {})
    await run_once(store, {"boom": _boom})
    job = await store.get(job_id)
    assert job is not None
    assert job.state == JobState.FAILED
    assert "kaboom" in (job.error or "")


@pytest.mark.asyncio
async def test_unknown_task_fails_gracefully() -> None:
    store = InMemoryJobStore()
    job_id = await store.enqueue("nope", {})
    await run_once(store, {})
    job = await store.get(job_id)
    assert job is not None
    assert job.state == JobState.FAILED


@pytest.mark.asyncio
async def test_run_once_empty_queue() -> None:
    store = InMemoryJobStore()
    assert await run_once(store, {}) is False
