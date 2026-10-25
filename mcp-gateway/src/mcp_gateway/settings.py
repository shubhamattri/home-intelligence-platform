from __future__ import annotations

from platform_common.config import CommonSettings


class GatewaySettings(CommonSettings):
    service_name: str = "mcp-gateway"
    # Base URL of the Traefik gateway fronting the platform services.
    platform_url: str = "http://localhost:8080"


settings = GatewaySettings()
