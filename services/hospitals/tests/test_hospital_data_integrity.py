"""Guard the hospital coordinates.

A fuzzy OSM name match once put Narayana Health City (Bommasandra, on Hosur Road)
20 km north by matching it to "Narayana Nethralaya", an unrelated eye hospital.
That silently removed the nearest cardiac centre from every south-east origin and
made Hosur Road origins look far from cardiac care when they are close to it. These tests make that
class of error fail loudly instead of quietly skewing a verdict.
"""

from __future__ import annotations

import json
import math
from pathlib import Path

import pytest

DATA = Path(__file__).resolve().parents[1] / "data" / "golden_hour_hospitals.json"

# Bangalore metro bounding box.
LAT_MIN, LAT_MAX, LON_MIN, LON_MAX = 12.7, 13.35, 77.3, 77.95

# Independently known locations for hospitals whose placement drives verdicts.
KNOWN: dict[str, tuple[float, float]] = {
    "Narayana Health City, Bommasandra, Bangalore": (12.8005, 77.6880),
    "Sri Jayadeva Institute of Cardiology, Bangalore": (12.9181, 77.5993),
    "Fortis Hospital, Bannerghatta Road, Bangalore": (12.8947, 77.5996),
    "Apollo Hospital, Bannerghatta Road, Bangalore": (12.8963, 77.5983),
    "BGS Gleneagles Global Hospital, Kengeri, Bangalore": (12.9063, 77.4855),
}

# A matched name carrying one of these, when the real hospital does not, means a
# different institution was matched.
SPECIALTY_WORDS = ("nethralaya", "eye", "dental", "ayurveda", "nursing home")


def _rows() -> list[dict[str, object]]:
    data: list[dict[str, object]] = json.loads(DATA.read_text(encoding="utf-8"))
    return data


def _km(a: float, b: float, c: float, d: float) -> float:
    r = 6371.0
    dp, dl = math.radians(c - a), math.radians(d - b)
    x = (
        math.sin(dp / 2) ** 2
        + math.cos(math.radians(a)) * math.cos(math.radians(c)) * math.sin(dl / 2) ** 2
    )
    return 2 * r * math.asin(math.sqrt(x))


def test_every_hospital_has_coordinates() -> None:
    missing = [r["verified_name"] for r in _rows() if r.get("lat") is None or r.get("lon") is None]
    assert not missing, f"hospitals without coordinates: {missing}"


def test_all_coordinates_inside_bangalore() -> None:
    for r in _rows():
        lat, lon = float(r["lat"]), float(r["lon"])  # type: ignore[arg-type]
        assert LAT_MIN <= lat <= LAT_MAX and LON_MIN <= lon <= LON_MAX, (
            f"{r['verified_name']} at {lat},{lon} is outside Bangalore"
        )


@pytest.mark.parametrize("name,coords", KNOWN.items())
def test_known_hospitals_are_where_they_actually_are(
    name: str, coords: tuple[float, float]
) -> None:
    row = next((r for r in _rows() if r.get("verified_name") == name), None)
    assert row is not None, f"{name} missing from dataset"
    off = _km(float(row["lat"]), float(row["lon"]), *coords)  # type: ignore[arg-type]
    assert off <= 3.0, f"{name} is {off:.1f} km from its real location"


def test_no_hospital_borrowed_coordinates_from_a_different_specialty() -> None:
    for r in _rows():
        verified = str(r.get("verified_name", "")).lower()
        matched = str(r.get("matched_osm_name") or "").lower()
        for word in SPECIALTY_WORDS:
            assert not (word in matched and word not in verified), (
                f"{r['verified_name']} took coordinates from '{r.get('matched_osm_name')}', "
                "which is a different kind of facility"
            )
