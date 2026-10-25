"""12-factor configuration shared by every service.

Keys resolve from environment variables. To preserve the original scripts'
convenience of a local key file (e.g. ``data/.tomtom_key``), ``resolve_secret``
also accepts a fallback file path.
"""

from __future__ import annotations

from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class CommonSettings(BaseSettings):
    """Base settings; each service subclasses and adds its own fields."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # External APIs (all optional; each unlocks one data source)
    tomtom_api_key: str | None = None
    google_maps_key: str | None = None
    firecrawl_api_key: str | None = None

    # External endpoints
    nominatim_url: str = "https://nominatim.openstreetmap.org/search"
    tomtom_base_url: str = "https://api.tomtom.com/routing/1/calculateRoute"

    # HTTP behaviour
    request_timeout_s: float = 30.0
    nominatim_min_interval_s: float = 1.1  # Nominatim usage policy: <= 1 req/s

    # Observability
    log_level: str = "INFO"
    service_name: str = "platform"


def resolve_secret(value: str | None, fallback_file: str | Path | None = None) -> str | None:
    """Return ``value`` if set, else the stripped contents of ``fallback_file``.

    Lets a key come from an env var in production and a gitignored local file in
    development, without hardcoding anything.
    """

    if value:
        return value
    if fallback_file is not None:
        path = Path(fallback_file).expanduser()
        if path.is_file():
            return path.read_text(encoding="utf-8").strip() or None
    return None
