"""Shared platform utilities for the Bangalore Home Intelligence services."""

from __future__ import annotations

from .config import CommonSettings, resolve_secret
from .errors import (
    GeocodeError,
    NotFoundError,
    PlatformError,
    RoutingError,
    UpstreamError,
    ValidationError,
)
from .geo import Geocoder, LatLon, TomTomGeocoder, TomTomRouter, haversine_km
from .http import CircuitBreaker, ResilientClient
from .logging import configure_logging, get_logger

__all__ = [
    "CircuitBreaker",
    "CommonSettings",
    "GeocodeError",
    "Geocoder",
    "LatLon",
    "NotFoundError",
    "PlatformError",
    "ResilientClient",
    "RoutingError",
    "TomTomGeocoder",
    "TomTomRouter",
    "UpstreamError",
    "ValidationError",
    "configure_logging",
    "get_logger",
    "haversine_km",
    "resolve_secret",
]
