from fastapi.testclient import TestClient

from backend.app import main
from backend.app.models import ErrorResponse, RecommendationsResponse


def test_health_returns_ok() -> None:
    client = TestClient(main.app)
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_api_recommendations_valid_seed_contains_required_keys(monkeypatch) -> None:
    pool = [
        {
            "name": "Modern Echo",
            "first_known_year": 2022,
            "formed_year": 2022,
            "active_status": True,
            "spotify_url": "",
            "monthly_listeners": 0,
            "genres": ["indie rock", "emo"],
            "emotional_tones": ["introspective", "vulnerable"],
            "lyrical_themes": ["existential doubt", "relationships"],
            "production_style": "layered dynamic builds",
            "vocal_style": "earnest tenor delivery",
            "scene_lineage": "emo revival",
            "curator_notes": "test",
            "recommended_legacy_matches": ["Manchester Orchestra"],
            "tags": ["indie rock", "emo"],
            "source_note": "test source note",
            "related_legacy_styles": ["Manchester Orchestra"],
        },
    ]
    monkeypatch.setattr(main, "_load_modern_pool", lambda: pool)
    client = TestClient(main.app)
    response = client.get("/api/recommendations", params={"seed": "Manchester Orchestra"})
    assert response.status_code == 200
    data = response.json()

    assert "seed" in data
    assert isinstance(data["seed"], str)

    sa = data["seed_artist"]
    assert "id" in sa
    assert "name" in sa
    assert "spotify_url" in sa
    assert "image_url" in sa
    assert "genres" in sa

    assert "modern_echoes" in data
    assert "bridge_artists" in data

    md = data["metadata"]
    assert "reason" in md
    assert "source_status" in md
    ss = md["source_status"]
    assert "manual_pool" in ss
    assert "lastfm_graph" in ss
    assert "musicbrainz" in ss
    assert "spotify" in ss

    all_cards = data["modern_echoes"] + data["bridge_artists"]
    for card in all_cards:
        assert "artist_name" in card
        assert "classification" in card
        assert "echo_score" in card
        assert "confidence" in card
        assert "emergence_year" in card
        assert "emergence_resolution" in card
        assert "shared_tags" in card
        assert "shared_tag_weights" in card
        assert "component_scores" in card
        assert "sources" in card
        assert "source_note" in card
        assert "spotify_url" in card
        assert "image_url" in card
        assert "genres" in card


def test_api_recommendations_unknown_seed_returns_flat_error(monkeypatch) -> None:
    monkeypatch.setattr(main, "_load_modern_pool", lambda: [])
    client = TestClient(main.app)
    response = client.get("/api/recommendations", params={"seed": "Totally Unknown Artist XYZ"})
    assert response.status_code == 404
    body = response.json()
    assert "detail" not in body
    assert body["error"]["code"] == "seed_not_found"
    assert isinstance(body["error"]["message"], str)
    ErrorResponse.model_validate(body)


def test_api_recommendations_empty_results_include_reason_metadata(monkeypatch) -> None:
    monkeypatch.setattr(main, "_load_modern_pool", lambda: [])
    client = TestClient(main.app)
    response = client.get("/api/recommendations", params={"seed": "Manchester Orchestra"})
    assert response.status_code == 200
    data = response.json()
    assert data["modern_echoes"] == []
    assert data["bridge_artists"] == []
    assert data["metadata"]["reason"] == "no_results_found"
    assert data["metadata"]["source_status"]["manual_pool"]["status"] == "empty"


def test_api_recommendations_response_validates_against_model(monkeypatch) -> None:
    pool = [
        {
            "name": "Modern Echo",
            "first_known_year": 2022,
            "formed_year": 2022,
            "active_status": True,
            "spotify_url": "",
            "monthly_listeners": 0,
            "genres": ["indie rock", "emo"],
            "emotional_tones": ["introspective", "vulnerable"],
            "lyrical_themes": ["existential doubt", "relationships"],
            "production_style": "layered dynamic builds",
            "vocal_style": "earnest tenor delivery",
            "scene_lineage": "emo revival",
            "curator_notes": "test",
            "recommended_legacy_matches": ["Manchester Orchestra"],
            "tags": ["indie rock", "emo"],
            "source_note": "test source note",
            "related_legacy_styles": ["Manchester Orchestra"],
        },
    ]
    monkeypatch.setattr(main, "_load_modern_pool", lambda: pool)
    client = TestClient(main.app)
    response = client.get("/api/recommendations", params={"seed": "Manchester Orchestra"})
    assert response.status_code == 200
    RecommendationsResponse.model_validate(response.json())
