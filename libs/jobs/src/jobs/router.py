"""FastAPI router exposing the async job pattern: submit -> 202 + id, then poll."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse

from .models import JobStatus
from .store import JobStore
from .worker import TaskRegistry


def build_jobs_router(store: JobStore, tasks: TaskRegistry) -> APIRouter:
    router = APIRouter(tags=["jobs"])

    @router.post("/jobs/{task}", status_code=202)
    async def submit(task: str, params: dict[str, Any] | None = None) -> JSONResponse:
        if task not in tasks:
            raise HTTPException(status_code=404, detail=f"unknown task: {task}")
        job_id = await store.enqueue(task, params or {})
        return JSONResponse(status_code=202, content={"job_id": job_id, "task": task})

    @router.get("/jobs/{job_id}", response_model=JobStatus)
    async def status(job_id: str) -> JobStatus:
        job = await store.get(job_id)
        if job is None:
            raise HTTPException(status_code=404, detail="job not found")
        return job

    return router
