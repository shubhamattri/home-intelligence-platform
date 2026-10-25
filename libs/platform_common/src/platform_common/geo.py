"""Geospatial helpers: haversine, geocoding, and peak-traffic drive times.

This module is the single home for logic that was previously copy-pasted across
the modules (haversine x6, geocode x8, TomTom client x6). Services depend on this
instead of re-implementing it.
"""

from __future__ import annotations

import asyncio
import math
import time
from dataclasses import dataclass

from .errors import GeocodeError, RoutingError
from .http import ResilientClient

EARTH_RADIUS_KM = 6371.0


def haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Great-circle distance in km between two lat/lon points."""

    p1, p2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dlambda / 2) ** 2
    return 2 * EARTH_RADIUS_KM * math.asin(math.sqrt(a))


@dataclass(frozen=True)
class LatLon:
    lat: float
    lon: float


class _RateLimiter:
    """Ensures a minimum interval between calls (Nominatim policy: <= 1 req/s)."""

    def __init__(self, min_interval_s: float) -> None:
        self._min = min_interval_s
        self._last = 0.0
        self._lock = asyncio.Lock()

    async def wait(self) -> None:
        async with self._lock:
            delta = time.monotonic() - self._last
            if delta < self._min:
                await asyncio.sleep(self._min - delta)
            self._last = time.monotonic()


class Geocoder:
    """Nominatim geocoder with polite rate limiting and retries."""

    def __init__(
        self,
        nominatim_url: str = "https://nominatim.openstreetmap.org/search",
        min_interval_s: float = 1.1,
        user_agent: str = "bangalore-home-intelligence/1.0",
        timeout_s: float = 30.0,
    ) -> None:
        self._url = nominatim_url
        self._limiter = _RateLimiter(min_interval_s)
        self._headers = {"User-Agent": user_agent}
        self._timeout = timeout_s

    async def geocode(self, query: str, region: str = "Bengaluru, India") -> LatLon:
        """Return coordinates for a free-text query, or raise GeocodeError."""

        await self._limiter.wait()
        params = {"q": f"{query}, {region}", "format": "json", "limit": 1}
        async with ResilientClient(timeout_s=self._timeout, headers=self._headers) as client:
            data = await client.get_json(self._url, params=params)
        if not data:
            raise GeocodeError(f"no geocode result for {query!r}")
        top = data[0]
        return LatLon(lat=float(top["lat"]), lon=float(top["lon"]))


class TomTomGeocoder:
    """TomTom Search API geocoder. Resolves named projects/POIs and addresses that
    free OSM/Nominatim misses (named apartment projects). Reuses the TomTom key."""

    def __init__(
        self,
        api_key: str,
        base_url: str = "https://api.tomtom.com/search/2/search",
        country: str = "IN",
        timeout_s: float = 30.0,
        bias_lat: float = 12.9716,
        bias_lon: float = 77.5946,
        bias_radius_m: int = 45000,
    ) -> None:
        self._key = api_key
        self._base = base_url
        self._country = country
        self._timeout = timeout_s
        self._bias = (bias_lat, bias_lon, bias_radius_m)

    async def geocode(self, query: str, region: str = "Bengaluru, India") -> LatLon:
        from urllib.parse import quote

        url = f"{self._base}/{quote(f'{query}, {region}')}.json"
        # Geo-bias to Bengaluru so a same-named place elsewhere is not returned.
        params = {
            "key": self._key,
            "limit": "1",
            "countrySet": self._country,
            "lat": str(self._bias[0]),
            "lon": str(self._bias[1]),
            "radius": str(self._bias[2]),
        }
        async with ResilientClient(timeout_s=self._timeout) as client:
            data = await client.get_json(url, params=params)
        results = data.get("results") or []
        if not results:
            raise GeocodeError(f"no TomTom geocode result for {query!r}")
        pos = results[0]["position"]
        return LatLon(lat=float(pos["lat"]), lon=float(pos["lon"]))


class TomTomRouter:
    """TomTom Routing API client for traffic-aware drive times."""

    def __init__(
        self,
        api_key: str,
        base_url: str = "https://api.tomtom.com/routing/1/calculateRoute",
        timeout_s: float = 30.0,
    ) -> None:
        self._key = api_key
        self._base = base_url
        self._timeout = timeout_s

    async def drive_minutes(
        self, origin: LatLon, dest: LatLon, depart_at: str | None = None
    ) -> float:
        """Traffic-aware drive time in minutes. ``depart_at`` is an ISO8601 string
        (e.g. a 9am weekday) to price in peak congestion.
        """

        loc = f"{origin.lat},{origin.lon}:{dest.lat},{dest.lon}"
        url = f"{self._base}/{loc}/json"
        params: dict[str, str] = {"key": self._key, "traffic": "true"}
        if depart_at:
            params["departAt"] = depart_at
        async with ResilientClient(timeout_s=self._timeout) as client:
            data = await client.get_json(url, params=params)
        try:
            seconds = data["routes"][0]["summary"]["travelTimeInSeconds"]
        except (KeyError, IndexError, TypeError) as e:
            raise RoutingError(f"unexpected TomTom response for {loc}") from e
        return round(float(seconds) / 60.0, 1)
