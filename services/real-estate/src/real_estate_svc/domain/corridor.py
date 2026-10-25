"""Growth-corridor heuristic. Ported verbatim from the original growth_corridor.py.

Multiplicative + gated: water < 0.2 is a hard cap, infra weighted by stage,
leasing (jobs signal) weighted highest, cheap price kept OUT of the score.
Honest label: a gated heuristic, not a trained predictor.
"""

from __future__ import annotations

from typing import Any

from contracts import CorridorScore

STAGE_W = {
    "operational": 1.0,
    "uc": 0.6,
    "under-construction": 0.6,
    "land-acquired": 0.2,
    "tender": 0.2,
    "announced": 0.05,
    "dpr": 0.05,
}
LEASE_W = {"hot": 1.0, "steady": 0.5, "cooling": 0.15, "none": 0.1}


def stage_w(s: str | None) -> float:
    s = (s or "").lower()
    for k, v in STAGE_W.items():
        if k in s:
            return v
    return 0.05


def water_w(s: str | None) -> float:
    s = (s or "").lower()
    if "connected" in s or ("cauvery" in s and "upcoming" not in s):
        return 1.0
    if "upcoming" in s or "stage" in s:
        return 0.5
    return 0.15


def lease_w(s: str | None) -> float:
    return LEASE_W.get((s or "").lower(), 0.3)


def score_corridors(
    emerging: list[dict[str, Any]], leasing_water: dict[str, Any]
) -> list[CorridorScore]:
    leasing = {x["submarket"].lower(): x for x in leasing_water.get("leasing", [])}
    water = {x["area"].lower(): x for x in leasing_water.get("water", [])}

    def match(d: dict[str, Any], name: str) -> dict[str, Any]:
        n = name.lower()
        for k, v in d.items():
            if k and (k in n or n.split()[0] in k):
                return v  # type: ignore[no-any-return]
        return {}

    rows: list[CorridorScore] = []
    for c in emerging:
        name = c["corridor"]
        infra = (
            stage_w(c.get("infra_status"))
            if c.get("infra_status")
            else max([stage_w(s) for s in c.get("leading_indicators", [])] or [0.05])
        )
        lm = match(leasing, name)
        wm = match(water, name)
        lease_src = c.get("leasing_momentum") or (lm.get("leasing_momentum") if lm else None)
        water_src = c.get("cauvery_status") or (wm.get("cauvery_status") if wm else None)
        lease = lease_w(lease_src) if lease_src else 0.3
        wat = water_w(water_src) if water_src else 0.4
        core = (infra**0.9) * (lease**1.1) * (wat**1.0)  # leasing weighted highest
        rows.append(
            CorridorScore(
                corridor=name,
                growth_heuristic=round(core, 3),
                infra_stage_w=round(infra, 2),
                leasing=lease_src or "?",
                leasing_w=round(lease, 2),
                cauvery=water_src or "?",
                water_w=round(wat, 2),
                water_gate_ok=wat >= 0.2,
                current_psf=c.get("current_psf"),
                cagr_pct=c.get("cagr_pct"),
                thesis=c.get("appreciation_note") or c.get("growth_thesis"),
            )
        )
    rows.sort(key=lambda r: -r.growth_heuristic)
    return rows
