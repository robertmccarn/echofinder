from __future__ import annotations

from fastapi.testclient import TestClient

from backend.app import main


def test_recommendations_use_configurable_modern_window(monkeypatch) -> None:
    pool = [
        {
            "name": "Recent Candidate",
            "first_known_year": 2021,
            "tags": ["indie rock", "emo"],
            "source_note": "recent",
            "related_legacy_styles": ["Manchester Orchestra"],
        },
        {
            "name": "Older Candidate",
            "first_known_year": 2019,
            "tags": ["indie rock", "emo"],
            "source_note": "older",
            "related_legacy_styles": ["Manchester Orchestra"],
        },
    ]

    monkeypatch.setattr(main, "_load_modern_pool", lambda: pool)
    client = TestClient(main.app)

    response = client.get("/api/recommendations", params={"seed": "Manchester Orchestra", "modern_window_years": 5})
    assert response.status_code == 200
    data = response.json()

    modern_names = [item["artist_name"] for item in data["modern_echoes"]]
    bridge_names = [item["artist_name"] for item in data["bridge_artists"]]
    assert "Recent Candidate" in modern_names
    assert "Older Candidate" in bridge_names


def test_emergence_fallback_is_exposed_in_response(monkeypatch) -> None:
    pool = [
        {
            "name": "Fallback Year Candidate",
            "first_known_year": None,
            "emergence_year": "2022",
            "tags": ["indie rock", "emo"],
            "source_note": "fallback year",
            "related_legacy_styles": ["Manchester Orchestra"],
        },
    ]

    monkeypatch.setattr(main, "_load_modern_pool", lambda: pool)
    client = TestClient(main.app)
    response = client.get("/api/recommendations", params={"seed": "Manchester Orchestra"})
    assert response.status_code == 200

    item = response.json()["modern_echoes"][0]
    assert item["emergence_year"] == 2022
    assert item["emergence_resolution"]["source_field"] == "emergence_year"
    assert item["emergence_resolution"]["fallback_used"] is True
    assert item["emergence_resolution"]["note"] == "resolved"
