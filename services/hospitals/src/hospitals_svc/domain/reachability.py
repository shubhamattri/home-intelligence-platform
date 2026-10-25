"""Golden-hour reachability: real drive time to the nearest quality hospital.

Picks the 3 nearest quality hospitals by haversine (cheap) then asks TomTom for
real peak-traffic drive time to each, returning the minimum. This bounds the
number of paid routing calls per request.
"""

from __future__ import annotations

from contracts import LatLonModel, ReachabilityRequest, ReachabilityResult
from platform_common.geo import LatLon, TomTomRouter, haversine_km

from ..repository import QualityHospital


def _coords(h: QualityHospital) -> LatLonModel:
    return LatLonModel(lat=h.lat, lon=h.lon)


async def reachability(
    req: ReachabilityRequest,
    hospitals: list[QualityHospital],
    router: TomTomRouter | None,
    golden_hour_minutes: float,
) -> ReachabilityResult:
    origin = LatLon(req.origin.lat, req.origin.lon)
    if not hospitals:
        return ReachabilityResult(
            origin=req.origin,
            nearest_quality_hospital=None,
            drive_minutes=None,
            within_golden_hour=False,
            min_quality=req.min_quality,
        )

    nearest = sorted(hospitals, key=lambda h: haversine_km(origin.lat, origin.lon, h.lat, h.lon))[
        :3
    ]

    if router is None:
        # No routing key: report the haversine-nearest, but drive time is unknown.
        top = nearest[0]
        return ReachabilityResult(
            origin=req.origin,
            nearest_quality_hospital=top.name,
            nearest_coords=_coords(top),
            drive_minutes=None,
            within_golden_hour=False,
            min_quality=req.min_quality,
        )

    best: QualityHospital | None = None
    best_min: float | None = None
    for h in nearest:
        minutes = await router.drive_minutes(origin, LatLon(h.lat, h.lon), depart_at=req.depart_at)
        if best_min is None or minutes < best_min:
            best_min, best = minutes, h

    return ReachabilityResult(
        origin=req.origin,
        nearest_quality_hospital=best.name if best else None,
        nearest_coords=_coords(best) if best else None,
        drive_minutes=best_min,
        within_golden_hour=(best_min is not None and best_min <= golden_hour_minutes),
        min_quality=req.min_quality,
    )
