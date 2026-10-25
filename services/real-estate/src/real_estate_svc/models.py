"""SQLAlchemy models for the real-estate database (real_estate_db)."""

from __future__ import annotations

from sqlalchemy.orm import Mapped, mapped_column

from persistence import Base


class ProjectRow(Base):
    __tablename__ = "projects"

    reg_no: Mapped[str] = mapped_column(primary_key=True)
    project_name: Mapped[str] = mapped_column(default="")
    promoter: Mapped[str] = mapped_column(default="")
    distressed_builder: Mapped[bool] = mapped_column(default=False)
    # Geocoded location + nearest area (from geocoded_projects.json; approximate).
    lat: Mapped[float | None] = mapped_column(default=None)
    lon: Mapped[float | None] = mapped_column(default=None)
    area: Mapped[str | None] = mapped_column(default=None, index=True)
