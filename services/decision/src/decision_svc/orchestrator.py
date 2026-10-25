"""Compose the three domain services into a single gate-based verdict.

The verdict is built from live downstream responses, never from local files:
commute (real-estate), golden-hour hospital reachability (hospitals), and school
count near the point (schools). Gates are hard: any failure => reject.
"""

from __future__ import annotations

import asyncio
from typing import Protocol

from contracts import (
    Address,
    DecisionRequest,
    DecisionVerdict,
    LatLonModel,
    ReachabilityResult,
    School,
)
from platform_common.errors import ValidationError
from platform_common.geo import LatLon

from .clients import HospitalsClient, RealEstateClient, SchoolsClient


class SupportsGeocode(Protocol):
    async def geocode(self, query: str, region: str = ...) -> LatLon: ...


async def _resolve(address: Address, geocoder: SupportsGeocode) -> LatLonModel:
    if address.coords is not None:
        return address.coords
    if address.query:
        loc = await geocoder.geocode(address.query)
        return LatLonModel(lat=loc.lat, lon=loc.lon)
    raise ValidationError("address must have either coords or query")


async def decide(
    req: DecisionRequest,
    geocoder: SupportsGeocode,
    real_estate: RealEstateClient,
    hospitals: HospitalsClient,
    schools: SchoolsClient,
    school_radius_km: float,
) -> DecisionVerdict:
    coords = await _resolve(req.address, geocoder)

    gate_payload = {
        "coords": coords.model_dump(),
        "budget_cr": req.budget_cr,
        "depart_at": req.depart_at,
        "max_commute_min": req.max_commute_min,
    }
    reach_payload = {
        "origin": coords.model_dump(),
        "depart_at": req.depart_at,
        "min_quality": req.min_hospital_quality,
    }

    gate_raw, reach_raw, near_raw = await asyncio.gather(
        real_estate.score_gate(gate_payload),
        hospitals.reachability(reach_payload),
        schools.near(coords.lat, coords.lon, school_radius_km),
    )

    hospital = ReachabilityResult.model_validate(reach_raw)
    sample = [School.model_validate(s) for s in near_raw]
    commute_min = gate_raw.get("commute_min")

    failed: list[str] = []
    if commute_min is None or commute_min > req.max_commute_min:
        failed.append(f"commute>{req.max_commute_min:.0f}m")
    if hospital.drive_minutes is None or hospital.drive_minutes > req.max_hospital_min:
        failed.append(f"hospital>{req.max_hospital_min:.0f}m")
    if len(sample) < req.min_schools:
        failed.append(f"schools<{req.min_schools}")

    passes = not failed
    rationale = (
        "All gates pass: reachable jobs, a quality hospital within the golden window, "
        "and enough schools nearby."
        if passes
        else "Rejected on: " + ", ".join(failed)
    )

    return DecisionVerdict(
        address=req.address,
        verdict="buy" if passes else "reject",
        passes=passes,
        commute_min=commute_min,
        hospital=hospital,
        schools_nearby=len(sample),
        sample_schools=sample[:5],
        failed_gates=failed,
        rationale=rationale,
    )
