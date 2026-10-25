from __future__ import annotations

from contracts import AreaOption, DecisionRequest, DecisionVerdict
from platform_common.errors import GeocodeError
from platform_common.geo import Geocoder, LatLon, TomTomGeocoder
from service_kit import create_app

from .areas import AREAS
from .clients import HospitalsClient, RealEstateClient, SchoolsClient
from .orchestrator import decide
from .settings import settings

app = create_app(settings.service_name, log_level=settings.log_level)


class _Geocoder:
    """TomTom search (resolves named projects) with a Nominatim fallback."""

    def __init__(self) -> None:
        self._tomtom = TomTomGeocoder(settings.tomtom_api_key) if settings.tomtom_api_key else None
        self._osm = Geocoder(nominatim_url=settings.nominatim_url)

    async def geocode(self, query: str, region: str = "Bengaluru, India") -> LatLon:
        if self._tomtom is not None:
            try:
                return await self._tomtom.geocode(query, region)
            except GeocodeError:
                pass
        return await self._osm.geocode(query, region)


_geocoder = _Geocoder()
_real_estate = RealEstateClient(settings.real_estate_url)
_hospitals = HospitalsClient(settings.hospitals_url)
_schools = SchoolsClient(settings.schools_url)


@app.get("/areas", response_model=list[AreaOption], tags=["decision"])
async def areas() -> list[AreaOption]:
    """Curated Bangalore localities with coordinates, for the UI pickers."""
    return AREAS


@app.post("/decision", response_model=DecisionVerdict, tags=["decision"])
async def decision(req: DecisionRequest) -> DecisionVerdict:
    return await decide(
        req, _geocoder, _real_estate, _hospitals, _schools, settings.school_radius_km
    )
