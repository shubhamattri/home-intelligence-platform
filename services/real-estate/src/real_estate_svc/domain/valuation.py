"""Estimate what a specific home is actually worth, instead of trusting portal asks.

Portal listings mix builder base price, resale asking and computed averages, so
they are unreliable. Two independent estimators are more defensible:

1. Indexed anchor: take a price that is known to be real at some past year and
   compound it forward at the corridor's own CAGR.
2. Land + construction: for an independent house, value the land at the local plot rate and
   the structure at Bangalore build cost, then add furnishing.

Where an asking price sits against these tells you the premium you are paying
for the gated community, the brand and the convenience.
"""

from __future__ import annotations

from dataclasses import dataclass

# Bangalore build cost per sqft, 2026 (excludes plan sanction, compound wall, borewell).
BUILD_COST = {"standard": (1850, 2200), "premium": (2200, 2700), "luxury": (2700, 3500)}


@dataclass(frozen=True)
class Valuation:
    asking: float
    land_value: float
    build_value: float
    furnishing: float
    component_fair: float
    corridor_value: float | None
    premium_pct: float
    premium_over_corridor_pct: float | None

    @property
    def verdict(self) -> str:
        p = self.premium_pct
        if p < 25:
            return "at or below fair build-up value"
        if p < 50:
            return "normal gated-project premium"
        if p < 80:
            return "rich premium"
        return "very rich premium"


def index_forward(anchor_price: float, anchor_year: int, cagr_pct: float, to_year: int) -> float:
    """Compound a known past price forward at the corridor's CAGR."""
    years = to_year - anchor_year
    if years < 0:
        raise ValueError("to_year must be >= anchor_year")
    return float(anchor_price * (1 + cagr_pct / 100) ** years)


def implied_cagr(psf_then: float, psf_now: float, years: int) -> float:
    """Back out the CAGR a corridor actually delivered."""
    if years <= 0 or psf_then <= 0:
        raise ValueError("years and psf_then must be positive")
    return float(((psf_now / psf_then) ** (1 / years) - 1) * 100)


def value_independent_house(
    asking: float,
    plot_sqft: float,
    land_psf: float,
    builtup_sqft: float,
    grade: str = "premium",
    furnishing: float = 0.0,
    corridor_psf: float | None = None,
) -> Valuation:
    """Value an independent house bottom-up as land + structure + furnishing, vs the asking price."""
    lo, hi = BUILD_COST[grade]
    land = plot_sqft * land_psf
    build = builtup_sqft * (lo + hi) / 2
    fair = land + build + furnishing
    corridor = builtup_sqft * corridor_psf if corridor_psf else None
    return Valuation(
        asking=asking,
        land_value=land,
        build_value=build,
        furnishing=furnishing,
        component_fair=fair,
        corridor_value=corridor,
        premium_pct=(asking / fair - 1) * 100 if fair else 0.0,
        premium_over_corridor_pct=((asking / corridor - 1) * 100 if corridor else None),
    )
