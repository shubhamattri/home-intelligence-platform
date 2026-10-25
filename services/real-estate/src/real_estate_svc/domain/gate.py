"""Real-estate intrinsic gate: peak-traffic commute to the job hub.

Hospital and school gates are owned by their services and composed by
decision-svc; this service only judges the real-estate dimensions.
"""

from __future__ import annotations

from contracts import GateResult, GateScoreRequest
from platform_common.geo import LatLon, TomTomRouter


async def score_gate(
    req: GateScoreRequest, router: TomTomRouter | None, job_hub: LatLon
) -> GateResult:
    origin = LatLon(req.coords.lat, req.coords.lon)
    failed: list[str] = []
    commute: float | None = None

    if router is None:
        failed.append("commute_unknown_no_router")
    else:
        commute = await router.drive_minutes(origin, job_hub, depart_at=req.depart_at)
        if commute > req.max_commute_min:
            failed.append(f"commute>{req.max_commute_min:.0f}m")

    return GateResult(
        coords=req.coords,
        passes=not failed,
        commute_min=commute,
        failed_gates=failed,
    )
