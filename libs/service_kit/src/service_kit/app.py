"""FastAPI application factory shared by every service.

Gives each service, for free: JSON logging, /health, /ready, Prometheus /metrics,
a request-duration histogram, and consistent PlatformError -> HTTP mapping.
"""

from __future__ import annotations

import time
from collections.abc import Awaitable, Callable
from contextlib import AbstractAsyncContextManager

from fastapi import FastAPI, Request, Response
from fastapi.responses import JSONResponse, PlainTextResponse
from prometheus_client import CONTENT_TYPE_LATEST, Counter, Histogram, generate_latest

from platform_common.errors import PlatformError
from platform_common.logging import configure_logging, get_logger

Lifespan = Callable[[FastAPI], AbstractAsyncContextManager[None]]

_REQUESTS = Counter(
    "http_requests_total", "Total HTTP requests", ["service", "method", "path", "status"]
)
_LATENCY = Histogram(
    "http_request_duration_seconds", "Request duration", ["service", "method", "path"]
)


def create_app(
    service_name: str,
    version: str = "0.1.0",
    log_level: str = "INFO",
    lifespan: Lifespan | None = None,
) -> FastAPI:
    configure_logging(level=log_level, service_name=service_name)
    log = get_logger(service_name)
    app = FastAPI(title=service_name, version=version, lifespan=lifespan)

    @app.middleware("http")
    async def _observe(
        request: Request, call_next: Callable[[Request], Awaitable[Response]]
    ) -> Response:
        start = time.perf_counter()
        response = await call_next(request)
        elapsed = time.perf_counter() - start
        route = request.scope.get("route")
        path = getattr(route, "path", request.url.path)
        _REQUESTS.labels(service_name, request.method, path, response.status_code).inc()
        _LATENCY.labels(service_name, request.method, path).observe(elapsed)
        return response

    @app.exception_handler(PlatformError)
    async def _platform_error(_: Request, exc: PlatformError) -> JSONResponse:
        log.warning("platform_error", error=str(exc), status=exc.status_code)
        return JSONResponse(status_code=exc.status_code, content={"detail": str(exc)})

    @app.get("/health", tags=["ops"])
    async def health() -> dict[str, str]:
        return {"status": "ok", "service": service_name, "version": version}

    @app.get("/ready", tags=["ops"])
    async def ready() -> dict[str, str]:
        return {"status": "ready", "service": service_name}

    @app.get("/metrics", tags=["ops"])
    async def metrics() -> Response:
        return PlainTextResponse(generate_latest(), media_type=CONTENT_TYPE_LATEST)

    return app
