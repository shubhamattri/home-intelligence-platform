from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from contracts import GateScoreRequest, LatLonModel
from platform_common.geo import LatLon
from real_estate_svc.domain.gate import score_gate
from real_estate_svc.main import app

client = TestClient(app)


def test_health() -> None:
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json()["service"] == "real-estate-svc"


def test_corridors_ranks_north_bangalore_top() -> None:
    r = client.get("/corridors")
    assert r.status_code == 200
    rows = r.json()
    assert len(rows) >= 5
    # North Bangalore / Devanahalli lead; Sarjapur East is capped at the bottom
    assert "North Bangalore" in rows[0]["corridor"] or "Devanahalli" in rows[0]["corridor"]
    assert rows[0]["growth_heuristic"] >= rows[-1]["growth_heuristic"]


def test_corridors_water_cap_flagged() -> None:
    rows = client.get("/corridors").json()
    capped = [r for r in rows if not r["water_gate_ok"]]
    assert any("Electronic City" in r["corridor"] for r in capped)


def test_projects_limit() -> None:
    r = client.get("/projects?limit=5")
    assert r.status_code == 200
    assert len(r.json()) == 5


def test_gate_no_router_marks_commute_unknown() -> None:
    r = client.post(
        "/score/gates", json={"coords": {"lat": 12.935, "lon": 77.624}, "budget_cr": 1.5}
    )
    body = r.json()
    assert body["passes"] is False
    assert any("commute_unknown" in g for g in body["failed_gates"])


class _FakeRouter:
    async def drive_minutes(
        self, origin: LatLon, dest: LatLon, depart_at: str | None = None
    ) -> float:
        return 27.0


@pytest.mark.asyncio
async def test_gate_passes_within_commute() -> None:
    req = GateScoreRequest(
        coords=LatLonModel(lat=12.935, lon=77.624), budget_cr=1.5, max_commute_min=45
    )
    result = await score_gate(req, _FakeRouter(), LatLon(12.956, 77.701))  # type: ignore[arg-type]
    assert result.passes
    assert result.commute_min == 27.0
