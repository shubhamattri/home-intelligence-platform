"""SQLAlchemy models for the schools database (schools_db)."""

from __future__ import annotations

from sqlalchemy.orm import Mapped, mapped_column

from persistence import Base


class SchoolRow(Base):
    __tablename__ = "schools"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(default="")
    board: Mapped[str | None] = mapped_column(default=None)
    tier: Mapped[int | None] = mapped_column(default=None)
    area: Mapped[str | None] = mapped_column(default=None)
    lat: Mapped[float | None] = mapped_column(default=None)
    lon: Mapped[float | None] = mapped_column(default=None)
