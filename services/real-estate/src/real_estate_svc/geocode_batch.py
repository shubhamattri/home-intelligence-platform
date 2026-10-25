"""Batch-geocode RERA projects -> coords -> nearest area, so the registry can be
filtered by area. Resumable (merges into geocoded_projects.json). TomTom search,
bounded to Bengaluru so bad matches are dropped rather than mis-assigned.

Run: TOMTOM_API_KEY=... uv run python -m real_estate_svc.geocode_batch [N]
"""

from __future__ import annotations

import asyncio
import json
import math
import sys

from platform_common.geo import TomTomGeocoder

from .settings import settings

# 35 curated localities (name -> lat, lon); a project maps to the nearest one.
AREAS: dict[str, tuple[float, float]] = {
    "Attibele": (12.788, 77.716),
    "Bagalur": (13.132, 77.665),
    "Bannerghatta Road": (12.888, 77.597),
    "Bellandur": (12.925, 77.678),
    "BTM Layout": (12.916, 77.610),
    "Bommanahalli": (12.897, 77.620),
    "Chandapura": (12.804, 77.698),
    "CV Raman Nagar": (12.985, 77.663),
    "Devanahalli": (13.245, 77.712),
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
# Bengaluru bounding box; drop geocodes outside it (wrong match).
BOUNDS = (12.7, 13.35, 77.3, 77.95)  # lat_min, lat_max, lon_min, lon_max


def _hav(a: float, b: float, c: float, d: float) -> float:
    R = 6371.0
    dp, dl = math.radians(c - a), math.radians(d - b)
    x = (
        math.sin(dp / 2) ** 2
        + math.cos(math.radians(a)) * math.cos(math.radians(c)) * math.sin(dl / 2) ** 2
    )
    return 2 * R * math.asin(math.sqrt(x))


def _nearest_area(lat: float, lon: float) -> str:
    return min(AREAS.items(), key=lambda kv: _hav(lat, lon, kv[1][0], kv[1][1]))[0]


async def main() -> None:
    limit = int(sys.argv[1]) if len(sys.argv) > 1 else 400
    key = settings.tomtom_api_key
    if not key:
        raise SystemExit("TOMTOM_API_KEY not set")

    projects = json.loads((settings.data_dir / "base_projects.json").read_text())
    out_path = settings.data_dir / "geocoded_projects.json"
    done: dict[str, dict[str, object]] = (
        json.loads(out_path.read_text()) if out_path.is_file() else {}
    )

    geocoder = TomTomGeocoder(key)
    todo = [p for p in projects if p.get("reg_no") and p["reg_no"] not in done][:limit]
    print(f"{len(done)} already geocoded; attempting {len(todo)} more", file=sys.stderr)

    hits = 0
    for i, p in enumerate(todo):
        try:
            loc = await geocoder.geocode(p["project_name"])
        except Exception:
            done[p["reg_no"]] = {"area": None}  # mark attempted, unlocatable
            continue
        if BOUNDS[0] <= loc.lat <= BOUNDS[1] and BOUNDS[2] <= loc.lon <= BOUNDS[3]:
            done[p["reg_no"]] = {
                "lat": loc.lat,
                "lon": loc.lon,
                "area": _nearest_area(loc.lat, loc.lon),
            }
            hits += 1
        else:
            done[p["reg_no"]] = {"area": None}  # geocoded outside Bengaluru -> drop
        if (i + 1) % 50 == 0:
            out_path.write_text(json.dumps(done, ensure_ascii=False))
            print(f"  [{i + 1}] {hits} located", file=sys.stderr)

    out_path.write_text(json.dumps(done, ensure_ascii=False))
    print(f"done: {hits}/{len(todo)} located this run; {len(done)} total attempted")


if __name__ == "__main__":
    asyncio.run(main())
