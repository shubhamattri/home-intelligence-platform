"""Hospitals service contracts."""

from __future__ import annotations

from pydantic import BaseModel, Field

from .common import LatLonModel


class Hospital(BaseModel):
    name: str
    coords: LatLonModel
    tier: str | None = None
    accredited: bool = False


class QualityScore(BaseModel):
    name: str
    quality_score: float = Field(ge=0, le=1)
    accreditation: str | None = None
    sentiment: float | None = None
    cardiac: bool = False
    lat: float | None = None
    lon: float | None = None


class ReachabilityRequest(BaseModel):
    origin: LatLonModel
    depart_at: str | None = None
    min_quality: float = Field(default=0.78, ge=0, le=1)


class ReachabilityResult(BaseModel):
    origin: LatLonModel
    nearest_quality_hospital: str | None
    nearest_coords: LatLonModel | None = None
    drive_minutes: float | None
    within_golden_hour: bool
    min_quality: float
