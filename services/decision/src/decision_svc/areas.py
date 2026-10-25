"""Curated Bangalore localities with coordinates, for the UI dropdowns.

Using known coordinates lets the scorer skip geocoding entirely (faster, no
Nominatim dependency, deterministic). Sorted alphabetically for the picker.
"""

from __future__ import annotations

from contracts import AreaOption

_RAW: dict[str, tuple[float, float]] = {
    "Attibele": (12.788, 77.716),
    "Bagalur (North)": (13.132, 77.665),
    "Bannerghatta Road": (12.888, 77.597),
    "Bellandur": (12.925, 77.678),
    "BTM Layout": (12.916, 77.610),
    "Bommanahalli": (12.897, 77.620),
    "Chandapura": (12.804, 77.698),
    "CV Raman Nagar": (12.985, 77.663),
    "Devanahalli (Airport belt)": (13.245, 77.712),
    "Electronic City": (12.845, 77.660),
    "Haralur": (12.905, 77.660),
    "Hebbal": (13.035, 77.597),
    "Hennur": (13.038, 77.640),
    "Hoskote": (13.070, 77.798),
    "HSR Layout": (12.911, 77.641),
    "Indiranagar": (12.971, 77.640),
    "Jayanagar": (12.928, 77.583),
    "JP Nagar": (12.908, 77.585),
    "Kaggadasapura": (12.985, 77.678),
    "Kanakapura Road": (12.888, 77.556),
    "Kasavanahalli": (12.905, 77.680),
    "Kengeri": (12.907, 77.484),
    "Kodathi": (12.885, 77.720),
    "Koramangala": (12.935, 77.624),
    "Marathahalli": (12.956, 77.701),
    "Nelamangala": (13.099, 77.394),
    "Old Airport Road": (12.960, 77.649),
    "Panathur": (12.936, 77.696),
    "Rajajinagar": (12.995, 77.552),
    "RR Nagar": (12.927, 77.517),
    "Sarjapur Road": (12.900, 77.700),
    "Thanisandra": (13.058, 77.630),
    "Varthur": (12.938, 77.741),
    "Whitefield": (12.969, 77.750),
    "Yelahanka": (13.100, 77.596),
}

AREAS: list[AreaOption] = [
    AreaOption(name=name, lat=lat, lon=lon) for name, (lat, lon) in sorted(_RAW.items())
]
