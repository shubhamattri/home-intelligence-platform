from __future__ import annotations

from pathlib import Path

from platform_common.config import CommonSettings


class HospitalsSettings(CommonSettings):
    service_name: str = "hospitals-svc"
    data_dir: Path = Path(__file__).resolve().parents[2] / "data"
    golden_hour_minutes: float = 60.0


settings = HospitalsSettings()
