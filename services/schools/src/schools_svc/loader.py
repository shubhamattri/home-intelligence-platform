"""One-time loader: JSON snapshot -> schools_db schools table."""

from __future__ import annotations

import asyncio
import json
from pathlib import Path

from persistence import Base, make_engine, make_session_factory

from .models import SchoolRow
from .repository import _parse_tier
from .settings import settings


async def load(database_url: str, data_dir: Path | None = None) -> int:
    data_dir = data_dir or settings.data_dir
    rows = json.loads((data_dir / "bengaluru_schools.json").read_text(encoding="utf-8"))

    from sqlalchemy import text

    engine = make_engine(database_url)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        await conn.execute(text("CREATE EXTENSION IF NOT EXISTS pg_trgm"))
        await conn.execute(
            text(
                "CREATE INDEX IF NOT EXISTS idx_school_name_trgm "
                "ON schools USING gin (name gin_trgm_ops)"
            )
        )
    sf = make_session_factory(engine)
    async with sf() as session:
        # Idempotent: clear before load so re-runs don't hit duplicate keys.
        from sqlalchemy import delete

        await session.execute(delete(SchoolRow))
        session.add_all(
            SchoolRow(
                name=r.get("name", ""),
                board=r.get("board"),
                tier=_parse_tier(r.get("tier")),
                area=r.get("cluster_area") or r.get("area"),
                lat=float(r["lat"]) if r.get("lat") is not None else None,
                lon=float(r["lon"]) if r.get("lon") is not None else None,
            )
            for r in rows
        )
        await session.commit()
    await engine.dispose()
    return len(rows)


def main() -> None:
    url = settings.database_url
    if not url:
        raise SystemExit("DATABASE_URL not set")
    count = asyncio.run(load(url))
    print(f"loaded {count} schools")


if __name__ == "__main__":
    main()
