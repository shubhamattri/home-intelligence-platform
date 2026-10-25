"""Calls into the platform REST services via the Traefik gateway prefixes."""

from __future__ import annotations

from typing import Any

from platform_common.http import ResilientClient

from .settings import settings


async def call_decision(payload: dict[str, Any]) -> dict[str, Any]:
    async with ResilientClient(settings.platform_url, settings.request_timeout_s) as c:
        result: dict[str, Any] = await c.post_json("/dec/decision", json=payload)
    return result


async def get_corridors() -> list[dict[str, Any]]:
    async with ResilientClient(settings.platform_url, settings.request_timeout_s) as c:
        return list(await c.get_json("/re/corridors"))


async def get_hospital_quality() -> list[dict[str, Any]]:
    async with ResilientClient(settings.platform_url, settings.request_timeout_s) as c:
        return list(await c.get_json("/hosp/hospitals/quality"))


async def post_school_shortlist(payload: dict[str, Any]) -> dict[str, Any]:
    async with ResilientClient(settings.platform_url, settings.request_timeout_s) as c:
        result: dict[str, Any] = await c.post_json("/sch/schools/shortlist", json=payload)
    return result
