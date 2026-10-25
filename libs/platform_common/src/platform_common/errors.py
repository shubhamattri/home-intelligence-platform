"""Platform-wide error hierarchy.

Every service raises these instead of bare exceptions so the API layer can map
them to consistent HTTP status codes in one place.
"""

from __future__ import annotations


class PlatformError(Exception):
    """Base class for all platform errors."""

    status_code: int = 500


class NotFoundError(PlatformError):
    """A requested resource does not exist."""

    status_code = 404


class ValidationError(PlatformError):
    """Input failed a domain-level validation rule."""

    status_code = 422


class UpstreamError(PlatformError):
    """A downstream dependency (another service or a 3rd-party API) failed."""

    status_code = 502


class GeocodeError(UpstreamError):
    """Address could not be geocoded."""


class RoutingError(UpstreamError):
    """A drive-time / routing lookup failed."""
