from __future__ import annotations

from typing import Any

import pytest

from mcp_gateway import client
from mcp_gateway.format import (
    format_corridors,
    format_hospital_quality,
    format_shortlist,
    format_verdict,
)


def test_format_verdict_buy() -> None:
    v = {
        "verdict": "buy",
        "rationale": "All gates pass.",
        "commute_min": 27,
        "hospital": {
            "nearest_quality_hospital": "Aster CMI",
            "drive_minutes": 20,
            "within_golden_hour": True,
        },
        "schools_nearby": 4,
        "failed_gates": [],
    }
    out = format_verdict(v)
    assert "Verdict: BUY" in out
    assert "Aster CMI" in out
    assert "27 min" in out


def test_format_verdict_reject_lists_gates() -> None:
    v = {
        "verdict": "reject",
        "rationale": "Rejected on: hospital>30m",
        "commute_min": None,
        "hospital": {
            "nearest_quality_hospital": None,
            "drive_minutes": None,
            "within_golden_hour": False,
        },
        "schools_nearby": 0,
        "failed_gates": ["hospital>30m", "schools<3"],
    }
    out = format_verdict(v)
    assert "Verdict: REJECT" in out
    assert "hospital>30m" in out
    assert "unknown" in out  # commute None


def test_format_corridors_flags_water_cap() -> None:
    rows = [
        {
            "corridor": "North Bangalore",
            "growth_heuristic": 0.316,
            "infra_stage_w": 0.6,
            "leasing": "hot",
            "water_w": 0.5,
            "water_gate_ok": True,
        },
        {
            "corridor": "Electronic City",
            "growth_heuristic": 0.07,
            "infra_stage_w": 1.0,
            "leasing": "steady",
            "water_w": 0.15,
            "water_gate_ok": False,
        },
    ]
    out = format_corridors(rows)
    assert "North Bangalore" in out
    assert "WATER-CAPPED" in out


def test_format_hospital_quality() -> None:
    out = format_hospital_quality(
        [{"name": "Aster CMI", "quality_score": 0.98, "accreditation": "NABH+JCI"}]
    )
    assert "Aster CMI" in out and "0.98" in out


def test_format_shortlist_empty() -> None:
    out = format_shortlist({"area": "Nowhere", "count": 0, "schools": []})
    assert "none matched" in out


@pytest.mark.asyncio
async def test_client_score_calls_decision(monkeypatch: pytest.MonkeyPatch) -> None:
    async def fake_post(self: object, url: str, **kwargs: Any) -> dict[str, Any]:
        assert url == "/dec/decision"
        return {"verdict": "buy"}

    monkeypatch.setattr("platform_common.http.ResilientClient.post_json", fake_post)
    result = await client.call_decision({"address": {"query": "Koramangala"}, "budget_cr": 1.5})
    assert result["verdict"] == "buy"


@pytest.mark.asyncio
async def test_server_registers_four_tools() -> None:
    from mcp_gateway.server import mcp

    tools = await mcp.list_tools()
    names = {t.name for t in tools}
    assert {"score_address", "growth_corridors", "hospital_quality", "school_shortlist"} <= names
