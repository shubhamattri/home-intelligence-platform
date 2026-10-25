"""Async job pattern end-to-end through the real-estate service (in-memory store)."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from jobs import run_once
from real_estate_svc.main import _store, app
from real_estate_svc.tasks import TASKS

client = TestClient(app)


def test_submit_unknown_task_404() -> None:
    assert client.post("/jobs/does_not_exist").status_code == 404


@pytest.mark.asyncio
async def test_submit_poll_complete() -> None:
    # submit returns 202 + job_id, job starts queued
    resp = client.post("/jobs/rescore_corridors", json={})
    assert resp.status_code == 202
    job_id = resp.json()["job_id"]

    assert client.get(f"/jobs/{job_id}").json()["state"] == "queued"

    # a worker processes it
    await run_once(_store, TASKS)

    done = client.get(f"/jobs/{job_id}").json()
    assert done["state"] == "done"
    assert done["result"]["count"] >= 5  # the emerging corridors


def test_poll_missing_job_404() -> None:
    assert client.get("/jobs/deadbeef").status_code == 404
