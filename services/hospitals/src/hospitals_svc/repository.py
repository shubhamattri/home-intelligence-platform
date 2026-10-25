from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, ClassVar, Protocol

from contracts import QualityScore

from .settings import settings


@dataclass(frozen=True)
class QualityHospital:
    name: str
    lat: float
    lon: float
    quality: float


def _norm(name: str) -> str:
    return " ".join((name or "").lower().split()[:2])


def _as_float(value: object) -> float | None:
    """Return a float if the value is numeric, else None (categorical labels)."""
    if isinstance(value, int | float):
        return float(value)
    if isinstance(value, str):
        try:
            return float(value)
        except ValueError:
            return None
    return None


class HospitalsRepository(Protocol):
    def quality_scores(self) -> list[QualityScore]: ...
    def quality_hospitals(self, min_quality: float) -> list[QualityHospital]: ...


class FileHospitalsRepository:
    def __init__(self, data_dir: Path | None = None) -> None:
        self._dir = data_dir or settings.data_dir

    def _load(self, name: str) -> list[dict[str, Any]]:
        path = self._dir / name
        data: list[dict[str, Any]] = (
            json.loads(path.read_text(encoding="utf-8")) if path.is_file() else []
        )
        return data

    # Curated real coordinates for major scored hospitals the golden-hour join misses.
    _CURATED: ClassVar[dict[str, tuple[float, float]]] = {
        "manipal old airport": (12.9585, 77.6490),
        "manipal whitefield": (12.9965, 77.7500),
        "apollo bannerghatta": (12.8895, 77.5985),
        "fortis bannerghatta": (12.8890, 77.5995),
        "narayana": (12.8005, 77.6880),
        "sparsh": (13.0235, 77.5540),
    }

    def _curated_coords(self, name: str) -> tuple[float, float] | None:
        n = name.lower()
        for key, latlon in self._CURATED.items():
            if all(w in n for w in key.split()):
                return latlon
        return None

    def quality_scores(self) -> list[QualityScore]:
        # Join coordinates from the golden-hour table (by normalized name), with a
        # curated fallback, so every hospital can be sorted by distance to an area.
        coords: dict[str, tuple[float, float]] = {}
        for r in self._load("golden_hour_hospitals.json"):
            if r.get("lat") is not None and r.get("lon") is not None:
                coords[_norm(str(r.get("verified_name", "")))] = (float(r["lat"]), float(r["lon"]))
        out: list[QualityScore] = []
        for row in self._load("hospital_score_v2.json"):
            name = str(row.get("hospital", ""))
            latlon = coords.get(_norm(name)) or self._curated_coords(name)
            out.append(
                QualityScore(
                    name=name,
                    quality_score=float(row.get("quality_score", 0.0)),
                    accreditation=(str(row["accreditation"]) if row.get("accreditation") else None),
                    sentiment=_as_float(row.get("cleanliness")),
                    cardiac=bool(row.get("cardiac_gate_pass")),
                    lat=latlon[0] if latlon else None,
                    lon=latlon[1] if latlon else None,
                )
            )
        return out

    def quality_hospitals(self, min_quality: float) -> list[QualityHospital]:
        # Join the computed quality table (no coords) with the golden-hour table (coords).
        scores = {
            _norm(str(r.get("hospital", ""))): float(r.get("quality_score", 0.0))
            for r in self._load("hospital_score_v2.json")
        }
        result: list[QualityHospital] = []
        for row in self._load("golden_hour_hospitals.json"):
            lat, lon = row.get("lat"), row.get("lon")
            if lat is None or lon is None:
                continue
            name = str(row.get("verified_name", ""))
            # Fall back to 0.8 for capability-verified hospitals absent from the score table.
            quality = scores.get(_norm(name), 0.8 if row.get("capabilities_verified") else 0.5)
            if quality >= min_quality:
                result.append(
                    QualityHospital(name=name, lat=float(lat), lon=float(lon), quality=quality)
                )
        return result
