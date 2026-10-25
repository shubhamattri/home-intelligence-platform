"""Postgres repository adapter proven against aiosqlite (no live Postgres needed)."""

from __future__ import annotations

import pytest
from sqlalchemy.ext.asyncio import create_async_engine

from persistence import Base, make_session_factory
from real_estate_svc.models import ProjectRow
from real_estate_svc.repository import PostgresRealEstateRepository


@pytest.mark.asyncio
async def test_postgres_adapter_lists_projects() -> None:
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    sf = make_session_factory(engine)

    async with sf() as session:
        session.add_all(
            [
                ProjectRow(reg_no="PRM1", project_name="Alpha", promoter="Good Devs"),
                ProjectRow(
                    reg_no="PRM2", project_name="Beta", promoter="Bad Co", distressed_builder=True
                ),
            ]
        )
        await session.commit()

    repo = PostgresRealEstateRepository(sf)
    projects = await repo.list_projects(limit=10)
    await engine.dispose()

    assert len(projects) == 2
    by_reg = {p.reg_no: p for p in projects}
    assert by_reg["PRM1"].project_name == "Alpha"
    assert by_reg["PRM2"].distressed_builder is True


@pytest.mark.asyncio
async def test_postgres_adapter_still_reads_config_from_file() -> None:
    # corridors/leasing config stays file-based in both adapters
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    sf = make_session_factory(engine)
    repo = PostgresRealEstateRepository(sf)
    corridors = await repo.emerging_corridors()
    await engine.dispose()
    assert len(corridors) >= 5
