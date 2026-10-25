from __future__ import annotations

from contracts import QualityScore, ReachabilityRequest, ReachabilityResult
from platform_common.config import resolve_secret
from platform_common.geo import TomTomRouter
from service_kit import create_app

from .domain.reachability import reachability
from .repository import FileHospitalsRepository, HospitalsRepository
from .settings import settings

app = create_app(settings.service_name, log_level=settings.log_level)
repo: HospitalsRepository = FileHospitalsRepository()


def _router() -> TomTomRouter | None:
    key = resolve_secret(settings.tomtom_api_key, settings.data_dir / ".tomtom_key")
    return TomTomRouter(key, base_url=settings.tomtom_base_url) if key else None


@app.get("/hospitals/quality", response_model=list[QualityScore], tags=["hospitals"])
async def quality() -> list[QualityScore]:
    return sorted(repo.quality_scores(), key=lambda q: -q.quality_score)


@app.post("/reachability", response_model=ReachabilityResult, tags=["hospitals"])
async def reach(req: ReachabilityRequest) -> ReachabilityResult:
    hospitals = repo.quality_hospitals(req.min_quality)
    return await reachability(req, hospitals, _router(), settings.golden_hour_minutes)
