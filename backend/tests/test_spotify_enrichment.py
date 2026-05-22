from unittest.mock import MagicMock

from fastapi.testclient import TestClient

from backend.app import main
from backend.app.spotify import SpotifyArtistMetadata


def _make_mock_client(meta: SpotifyArtistMetadata | None = None, fail: bool = False):
    client = MagicMock()
    client.is_configured = True

    def search(name: str) -> SpotifyArtistMetadata | None:
        if fail:
            raise RuntimeError("Simulated Spotify failure")
        return meta

    client.search_artist = search
    return client


def test_spotify_metadata_model_defaults() -> None:
    meta = SpotifyArtistMetadata(name="Test Artist")
    assert meta.name == "Test Artist"
    assert meta.spotify_url == ""
    assert meta.image_url == ""
    assert meta.genres == []


def test_spotify_metadata_model_full() -> None:
    meta = SpotifyArtistMetadata(
        name="Test Artist",
        spotify_url="https://open.spotify.com/artist/abc",
        image_url="https://i.scdn.co/image/abc",
        genres=["indie rock", "emo"],
    )
    assert meta.spotify_url == "https://open.spotify.com/artist/abc"
    assert meta.image_url == "https://i.scdn.co/image/abc"
    assert meta.genres == ["indie rock", "emo"]


def test_missing_credentials_returns_unavailable_status(monkeypatch) -> None:
    monkeypatch.setattr(main, "_get_spotify_client", lambda: None)
    monkeypatch.setattr(main, "_load_modern_pool", lambda: [])
    client = TestClient(main.app)
    response = client.get("/api/recommendations", params={"seed": "Manchester Orchestra"})
    assert response.status_code == 200
    data = response.json()
    assert data["metadata"]["source_status"]["spotify"]["status"] == "unavailable"


def test_missing_credentials_still_returns_200_for_known_seed(monkeypatch) -> None:
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
            "source_note": "test",
            "related_legacy_styles": ["Manchester Orchestra"],
        },
    ]
    monkeypatch.setattr(main, "_get_spotify_client", lambda: None)
    monkeypatch.setattr(main, "_load_modern_pool", lambda: pool)
    client = TestClient(main.app)
    response = client.get("/api/recommendations", params={"seed": "Manchester Orchestra"})
    assert response.status_code == 200
    data = response.json()
    assert len(data["modern_echoes"]) > 0
    assert data["metadata"]["source_status"]["spotify"]["status"] == "unavailable"


def test_missing_credentials_card_fields_default_to_empty(monkeypatch) -> None:
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
            "source_note": "test",
            "related_legacy_styles": ["Manchester Orchestra"],
        },
    ]
    monkeypatch.setattr(main, "_get_spotify_client", lambda: None)
    monkeypatch.setattr(main, "_load_modern_pool", lambda: pool)
    client = TestClient(main.app)
    response = client.get("/api/recommendations", params={"seed": "Manchester Orchestra"})
    assert response.status_code == 200
    data = response.json()
    card = data["modern_echoes"][0]
    assert card["image_url"] == ""
    assert card["genres"] == []
    assert data["seed_artist"]["image_url"] == ""
    assert data["seed_artist"]["genres"] == []


def test_successful_enrichment_sets_ok_status(monkeypatch) -> None:
    meta = SpotifyArtistMetadata(
        name="Manchester Orchestra",
        spotify_url="https://open.spotify.com/artist/abc",
        image_url="https://i.scdn.co/image/abc",
        genres=["indie rock", "emo"],
    )
    monkeypatch.setattr(main, "_get_spotify_client", lambda: _make_mock_client(meta))
    monkeypatch.setattr(main, "_load_modern_pool", lambda: [])
    client = TestClient(main.app)
    response = client.get("/api/recommendations", params={"seed": "Manchester Orchestra"})
    assert response.status_code == 200
    data = response.json()
    assert data["metadata"]["source_status"]["spotify"]["status"] == "ok"


def test_successful_enrichment_sets_seed_artist_metadata(monkeypatch) -> None:
    meta = SpotifyArtistMetadata(
        name="Manchester Orchestra",
        spotify_url="https://open.spotify.com/artist/abc",
        image_url="https://i.scdn.co/image/abc",
        genres=["indie rock", "emo"],
    )
    monkeypatch.setattr(main, "_get_spotify_client", lambda: _make_mock_client(meta))
    monkeypatch.setattr(main, "_load_modern_pool", lambda: [])
    client = TestClient(main.app)
    response = client.get("/api/recommendations", params={"seed": "Manchester Orchestra"})
    assert response.status_code == 200
    data = response.json()
    assert data["seed_artist"]["spotify_url"] == "https://open.spotify.com/artist/abc"
    assert data["seed_artist"]["image_url"] == "https://i.scdn.co/image/abc"
    assert data["seed_artist"]["genres"] == ["indie rock", "emo"]


def test_successful_enrichment_sets_card_metadata(monkeypatch) -> None:
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
            "source_note": "test",
            "related_legacy_styles": ["Manchester Orchestra"],
        },
    ]
    meta = SpotifyArtistMetadata(
        name="Modern Echo",
        spotify_url="https://open.spotify.com/artist/card",
        image_url="https://i.scdn.co/image/card",
        genres=["indie rock"],
    )

    def mock_client():
        c = MagicMock()
        c.search_artist = lambda name: meta
        return c

    monkeypatch.setattr(main, "_get_spotify_client", mock_client)
    monkeypatch.setattr(main, "_load_modern_pool", lambda: pool)
    client = TestClient(main.app)
    response = client.get("/api/recommendations", params={"seed": "Manchester Orchestra"})
    assert response.status_code == 200
    data = response.json()
    card = data["modern_echoes"][0]
    assert card["spotify_url"] == "https://open.spotify.com/artist/card"
    assert card["image_url"] == "https://i.scdn.co/image/card"
    assert card["genres"] == ["indie rock"]


def test_no_match_from_spotify_returns_empty_status(monkeypatch) -> None:
    monkeypatch.setattr(main, "_get_spotify_client", lambda: _make_mock_client(None))
    monkeypatch.setattr(main, "_load_modern_pool", lambda: [])
    client = TestClient(main.app)
    response = client.get("/api/recommendations", params={"seed": "Manchester Orchestra"})
    assert response.status_code == 200
    data = response.json()
    assert data["metadata"]["source_status"]["spotify"]["status"] == "empty"


def test_no_match_keeps_fields_empty(monkeypatch) -> None:
    monkeypatch.setattr(main, "_get_spotify_client", lambda: _make_mock_client(None))
    monkeypatch.setattr(main, "_load_modern_pool", lambda: [])
    client = TestClient(main.app)
    response = client.get("/api/recommendations", params={"seed": "Manchester Orchestra"})
    assert response.status_code == 200
    data = response.json()
    assert data["seed_artist"]["image_url"] == ""
    assert data["seed_artist"]["genres"] == []


def test_spotify_failure_sets_failed_status(monkeypatch) -> None:
    monkeypatch.setattr(main, "_get_spotify_client", lambda: _make_mock_client(fail=True))
    monkeypatch.setattr(main, "_load_modern_pool", lambda: [])
    client = TestClient(main.app)
    response = client.get("/api/recommendations", params={"seed": "Manchester Orchestra"})
    assert response.status_code == 200
    data = response.json()
    assert data["metadata"]["source_status"]["spotify"]["status"] == "failed"


def test_spotify_failure_still_returns_manual_results(monkeypatch) -> None:
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
            "source_note": "test",
            "related_legacy_styles": ["Manchester Orchestra"],
        },
    ]
    monkeypatch.setattr(main, "_get_spotify_client", lambda: _make_mock_client(fail=True))
    monkeypatch.setattr(main, "_load_modern_pool", lambda: pool)
    client = TestClient(main.app)
    response = client.get("/api/recommendations", params={"seed": "Manchester Orchestra"})
    assert response.status_code == 200
    data = response.json()
    assert len(data["modern_echoes"]) > 0
    assert data["modern_echoes"][0]["artist_name"] == "Modern Echo"


def test_spotify_failure_has_no_stack_trace(monkeypatch) -> None:
    monkeypatch.setattr(main, "_get_spotify_client", lambda: _make_mock_client(fail=True))
    monkeypatch.setattr(main, "_load_modern_pool", lambda: [])
    client = TestClient(main.app)
    response = client.get("/api/recommendations", params={"seed": "Manchester Orchestra"})
    body_text = response.text
    assert "Traceback" not in body_text
    assert "RuntimeError" not in body_text
