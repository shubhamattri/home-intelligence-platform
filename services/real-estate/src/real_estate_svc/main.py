from __future__ import annotations

import asyncio
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI, Query

from contracts import CorridorScore, GateResult, GateScoreRequest, Project
from jobs import build_jobs_router, make_store, run_worker
from platform_common.config import resolve_secret
from platform_common.geo import LatLon, TomTomRouter
from service_kit import create_app

from .domain.corridor import score_corridors
from .domain.gate import score_gate
from .repository import (
    FileRealEstateRepository,
    PostgresRealEstateRepository,
    RealEstateRepository,
)
from .settings import settings
from .tasks import TASKS


def _make_repo() -> RealEstateRepository:
    if settings.database_url:
        from persistence import make_engine, make_session_factory

        sf = make_session_factory(make_engine(settings.database_url))
        return PostgresRealEstateRepository(sf)
    return FileRealEstateRepository()


repo: RealEstateRepository = _make_repo()
_store = make_store(settings.redis_url)


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncIterator[None]:
    # Convenience for local/in-memory dev; in compose/k8s a separate worker runs.
    worker: asyncio.Task[None] | None = None
    if settings.jobs_inprocess_worker:
        worker = asyncio.create_task(run_worker(_store, TASKS))
    yield
    if worker is not None:
        worker.cancel()


app = create_app(settings.service_name, log_level=settings.log_level, lifespan=lifespan)
app.include_router(build_jobs_router(_store, TASKS))


def _router() -> TomTomRouter | None:
    key = resolve_secret(settings.tomtom_api_key, settings.data_dir / ".tomtom_key")
    return TomTomRouter(key, base_url=settings.tomtom_base_url) if key else None


@app.get("/projects", response_model=list[Project], tags=["real-estate"])
async def list_projects(
    q: str | None = None,
    exclude_distressed: bool = False,
    area: str | None = None,
    limit: int = Query(default=100, le=1000),
    offset: int = Query(default=0, ge=0),
) -> list[Project]:
    return await repo.list_projects(
        limit=limit, q=q, exclude_distressed=exclude_distressed, offset=offset, area=area
    )


@app.get("/corridors", response_model=list[CorridorScore], tags=["real-estate"])
async def corridors() -> list[CorridorScore]:
    return score_corridors(await repo.emerging_corridors(), await repo.leasing_water())


@app.get("/appreciation", tags=["real-estate"])
async def appreciation() -> dict[str, object]:
    """Historical proven corridors (psf then vs now, multiples) + emerging with CAGR."""
    return await repo.appreciation()


@app.post("/score/gates", response_model=GateResult, tags=["real-estate"])
async def score_gates(req: GateScoreRequest) -> GateResult:
    hub = LatLon(settings.job_hub_lat, settings.job_hub_lon)
    return await score_gate(req, _router(), hub)
