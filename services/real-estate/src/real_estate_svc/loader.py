"""One-time loader: JSON snapshot -> real_estate_db projects table."""

from __future__ import annotations

import asyncio
import json
from pathlib import Path

from persistence import Base, make_engine, make_session_factory

from .models import ProjectRow
from .repository import _norm
from .settings import settings


async def load(database_url: str, data_dir: Path | None = None) -> int:
    data_dir = data_dir or settings.data_dir
    projects = json.loads((data_dir / "base_projects.json").read_text(encoding="utf-8"))
    distress_raw = json.loads((data_dir / "builders_distress.json").read_text(encoding="utf-8"))
    distressed = {
        d["norm"] for d in distress_raw if d.get("level") == "DISTRESSED" and d.get("norm")
    }
    geo_path = data_dir / "geocoded_projects.json"
    geo = json.loads(geo_path.read_text(encoding="utf-8")) if geo_path.is_file() else {}

    from sqlalchemy import text

    engine = make_engine(database_url)
    async with engine.begin() as conn:
        # Recreate so schema changes (new lat/lon/area columns) take effect; the
        # loader is the source of truth and repopulates from JSON below.
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
        # Fuzzy search: trigram similarity + GIN indexes (typo-tolerant, ranked).
        await conn.execute(text("CREATE EXTENSION IF NOT EXISTS pg_trgm"))
        await conn.execute(
            text(
                "CREATE INDEX IF NOT EXISTS idx_proj_name_trgm "
                "ON projects USING gin (project_name gin_trgm_ops)"
            )
        )
        await conn.execute(
            text(
                "CREATE INDEX IF NOT EXISTS idx_proj_prom_trgm "
                "ON projects USING gin (promoter gin_trgm_ops)"
            )
        )
    sf = make_session_factory(engine)
    async with sf() as session:
        # Idempotent: clear before load so re-runs don't hit duplicate primary keys.
        from sqlalchemy import delete

        await session.execute(delete(ProjectRow))
        rows = []
        for p in projects:
            reg = p.get("reg_no")
            if not reg:
                continue
            g = geo.get(reg, {})
            rows.append(
                ProjectRow(
                    reg_no=reg,
                    project_name=p.get("project_name", ""),
                    promoter=p.get("promoter", ""),
                    distressed_builder=_norm(p.get("promoter", "")) in distressed,
                    lat=g.get("lat"),
                    lon=g.get("lon"),
                    area=g.get("area"),
                )
            )
        session.add_all(rows)
        await session.commit()
    await engine.dispose()
    return len(projects)


def main() -> None:
    url = settings.database_url
    if not url:
        raise SystemExit("DATABASE_URL not set")
    count = asyncio.run(load(url))
    print(f"loaded {count} projects")


if __name__ == "__main__":
    main()
