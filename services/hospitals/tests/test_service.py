from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from contracts import LatLonModel, ReachabilityRequest
from hospitals_svc.domain.reachability import reachability
from hospitals_svc.main import app
from hospitals_svc.repository import QualityHospital
from platform_common.geo import LatLon

client = TestClient(app)


def test_health() -> None:
    assert client.get("/health").json()["service"] == "hospitals-svc"


def test_quality_sorted_desc() -> None:
    r = client.get("/hospitals/quality")
    assert r.status_code == 200
    rows = r.json()
    assert len(rows) >= 5
    scores = [x["quality_score"] for x in rows]
    assert scores == sorted(scores, reverse=True)


def test_reachability_no_router_returns_nearest_only() -> None:
    r = client.post("/reachability", json={"origin": {"lat": 12.93, "lon": 77.62}})
    body = r.json()
    assert body["nearest_quality_hospital"] is not None
    assert body["drive_minutes"] is None
    assert body["within_golden_hour"] is False


class _FakeRouter:
    async def drive_minutes(
        self, origin: LatLon, dest: LatLon, depart_at: str | None = None
    ) -> float:
        return 18.0


@pytest.mark.asyncio
async def test_reachability_with_router_picks_min() -> None:
    hosp = [
        QualityHospital("Aster CMI", 13.05, 77.59, 0.98),
        QualityHospital("Narayana", 12.91, 77.64, 0.85),
    ]
    req = ReachabilityRequest(origin=LatLonModel(lat=12.93, lon=77.62))
    result = await reachability(req, hosp, _FakeRouter(), golden_hour_minutes=60)  # type: ignore[arg-type]
    assert result.drive_minutes == 18.0
    assert result.within_golden_hour is True


@pytest.mark.asyncio
async def test_reachability_empty_set() -> None:
    req = ReachabilityRequest(origin=LatLonModel(lat=12.93, lon=77.62), min_quality=0.99)
    result = await reachability(req, [], None, golden_hour_minutes=60)
    assert result.nearest_quality_hospital is None
    assert result.within_golden_hour is False
