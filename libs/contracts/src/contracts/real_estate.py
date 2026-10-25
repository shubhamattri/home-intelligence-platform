"""Real-estate service contracts."""

from __future__ import annotations

from pydantic import BaseModel, Field

from .common import LatLonModel


class Project(BaseModel):
    reg_no: str
    project_name: str
    promoter: str
    coords: LatLonModel | None = None
    area: str | None = None
    distressed_builder: bool = False


class GateScoreRequest(BaseModel):
    coords: LatLonModel
    budget_cr: float = Field(gt=0)
    depart_at: str | None = None
    max_commute_min: float = 45.0
    max_hospital_min: float = 30.0
    min_schools: int = 3


class GateResult(BaseModel):
    coords: LatLonModel
    passes: bool
    commute_min: float | None = None
    hospital_min: float | None = None
    school_count: int | None = None
    within_budget: bool | None = None
    failed_gates: list[str] = []


class AreaScore(BaseModel):
    area: str
    passes: bool
    jobs_min: float | None = None
    hospital_min: float | None = None
    school_count: int | None = None


class CorridorScore(BaseModel):
    corridor: str
    growth_heuristic: float
    infra_stage_w: float
    leasing: str
    leasing_w: float
    cauvery: str
    water_w: float
    water_gate_ok: bool
    current_psf: float | None = None
    cagr_pct: float | None = None
    thesis: str | None = None
