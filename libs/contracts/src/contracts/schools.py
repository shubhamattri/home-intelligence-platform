"""Schools service contracts."""

from __future__ import annotations

from pydantic import BaseModel

from .common import LatLonModel


class School(BaseModel):
    name: str
    board: str | None = None
    tier: int | None = None
    area: str | None = None
    coords: LatLonModel | None = None


class SchoolShortlistRequest(BaseModel):
    area: str
    boards: list[str] | None = None
    min_tier: int | None = None


class SchoolShortlistResult(BaseModel):
    area: str
    count: int
    schools: list[School]
