from __future__ import annotations

import math

import httpx
import pytest

from platform_common.errors import GeocodeError
from platform_common.geo import Geocoder, LatLon, TomTomRouter, haversine_km


def test_haversine_zero_distance() -> None:
    assert haversine_km(12.935, 77.624, 12.935, 77.624) == pytest.approx(0.0, abs=1e-9)


def test_haversine_known_distance() -> None:
    # Koramangala to Whitefield is roughly 13-15 km straight line.
    d = haversine_km(12.935, 77.624, 12.969, 77.750)
    assert 12.0 < d < 16.0


def test_haversine_symmetry() -> None:
    a = haversine_km(12.935, 77.624, 13.0, 77.7)
    b = haversine_km(13.0, 77.7, 12.935, 77.624)
    assert math.isclose(a, b)


@pytest.mark.asyncio
async def test_geocoder_parses_first_result(monkeypatch: pytest.MonkeyPatch) -> None:
    async def fake_get_json(self: object, url: str, **kwargs: object) -> object:
        return [{"lat": "12.9351", "lon": "77.6245"}]

    monkeypatch.setattr("platform_common.http.ResilientClient.get_json", fake_get_json)
    geo = Geocoder(min_interval_s=0.0)
    result = await geo.geocode("Koramangala")
    assert result == LatLon(lat=12.9351, lon=77.6245)


@pytest.mark.asyncio
async def test_geocoder_raises_on_empty(monkeypatch: pytest.MonkeyPatch) -> None:
    async def fake_get_json(self: object, url: str, **kwargs: object) -> object:
        return []

    monkeypatch.setattr("platform_common.http.ResilientClient.get_json", fake_get_json)
    geo = Geocoder(min_interval_s=0.0)
    with pytest.raises(GeocodeError):
        await geo.geocode("nowhere-xyz")


@pytest.mark.asyncio
async def test_tomtom_returns_minutes(monkeypatch: pytest.MonkeyPatch) -> None:
    async def fake_get_json(self: object, url: str, **kwargs: object) -> object:
        return {"routes": [{"summary": {"travelTimeInSeconds": 1620}}]}

    monkeypatch.setattr("platform_common.http.ResilientClient.get_json", fake_get_json)
    router = TomTomRouter(api_key="test")
    minutes = await router.drive_minutes(
        LatLon(12.935, 77.624), LatLon(12.97, 77.75), depart_at="2026-07-27T09:00:00"
    )
    assert minutes == pytest.approx(27.0)


def test_httpx_importable() -> None:
    # guards against the http extra being dropped from deps
    assert hasattr(httpx, "AsyncClient")
