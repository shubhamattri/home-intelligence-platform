"""End-to-end integration WITHOUT Docker.

Runs the decision orchestrator against the REAL domain services and their real
seed data, wiring the downstream clients to each app's ASGI TestClient. Proves
that a verdict is composed from live downstream responses, not local files.
"""

from __future__ import annotations

from typing import Any

import pytest
from fastapi.testclient import TestClient

from contracts import Address, DecisionRequest, LatLonModel
from decision_svc.orchestrator import decide
from hospitals_svc.main import app as hospitals_app
from platform_common.geo import Geocoder
from real_estate_svc.main import app as real_estate_app
from schools_svc.main import app as schools_app

_re = TestClient(real_estate_app)
_hosp = TestClient(hospitals_app)
_sch = TestClient(schools_app)


class RealEstateViaAsgi:
    async def score_gate(self, payload: dict[str, Any]) -> dict[str, Any]:
        return _re.post("/score/gates", json=payload).json()  # type: ignore[no-any-return]


class HospitalsViaAsgi:
    async def reachability(self, payload: dict[str, Any]) -> dict[str, Any]:
        return _hosp.post("/reachability", json=payload).json()  # type: ignore[no-any-return]


class SchoolsViaAsgi:
    async def near(self, lat: float, lon: float, radius_km: float) -> list[dict[str, Any]]:
        return _sch.get(
            "/schools/near", params={"lat": lat, "lon": lon, "radius_km": radius_km, "limit": 50}
        ).json()  # type: ignore[no-any-return]


@pytest.mark.asyncio
async def test_verdict_composed_from_real_services() -> None:
    # Koramangala coordinates; skip geocode by passing coords.
    req = DecisionRequest(
        address=Address(coords=LatLonModel(lat=12.935, lon=77.624)),
        budget_cr=1.5,
        min_hospital_quality=0.5,
    )
    verdict = await decide(
        req,
        Geocoder(),
        RealEstateViaAsgi(),  # type: ignore[arg-type]
        HospitalsViaAsgi(),  # type: ignore[arg-type]
        SchoolsViaAsgi(),  # type: ignore[arg-type]
        school_radius_km=5.0,
    )

    # Real hospital data flowed through: a nearest quality hospital was found.
    assert verdict.hospital.nearest_quality_hospital is not None
    # Real schools data flowed through: Koramangala has schools within 5km.
    assert verdict.schools_nearby > 0
    # No TomTom key in test env => commute is unknown => that gate fails.
    assert "commute" in " ".join(verdict.failed_gates)
    assert verdict.verdict == "reject"
