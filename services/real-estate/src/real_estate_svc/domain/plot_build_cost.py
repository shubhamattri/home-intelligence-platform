"""True all-in cost of buying a plot and building on it in Bangalore.

Plot price plus construction is the number people quote. It is not the number they
pay. This module carries the line items that actually appear, each with its basis
stated, so nothing is a silent assumption.

Sourcing honesty (read this before trusting any output):
  SOURCED   stamp duty and registration  - Karnataka schedule, 5% + 1% + ~0.6% cess
                                           above Rs 45L, charged on guidance value
                                           or consideration, whichever is higher
  SOURCED   construction per sqft        - five Bangalore contractor rate cards read
                                           26 Jul 2026 (sqft.expert, Deejos, NoBroker,
                                           99acres, JK Cement). These are VENDOR
                                           MARKETING RATES, not audited costs, and
                                           they exclude everything below.
  ESTIMATE  interiors, compound wall, borewell, utility connections, plan sanction,
            architect fees, contingency - these are assumptions from typical
            Bangalore practice. NOT sourced. Replace each with a real quote before
            relying on the total.

GST note: a single works contract to a builder attracts 18% GST on the contract
value. Engaging labour and buying material separately usually lands lower in
practice. Both are modelled via `gst_mode`.
"""

from __future__ import annotations

from dataclasses import dataclass

# SOURCED: contractor rate cards, 26 Jul 2026. Vendor marketing rates. Exclude
# interiors, fees, sanction, compound wall, borewell, connections, GST, escalation.
BUILD_PSF = {"standard": 2025, "premium": 2450, "luxury": 3100}

# Karnataka, property above Rs 45 lakh. SOURCED.
STAMP_PCT = 0.05
REG_PCT = 0.01
CESS_PCT = 0.006


@dataclass(frozen=True)
class CostLine:
    label: str
    amount: float
    basis: str  # "sourced" or "estimate"


@dataclass(frozen=True)
class PlotBuildCost:
    lines: list[CostLine]

    @property
    def total(self) -> float:
        return sum(line.amount for line in self.lines)

    @property
    def sourced_total(self) -> float:
        return sum(x.amount for x in self.lines if x.basis == "sourced")

    @property
    def estimated_total(self) -> float:
        return sum(x.amount for x in self.lines if x.basis == "estimate")


def plot_build_cost(
    plot_sqft: float,
    land_psf: float,
    builtup_sqft: float,
    grade: str = "premium",
    interiors_psf: float = 900.0,
    gst_mode: str = "self_managed",
    contingency_pct: float = 0.10,
    guidance_value: float | None = None,
) -> PlotBuildCost:
    """All-in cost of land + build. `guidance_value` overrides the land price for
    duty if the government rate is higher, which is how Karnataka actually charges."""
    if grade not in BUILD_PSF:
        raise ValueError(f"grade must be one of {sorted(BUILD_PSF)}")
    if gst_mode not in {"self_managed", "works_contract"}:
        raise ValueError("gst_mode must be 'self_managed' or 'works_contract'")

    land = plot_sqft * land_psf
    dutiable = max(land, guidance_value) if guidance_value else land
    build = builtup_sqft * BUILD_PSF[grade]

    lines = [
        CostLine("Plot price", land, "sourced"),
        CostLine("Stamp duty (5%)", dutiable * STAMP_PCT, "sourced"),
        CostLine("Registration (1%)", dutiable * REG_PCT, "sourced"),
        CostLine("Cess + surcharge (~0.6%)", dutiable * CESS_PCT, "sourced"),
        CostLine("Legal, khata transfer, documentation", 75_000, "estimate"),
        CostLine("Plan sanction + scrutiny fees", builtup_sqft * 45, "estimate"),
        CostLine("Architect + structural fees (4%)", build * 0.04, "estimate"),
        CostLine(f"Construction ({grade}, Rs {BUILD_PSF[grade]}/sqft)", build, "sourced"),
        CostLine("Compound wall + gate", 4_50_000, "estimate"),
        CostLine("Borewell + sump + overhead tank", 3_50_000, "estimate"),
        CostLine("BESCOM + water/sewage connections", 1_75_000, "estimate"),
        CostLine(
            f"Interiors + modular kitchen (Rs {interiors_psf:.0f}/sqft)",
            builtup_sqft * interiors_psf,
            "estimate",
        ),
    ]
    if gst_mode == "works_contract":
        lines.append(CostLine("GST on works contract (18%)", build * 0.18, "sourced"))

    subtotal = sum(x.amount for x in lines)
    lines.append(
        CostLine(
            f"Contingency ({contingency_pct * 100:.0f}%)", subtotal * contingency_pct, "estimate"
        )
    )
    return PlotBuildCost(lines=lines)
