"""Data access for the real-estate service.

Async repository interface with two adapters behind it:
- FileRealEstateRepository: JSON snapshots (dev/tests).
- PostgresRealEstateRepository: projects table in real_estate_db.
Small config datasets (distress list, corridor inputs) stay file-based in both.
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any, Protocol

from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import async_sessionmaker

from contracts import LatLonModel, Project
from persistence import AsyncSession

from .models import ProjectRow
from .settings import settings


class RealEstateRepository(Protocol):
    async def list_projects(
        self,
        limit: int = 100,
        q: str | None = None,
        exclude_distressed: bool = False,
        offset: int = 0,
        area: str | None = None,
    ) -> list[Project]: ...
    async def distressed_norms(self) -> set[str]: ...
    async def emerging_corridors(self) -> list[dict[str, Any]]: ...
    async def leasing_water(self) -> dict[str, Any]: ...
    async def appreciation(self) -> dict[str, Any]: ...


def _load(path: Path, default: Any) -> Any:
    if not path.is_file():
        return default
    return json.loads(path.read_text(encoding="utf-8"))


def _norm(name: str) -> str:
    name = re.sub(r"&amp;", "&", (name or "").lower())
    return re.sub(
        r"\b(private|pvt|limited|ltd|llp|developers?|builders?|properties|projects|group|infra|and|&)\b",
        "",
        name,
    ).strip()


class _ConfigReadsMixin:
    """Shared file-based reads of the small config datasets."""

    _dir: Path

    async def distressed_norms(self) -> set[str]:
        raw = _load(self._dir / "builders_distress.json", [])
        return {d["norm"] for d in raw if d.get("level") == "DISTRESSED" and d.get("norm")}

    async def emerging_corridors(self) -> list[dict[str, Any]]:
        return list(_load(self._dir / "emerging_corridors.json", []))

    async def leasing_water(self) -> dict[str, Any]:
        return dict(_load(self._dir / "leasing_water.json", {"leasing": [], "water": []}))

    async def appreciation(self) -> dict[str, Any]:
        return dict(_load(self._dir / "appreciation.json", {"historical": [], "emerging": []}))


class FileRealEstateRepository(_ConfigReadsMixin):
    def __init__(self, data_dir: Path | None = None) -> None:
        self._dir = data_dir or settings.data_dir

    async def list_projects(
        self,
        limit: int = 100,
        q: str | None = None,
        exclude_distressed: bool = False,
        offset: int = 0,
        area: str | None = None,
    ) -> list[Project]:
        raw = _load(self._dir / "base_projects.json", [])
        geo = _load(self._dir / "geocoded_projects.json", {})
        distressed = await self.distressed_norms()
        ql = (q or "").lower().strip()
        matched: list[Project] = []
        for row in raw:
            name, promoter = row.get("project_name", ""), row.get("promoter", "")
            if ql and ql not in name.lower() and ql not in promoter.lower():
                continue
            g = geo.get(row.get("reg_no", ""), {})
            if area and g.get("area") != area:
                continue
            is_distressed = _norm(promoter) in distressed
            if exclude_distressed and is_distressed:
                continue
            coords = LatLonModel(lat=g["lat"], lon=g["lon"]) if g.get("lat") is not None else None
            matched.append(
                Project(
                    reg_no=row.get("reg_no", ""),
                    project_name=name,
                    promoter=promoter,
                    coords=coords,
                    area=g.get("area"),
                    distressed_builder=is_distressed,
                )
            )
        return matched[offset : offset + limit]


class PostgresRealEstateRepository(_ConfigReadsMixin):
    def __init__(
        self, session_factory: async_sessionmaker[AsyncSession], data_dir: Path | None = None
    ) -> None:
        self._sf = session_factory
        self._dir = data_dir or settings.data_dir

    async def list_projects(
        self,
        limit: int = 100,
        q: str | None = None,
        exclude_distressed: bool = False,
        offset: int = 0,
        area: str | None = None,
    ) -> list[Project]:
        stmt = select(ProjectRow)
        if q:
            # Fuzzy: trigram similarity (typo/word-order tolerant) OR substring, ranked.
            like = f"%{q}%"
            sim = func.greatest(
                func.similarity(ProjectRow.project_name, q),
                func.similarity(ProjectRow.promoter, q),
            )
            stmt = stmt.where(
                or_(
                    ProjectRow.project_name.ilike(like), ProjectRow.promoter.ilike(like), sim > 0.15
                )
            ).order_by(sim.desc())
        if area:
            stmt = stmt.where(ProjectRow.area == area)
        if exclude_distressed:
            stmt = stmt.where(ProjectRow.distressed_builder.is_(False))
        async with self._sf() as session:
            rows = (await session.execute(stmt.offset(offset).limit(limit))).scalars().all()
        return [
            Project(
                reg_no=r.reg_no,
                project_name=r.project_name,
                promoter=r.promoter,
                coords=(
                    LatLonModel(lat=r.lat, lon=r.lon)
                    if r.lat is not None and r.lon is not None
                    else None
                ),
                area=r.area,
                distressed_builder=r.distressed_builder,
            )
            for r in rows
        ]
