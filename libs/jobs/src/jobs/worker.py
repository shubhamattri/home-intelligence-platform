"""Worker loop: reserve a job, run its registered task, record the outcome."""

from __future__ import annotations

import asyncio
from collections.abc import Awaitable, Callable, Mapping
from typing import Any

from platform_common.logging import get_logger

from .store import JobStore

Task = Callable[[dict[str, Any]], Awaitable[Any]]
TaskRegistry = Mapping[str, Task]

log = get_logger("jobs.worker")


async def run_once(store: JobStore, tasks: TaskRegistry) -> bool:
    """Process at most one job. Returns True if a job was handled."""

    job = await store.reserve()
    if job is None:
        return False
    task = tasks.get(job.task)
    if task is None:
        await store.fail(job.id, f"unknown task: {job.task}")
        return True
    try:
        result = await task(job.params)
        await store.complete(job.id, result)
        log.info("job_done", job_id=job.id, task=job.task)
    except Exception as e:  # worker must never crash on a bad job
        await store.fail(job.id, str(e))
        log.warning("job_failed", job_id=job.id, task=job.task, error=str(e))
    return True


async def run_worker(store: JobStore, tasks: TaskRegistry, poll_interval_s: float = 1.0) -> None:
    """Continuously process jobs. Entry point for the worker container."""

    log.info("worker_started", tasks=list(tasks))
    while True:
        handled = await run_once(store, tasks)
        if not handled:
            await asyncio.sleep(poll_interval_s)
