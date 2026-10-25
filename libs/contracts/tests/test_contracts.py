from __future__ import annotations

import pytest
from pydantic import ValidationError

from contracts import (
    Address,
    CorridorScore,
    DecisionRequest,
    GateScoreRequest,
    LatLonModel,
)


def test_latlon_bounds_enforced() -> None:
    with pytest.raises(ValidationError):
        LatLonModel(lat=200, lon=0)


def test_gate_request_rejects_nonpositive_budget() -> None:
    with pytest.raises(ValidationError):
        GateScoreRequest(coords=LatLonModel(lat=12.935, lon=77.624), budget_cr=0)


def test_gate_request_defaults() -> None:
    req = GateScoreRequest(coords=LatLonModel(lat=12.935, lon=77.624), budget_cr=1.5)
    assert req.max_commute_min == 45.0
    assert req.min_schools == 3


def test_decision_request_accepts_query_address() -> None:
    req = DecisionRequest(address=Address(query="Koramangala"), budget_cr=1.5)
    assert req.min_hospital_quality == 0.78


def test_corridor_score_roundtrip() -> None:
    c = CorridorScore(
        corridor="North Bangalore",
        growth_heuristic=0.316,
        infra_stage_w=0.6,
        leasing="hot",
        leasing_w=1.0,
        cauvery="upcoming-stage6",
        water_w=0.5,
        water_gate_ok=True,
        current_psf=6000,
    )
    assert CorridorScore.model_validate(c.model_dump()) == c
