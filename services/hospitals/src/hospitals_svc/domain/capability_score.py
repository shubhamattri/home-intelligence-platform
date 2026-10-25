"""Score hospitals by what they can actually DO, not by how pleasant they are.

The previous quality_score blended accreditation with cleanliness, billing friction
and star ratings. That ranked Sri Jayadeva LAST of twelve, when it is India's leading
dedicated cardiac institute with 1,150 beds and a 24x7 cath lab. It scored badly
because a high-volume public institute has queues and poor reviews.

Reviews measure the billing counter. They do not measure whether someone opens your
artery at 2am. So this module scores three different questions separately, because a
hospital that is right for one is often wrong for another:

  cardiac_emergency - can they do primary angioplasty tonight?
  general_emergency - trauma, stroke, the things that are not your heart
  elective          - planned care, where comfort and cost legitimately matter

Bed count is used only as a weak volume proxy. Cardiac outcome literature consistently
links procedure volume to survival, and beds is the only volume signal in the dataset.
It is NOT a quality measure on its own.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

# Weights sum to 1.0 within each score.
CARDIAC_W = {
    "cath_lab_24x7": 0.40,  # the single thing that decides a STEMI outcome
    "cardiac_surgery": 0.25,  # valve work, CABG, and the backstop if PCI fails
    "nabh_or_jci_accredited": 0.10,
    "blood_bank": 0.10,
    "volume": 0.15,  # beds as a proxy for procedure volume
}
GENERAL_W = {
    "trauma_emergency_24x7": 0.35,
    "stroke_ready": 0.25,
    "blood_bank": 0.15,
    "nabh_or_jci_accredited": 0.10,
    "volume": 0.15,
}
VOLUME_FULL_CREDIT_BEDS = 600  # beyond this, extra beds add nothing to the proxy


@dataclass(frozen=True)
class CapabilityScore:
    hospital: str
    cardiac_emergency: float
    general_emergency: float
    elective: float | None
    unknowns: list[str]

    @property
    def cardiac_verdict(self) -> str:
        if self.cardiac_emergency >= 0.85:
            return "primary cardiac destination"
        if self.cardiac_emergency >= 0.65:
            return "capable, viable first stop"
        if self.cardiac_emergency >= 0.40:
            return "stabilise and transfer"
        return "not a cardiac destination"


def _volume(beds: Any) -> float:
    try:
        b = float(beds)
    except (TypeError, ValueError):
        return 0.0
    return min(b / VOLUME_FULL_CREDIT_BEDS, 1.0)


def _weighted(
    caps: dict[str, Any], beds: Any, weights: dict[str, float]
) -> tuple[float, list[str]]:
    """Score against weights. An unknown capability scores zero and is reported,
    never silently treated as present."""
    total = 0.0
    unknown: list[str] = []
    for key, w in weights.items():
        if key == "volume":
            total += w * _volume(beds)
            continue
        v = caps.get(key)
        if v is None:
            unknown.append(key)
        elif v:
            total += w
    return round(total, 3), unknown


def score_hospital(
    name: str,
    capabilities: dict[str, Any] | None,
    beds: Any = None,
    elective_score: float | None = None,
) -> CapabilityScore:
    caps = capabilities or {}
    cardiac, u1 = _weighted(caps, beds, CARDIAC_W)
    general, u2 = _weighted(caps, beds, GENERAL_W)
    return CapabilityScore(
        hospital=name,
        cardiac_emergency=cardiac,
        general_emergency=general,
        elective=elective_score,
        unknowns=sorted(set(u1) | set(u2)),
    )
