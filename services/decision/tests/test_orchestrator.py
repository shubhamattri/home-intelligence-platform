from __future__ import annotations

from typing import Any

import pytest

from contracts import Address, DecisionRequest, LatLonModel
from decision_svc.orchestrator import decide
from platform_common.geo import Geocoder


class _RE:
    def __init__(self, commute: float | None) -> None:
        self._c = commute

    async def score_gate(self, payload: dict[str, Any]) -> dict[str, Any]:
        return {"commute_min": self._c, "passes": self._c is not None}


class _Hosp:
    def __init__(self, minutes: float | None) -> None:
        self._m = minutes

    async def reachability(self, payload: dict[str, Any]) -> dict[str, Any]:
        return {
            "origin": payload["origin"],
            "nearest_quality_hospital": "Aster CMI",
            "drive_minutes": self._m,
            "within_golden_hour": self._m is not None and self._m <= 60,
            "min_quality": payload["min_quality"],
        }


class _Sch:
    def __init__(self, n: int) -> None:
        self._n = n

    async def near(self, lat: float, lon: float, radius_km: float) -> list[dict[str, Any]]:
        return [{"name": f"School {i}", "board": "CBSE"} for i in range(self._n)]


def _req() -> DecisionRequest:
    return DecisionRequest(
        address=Address(coords=LatLonModel(lat=12.935, lon=77.624)), budget_cr=1.5
    )


@pytest.mark.asyncio
async def test_all_gates_pass_buys() -> None:
    v = await decide(_req(), Geocoder(), _RE(27), _Hosp(20), _Sch(4), 5.0)  # type: ignore[arg-type]
    assert v.verdict == "buy"
    assert v.passes
    assert v.schools_nearby == 4
    assert v.hospital.nearest_quality_hospital == "Aster CMI"


@pytest.mark.asyncio
async def test_hospital_gate_rejects() -> None:
    v = await decide(_req(), Geocoder(), _RE(27), _Hosp(40), _Sch(4), 5.0)  # type: ignore[arg-type]
    assert v.verdict == "reject"
    assert any("hospital" in g for g in v.failed_gates)


@pytest.mark.asyncio
async def test_school_gate_rejects() -> None:
    v = await decide(_req(), Geocoder(), _RE(27), _Hosp(20), _Sch(1), 5.0)  # type: ignore[arg-type]
    assert not v.passes
    assert any("schools" in g for g in v.failed_gates)


@pytest.mark.asyncio
async def test_commute_gate_rejects() -> None:
    v = await decide(_req(), Geocoder(), _RE(None), _Hosp(20), _Sch(4), 5.0)  # type: ignore[arg-type]
    assert not v.passes
    assert any("commute" in g for g in v.failed_gates)
