from __future__ import annotations

from enum import StrEnum
from typing import Any

from pydantic import BaseModel


class JobState(StrEnum):
    QUEUED = "queued"
    RUNNING = "running"
    DONE = "done"
    FAILED = "failed"


class JobStatus(BaseModel):
    id: str
    task: str
    state: JobState
    params: dict[str, Any] = {}
    result: Any | None = None
    error: str | None = None
