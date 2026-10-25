"""MCP server exposing the Bangalore Home Intelligence platform to agents.

Workflow-oriented tools (not thin endpoint wrappers): one call answers a real
question a family asks. All tools are read-only and return concise Markdown.
"""

from __future__ import annotations

from mcp.server.fastmcp import FastMCP
from mcp.types import ToolAnnotations

from . import client
from .format import (
    format_corridors,
    format_hospital_quality,
    format_shortlist,
    format_verdict,
)

mcp = FastMCP("bangalore-home-intelligence")

# All tools here read live data from downstream services; none mutate state.
_READONLY = ToolAnnotations(readOnlyHint=True, openWorldHint=True)


@mcp.tool(annotations=_READONLY)
async def score_address(
    address: str,
    budget_cr: float,
    max_commute_min: float = 45.0,
    max_hospital_min: float = 30.0,
    min_schools: int = 3,
    depart_at: str | None = None,
) -> str:
    """Score a Bangalore address for a family home purchase and return a buy/reject verdict.

    Composes three hard gates from the live services: peak-traffic commute to the job
    hub, golden-hour reachability to a quality hospital, and school availability nearby.
    Any gate failing => reject.

    Args:
        address: Free-text locality or address, e.g. "Koramangala" or "HSR Layout Sector 2".
        budget_cr: Budget in crores INR (e.g. 1.5).
        max_commute_min: Max acceptable peak commute in minutes (default 45).
        max_hospital_min: Max acceptable drive to a quality hospital (default 30).
        min_schools: Minimum schools required within radius (default 3).
        depart_at: Optional ISO8601 departure time for peak traffic, e.g. "2026-07-27T09:00:00".

    Returns a Markdown verdict with the per-gate breakdown. If commute shows "unknown",
    the platform has no TomTom key configured.
    """
    payload = {
        "address": {"query": address},
        "budget_cr": budget_cr,
        "max_commute_min": max_commute_min,
        "max_hospital_min": max_hospital_min,
        "min_schools": min_schools,
        "depart_at": depart_at,
    }
    return format_verdict(await client.call_decision(payload))


@mcp.tool(annotations=_READONLY)
async def growth_corridors() -> str:
    """List Bangalore's emerging growth corridors, ranked by a gated heuristic.

    The score multiplies infrastructure stage, commercial-leasing momentum (the jobs
    signal), and Cauvery water stage. Water below a threshold hard-caps the score.
    This is a transparent heuristic, not a trained predictor.
    """
    return format_corridors(await client.get_corridors())


@mcp.tool(annotations=_READONLY)
async def hospital_quality() -> str:
    """List Bangalore hospitals ranked by clinical quality.

    Quality is derived from accreditation plus aspect-based review sentiment, NOT raw
    Google stars (a 3.9-star hospital dragged down by billing complaints is not the
    same as a clinically weak one).
    """
    return format_hospital_quality(await client.get_hospital_quality())


@mcp.tool(annotations=_READONLY)
async def school_shortlist(
    area: str, boards: list[str] | None = None, min_tier: int | None = None
) -> str:
    """Shortlist schools in an area, optionally filtered by board and minimum tier.

    Args:
        area: Locality name, e.g. "HSR", "Koramangala".
        boards: Optional board filter, e.g. ["CBSE", "ICSE"].
        min_tier: Optional minimum tier (1 = best); returns schools at or above it.
    """
    payload: dict[str, object] = {"area": area, "boards": boards, "min_tier": min_tier}
    return format_shortlist(await client.post_school_shortlist(payload))


def main() -> None:
    mcp.run()


if __name__ == "__main__":
    main()
