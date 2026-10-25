from __future__ import annotations

from pathlib import Path

from platform_common.config import CommonSettings


class SchoolsSettings(CommonSettings):
    service_name: str = "schools-svc"
    data_dir: Path = Path(__file__).resolve().parents[2] / "data"
    database_url: str | None = None


settings = SchoolsSettings()
