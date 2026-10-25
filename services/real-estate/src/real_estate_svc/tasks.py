"""Async tasks runnable via the job queue (long or rate-limited work)."""

from __future__ import annotations

from typing import Any

from platform_common.geo import Geocoder

from .domain.corridor import score_corridors
from .repository import FileRealEstateRepository


async def rescore_corridors(params: dict[str, Any]) -> dict[str, Any]:
    """Recompute the growth-corridor heuristic. Fast, no network."""
    repo = FileRealEstateRepository()
    scores = score_corridors(await repo.emerging_corridors(), await repo.leasing_water())
    return {"count": len(scores), "top": scores[0].corridor if scores else None}


async def geocode_projects(params: dict[str, Any]) -> dict[str, Any]:
    """Geocode a batch of project names via Nominatim (rate-limited => a job)."""
    names: list[str] = params.get("names", [])
    geocoder = Geocoder()
    out: list[dict[str, Any]] = []
    for name in names:
        try:
            loc = await geocoder.geocode(name)
            out.append({"name": name, "lat": loc.lat, "lon": loc.lon})
        except Exception as e:  # record per-item failure, keep going
            out.append({"name": name, "error": str(e)})
    return {"geocoded": out}


TASKS = {
    "rescore_corridors": rescore_corridors,
    "geocode_projects": geocode_projects,
}
