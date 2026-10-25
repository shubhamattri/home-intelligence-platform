"""Decision orchestrator contracts."""

from __future__ import annotations

from pydantic import BaseModel, Field

from .common import Address
from .hospitals import ReachabilityResult
from .schools import School


class DecisionRequest(BaseModel):
    address: Address
    budget_cr: float = Field(gt=0)
    depart_at: str | None = None
    max_commute_min: float = 45.0
    max_hospital_min: float = 30.0
    min_schools: int = 3
    min_hospital_quality: float = 0.78


class DecisionVerdict(BaseModel):
    """Composed from the three domain services, not from local files."""

    address: Address
    verdict: str  # "buy" | "reject"
    passes: bool
    commute_min: float | None
    hospital: ReachabilityResult
    schools_nearby: int
    sample_schools: list[School]
    failed_gates: list[str]
    rationale: str
