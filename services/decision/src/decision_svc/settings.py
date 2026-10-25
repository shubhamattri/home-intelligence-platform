from __future__ import annotations

from platform_common.config import CommonSettings


class DecisionSettings(CommonSettings):
    service_name: str = "decision-svc"
    # Downstream service base URLs (overridden by env in compose/k8s).
    real_estate_url: str = "http://localhost:8001"
    hospitals_url: str = "http://localhost:8002"
    schools_url: str = "http://localhost:8003"
    school_radius_km: float = 5.0


settings = DecisionSettings()
