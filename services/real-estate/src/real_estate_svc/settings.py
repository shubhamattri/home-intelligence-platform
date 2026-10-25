from __future__ import annotations

from pathlib import Path

from platform_common.config import CommonSettings


class RealEstateSettings(CommonSettings):
    service_name: str = "real-estate-svc"
    data_dir: Path = Path(__file__).resolve().parents[2] / "data"
    # Default job hub used for commute gating (Marathahalli / ORR tech belt)
    job_hub_lat: float = 12.956
    job_hub_lon: float = 77.701
    # Async jobs: Redis in compose/k8s; unset => in-memory (single process)
    redis_url: str | None = None
    jobs_inprocess_worker: bool = False
    # Persistence: Postgres when set, else file-backed (dev/tests)
    database_url: str | None = None


settings = RealEstateSettings()
