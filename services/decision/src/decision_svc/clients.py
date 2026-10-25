"""Typed async clients for the downstream domain services."""

from __future__ import annotations

from typing import Any

from platform_common.http import ResilientClient


class RealEstateClient:
    def __init__(self, base_url: str, timeout_s: float = 30.0) -> None:
        self._base = base_url
        self._timeout = timeout_s

    async def score_gate(self, payload: dict[str, Any]) -> dict[str, Any]:
        async with ResilientClient(self._base, self._timeout) as c:
            result: dict[str, Any] = await c.post_json("/score/gates", json=payload)
        return result


class HospitalsClient:
    def __init__(self, base_url: str, timeout_s: float = 30.0) -> None:
        self._base = base_url
        self._timeout = timeout_s

    async def reachability(self, payload: dict[str, Any]) -> dict[str, Any]:
        async with ResilientClient(self._base, self._timeout) as c:
            result: dict[str, Any] = await c.post_json("/reachability", json=payload)
        return result


class SchoolsClient:
    def __init__(self, base_url: str, timeout_s: float = 30.0) -> None:
        self._base = base_url
        self._timeout = timeout_s

    async def near(self, lat: float, lon: float, radius_km: float) -> list[dict[str, Any]]:
        async with ResilientClient(self._base, self._timeout) as c:
            result = await c.get_json(
                "/schools/near",
                params={"lat": lat, "lon": lon, "radius_km": radius_km, "limit": 50},
            )
        return list(result)
