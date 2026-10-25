"""Shared primitives used across service contracts."""

from __future__ import annotations

from pydantic import BaseModel, Field


class LatLonModel(BaseModel):
    lat: float = Field(ge=-90, le=90)
    lon: float = Field(ge=-180, le=180)


class Address(BaseModel):
    """Either a free-text query or explicit coordinates."""

    query: str | None = None
    coords: LatLonModel | None = None


class HealthStatus(BaseModel):
    status: str = "ok"
    service: str
    version: str = "0.1.0"


class AreaOption(BaseModel):
    """A selectable Bangalore locality with its coordinates (for UI dropdowns)."""

    name: str
    lat: float
    lon: float
