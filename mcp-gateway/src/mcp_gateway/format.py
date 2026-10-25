"""Pure formatters: turn service JSON into concise, human-readable Markdown.

Kept separate from the tools so they can be unit-tested without a running server.
"""

from __future__ import annotations

from typing import Any


def format_verdict(v: dict[str, Any]) -> str:
    verdict = v.get("verdict", "?").upper()
    hosp = v.get("hospital", {})
    lines = [
        f"**Verdict: {verdict}**  ({v.get('rationale', '')})",
        "",
        f"- Commute to jobs: {_min(v.get('commute_min'))}",
        f"- Nearest quality hospital: {hosp.get('nearest_quality_hospital') or 'none found'}"
        f" ({_min(hosp.get('drive_minutes'))}, golden-hour: {hosp.get('within_golden_hour')})",
        f"- Schools within radius: {v.get('schools_nearby', 0)}",
    ]
    if v.get("failed_gates"):
        lines.append(f"- Failed gates: {', '.join(v['failed_gates'])}")
    return "\n".join(lines)


def format_corridors(rows: list[dict[str, Any]]) -> str:
    if not rows:
        return "No corridor data available."
    out = ["**Emerging growth corridors (heuristic, not a trained predictor):**", ""]
    for r in rows:
        cap = "" if r.get("water_gate_ok", True) else "  [WATER-CAPPED]"
        out.append(
            f"- {r['corridor']}: score {r['growth_heuristic']} "
            f"(infra {r['infra_stage_w']}, leasing {r['leasing']}, water {r['water_w']}){cap}"
        )
    return "\n".join(out)


def format_hospital_quality(rows: list[dict[str, Any]]) -> str:
    if not rows:
        return "No hospital quality data available."
    out = ["**Hospital quality (accreditation + sentiment, not raw stars):**", ""]
    for r in rows:
        out.append(
            f"- {r['name']}: {r['quality_score']} ({r.get('accreditation') or 'unaccredited'})"
        )
    return "\n".join(out)


def format_shortlist(res: dict[str, Any]) -> str:
    schools = res.get("schools", [])
    header = f"**{res.get('count', 0)} schools in {res.get('area', '?')}:**"
    if not schools:
        return header + "\n\n(none matched)"
    lines = [header, ""]
    for s in schools[:25]:
        lines.append(f"- {s['name']} ({s.get('board') or '?'}, tier {s.get('tier') or '?'})")
    return "\n".join(lines)


def _min(value: Any) -> str:
    return f"{value:.0f} min" if isinstance(value, int | float) else "unknown"
