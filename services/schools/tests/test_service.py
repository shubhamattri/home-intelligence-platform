from __future__ import annotations

from fastapi.testclient import TestClient

from schools_svc.main import app

client = TestClient(app)


def test_health() -> None:
    assert client.get("/health").json()["service"] == "schools-svc"


def test_list_schools_returns_data() -> None:
    r = client.get("/schools?limit=10")
    assert r.status_code == 200
    assert len(r.json()) == 10


def test_area_filter() -> None:
    r = client.get("/schools?area=Koramangala&limit=500")
    assert r.status_code == 200
    for s in r.json():
        assert "koramangala" in (s["area"] or "").lower()


def test_shortlist_endpoint() -> None:
    r = client.post("/schools/shortlist", json={"area": "HSR"})
    assert r.status_code == 200
    body = r.json()
    assert body["area"] == "HSR"
    assert body["count"] == len(body["schools"])
