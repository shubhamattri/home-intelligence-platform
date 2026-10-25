"""Shared API contracts for the Bangalore Home Intelligence platform."""

from __future__ import annotations

from .common import Address, AreaOption, HealthStatus, LatLonModel
from .decision import DecisionRequest, DecisionVerdict
from .hospitals import (
    Hospital,
    QualityScore,
    ReachabilityRequest,
    ReachabilityResult,
)
from .real_estate import AreaScore, CorridorScore, GateResult, GateScoreRequest, Project
from .schools import School, SchoolShortlistRequest, SchoolShortlistResult

__all__ = [
    "Address",
    "AreaOption",
    "AreaScore",
    "CorridorScore",
    "DecisionRequest",
    "DecisionVerdict",
    "GateResult",
    "GateScoreRequest",
    "HealthStatus",
    "Hospital",
    "LatLonModel",
    "Project",
    "QualityScore",
    "ReachabilityRequest",
    "ReachabilityResult",
    "School",
    "SchoolShortlistRequest",
    "SchoolShortlistResult",
]
