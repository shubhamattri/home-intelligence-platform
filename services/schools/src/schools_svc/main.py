from __future__ import annotations

from fastapi import Query

from contracts import School, SchoolShortlistRequest, SchoolShortlistResult
from platform_common.geo import Geocoder
from service_kit import create_app

from .repository import FileSchoolsRepository, PostgresSchoolsRepository, SchoolsRepository
from .settings import settings

_geocoder = Geocoder(nominatim_url=settings.nominatim_url)


def _make_repo() -> SchoolsRepository:
    if settings.database_url:
        from persistence import make_engine, make_session_factory

        sf = make_session_factory(make_engine(settings.database_url))
        return PostgresSchoolsRepository(sf)
    return FileSchoolsRepository()


app = create_app(settings.service_name, log_level=settings.log_level)
repo: SchoolsRepository = _make_repo()


@app.get("/schools", response_model=list[School], tags=["schools"])
async def list_schools(
    area: str | None = None, limit: int = Query(default=200, le=2000)
) -> list[School]:
    schools = await repo.all_schools()
    if area:
        area_l = area.lower()
        schools = [s for s in schools if s.area and area_l in s.area.lower()]
    return schools[:limit]


@app.post("/schools/shortlist", response_model=SchoolShortlistResult, tags=["schools"])
async def shortlist(req: SchoolShortlistRequest) -> SchoolShortlistResult:
    matched = await repo.shortlist(req.area, req.boards, req.min_tier)
    return SchoolShortlistResult(area=req.area, count=len(matched), schools=matched)


@app.get("/schools/search", response_model=list[School], tags=["schools"])
async def search(q: str, limit: int = Query(default=30, le=200)) -> list[School]:
    """Fuzzy name search across all Bangalore schools (typo/word-order tolerant)."""
    return await repo.search(q, limit)


@app.get("/schools/near", response_model=list[School], tags=["schools"])
async def near(
    lat: float, lon: float, radius_km: float = 5.0, limit: int = Query(default=50, le=500)
) -> list[School]:
    return await repo.near(lat, lon, radius_km, limit)


@app.get("/schools/near_area", response_model=SchoolShortlistResult, tags=["schools"])
async def near_area(
    area: str, radius_km: float = 4.0, limit: int = Query(default=60, le=500)
) -> SchoolShortlistResult:
    """Geocode an area name and return schools near it.

    The schools' stored area labels use a different taxonomy than what users type,
    so name-matching is unreliable; geocoding + radius gives real results.
    """
    loc = await _geocoder.geocode(area)
    schools = await repo.near(loc.lat, loc.lon, radius_km, limit)
    return SchoolShortlistResult(area=area, count=len(schools), schools=schools)
