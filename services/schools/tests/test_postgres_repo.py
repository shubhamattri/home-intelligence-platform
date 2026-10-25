"""Schools Postgres adapter proven against aiosqlite."""

from __future__ import annotations

import pytest
from sqlalchemy.ext.asyncio import create_async_engine

from persistence import Base, make_session_factory
from schools_svc.models import SchoolRow
from schools_svc.repository import PostgresSchoolsRepository


@pytest.mark.asyncio
async def test_postgres_near_and_shortlist() -> None:
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    sf = make_session_factory(engine)
    async with sf() as session:
        session.add_all(
            [
                SchoolRow(
                    name="Near CBSE",
                    board="CBSE",
                    tier=1,
                    area="Koramangala",
                    lat=12.935,
                    lon=77.624,
                ),
                SchoolRow(
                    name="Far ICSE", board="ICSE", tier=2, area="Whitefield", lat=12.969, lon=77.750
                ),
            ]
        )
        await session.commit()

    repo = PostgresSchoolsRepository(sf)
    near = await repo.near(12.935, 77.624, radius_km=3.0, limit=10)
    shortlist = await repo.shortlist("Koramangala", boards=["CBSE"], min_tier=1)
    await engine.dispose()

    assert [s.name for s in near] == ["Near CBSE"]  # Whitefield is >3km away
    assert [s.name for s in shortlist] == ["Near CBSE"]
