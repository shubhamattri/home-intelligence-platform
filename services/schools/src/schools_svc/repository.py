"""Data access for the schools service.

Async repository interface. File adapter (JSON) and Postgres adapter (schools_db)
share the near/shortlist logic, which operates over ``all_schools``.
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Protocol

from sqlalchemy import select
from sqlalchemy.ext.asyncio import async_sessionmaker

from contracts import LatLonModel, School
from persistence import AsyncSession
from platform_common.geo import haversine_km

from .models import SchoolRow
from .settings import settings


def _parse_tier(value: object) -> int | None:
    """Extract the tier number from labels like 'Tier 2 (est.)' or an int."""
    if isinstance(value, int):
        return value
    if isinstance(value, str):
        m = re.search(r"\d+", value)
        if m:
            return int(m.group())
    return None


class SchoolsRepository(Protocol):
    async def all_schools(self) -> list[School]: ...
    async def near(self, lat: float, lon: float, radius_km: float, limit: int) -> list[School]: ...
    async def search(self, q: str, limit: int) -> list[School]: ...
    async def shortlist(
        self, area: str, boards: list[str] | None, min_tier: int | None
    ) -> list[School]: ...


class _QueryMixin:
    """near/shortlist/search logic shared by both adapters."""

    async def all_schools(self) -> list[School]:  # pragma: no cover - overridden
        raise NotImplementedError

    async def search(self, q: str, limit: int) -> list[School]:
        # Token-based, order-independent name match (File/dev fallback).
        toks = [t for t in q.lower().split() if t]
        out = [s for s in await self.all_schools() if all(t in s.name.lower() for t in toks)]
        return out[:limit]

    async def near(self, lat: float, lon: float, radius_km: float, limit: int) -> list[School]:
        scored = [
            (haversine_km(lat, lon, s.coords.lat, s.coords.lon), s)
            for s in await self.all_schools()
            if s.coords is not None
        ]
        scored.sort(key=lambda x: x[0])
        return [s for dist, s in scored if dist <= radius_km][:limit]

    async def shortlist(
        self, area: str, boards: list[str] | None, min_tier: int | None
    ) -> list[School]:
        area_l = area.lower()
        result: list[School] = []
        for s in await self.all_schools():
            if not s.area or area_l not in s.area.lower():
                continue
            if boards and (s.board or "").upper() not in {b.upper() for b in boards}:
                continue
            if min_tier is not None and (s.tier is None or s.tier > min_tier):
                continue
            result.append(s)
        return result


class FileSchoolsRepository(_QueryMixin):
    def __init__(self, data_dir: Path | None = None) -> None:
        self._dir = data_dir or settings.data_dir
        self._cache: list[School] | None = None

    async def all_schools(self) -> list[School]:
        if self._cache is not None:
            return self._cache
        path = self._dir / "bengaluru_schools.json"
        raw = json.loads(path.read_text(encoding="utf-8")) if path.is_file() else []
        out: list[School] = []
        for row in raw:
            coords = None
            if row.get("lat") is not None and row.get("lon") is not None:
                coords = LatLonModel(lat=float(row["lat"]), lon=float(row["lon"]))
            out.append(
                School(
                    name=row.get("name", ""),
                    board=row.get("board"),
                    tier=_parse_tier(row.get("tier")),
                    area=row.get("cluster_area") or row.get("area"),
                    coords=coords,
                )
            )
        self._cache = out
        return out


class PostgresSchoolsRepository(_QueryMixin):
    def __init__(self, session_factory: async_sessionmaker[AsyncSession]) -> None:
        self._sf = session_factory

    async def all_schools(self) -> list[School]:
        async with self._sf() as session:
            rows = (await session.execute(select(SchoolRow))).scalars().all()
        out: list[School] = []
        for r in rows:
            coords = (
                LatLonModel(lat=r.lat, lon=r.lon)
                if r.lat is not None and r.lon is not None
                else None
            )
            out.append(School(name=r.name, board=r.board, tier=r.tier, area=r.area, coords=coords))
        return out

    async def search(self, q: str, limit: int) -> list[School]:
        from sqlalchemy import func

        sim = func.similarity(SchoolRow.name, q)
        stmt = (
            select(SchoolRow)
            .where(func.lower(SchoolRow.name).contains(q.lower()) | (sim > 0.2))
            .order_by(sim.desc())
            .limit(limit)
        )
        async with self._sf() as session:
            rows = (await session.execute(stmt)).scalars().all()
        return [
            School(
                name=r.name,
                board=r.board,
                tier=r.tier,
                area=r.area,
                coords=(
                    LatLonModel(lat=r.lat, lon=r.lon)
                    if r.lat is not None and r.lon is not None
                    else None
                ),
            )
            for r in rows
        ]
