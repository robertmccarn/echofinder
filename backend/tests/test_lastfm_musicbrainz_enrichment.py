from unittest.mock import MagicMock

from fastapi.testclient import TestClient

from backend.app import main


def _pool() -> list[dict]:
    return [
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


def _make_client(found: bool = True, fail: bool = False):
    client = MagicMock()

    def search(_: str) -> bool:
        if fail:
            raise RuntimeError("failure")
        return found

    client.search_artist_exists = search
    return client


def test_lastfm_missing_credentials_sets_unavailable(monkeypatch) -> None:
    monkeypatch.setattr(main, "_get_lastfm_client", lambda: None)
    monkeypatch.setattr(main, "_get_musicbrainz_client", lambda: None)
    monkeypatch.setattr(main, "_get_spotify_client", lambda: None)
    monkeypatch.setattr(main, "_load_modern_pool", _pool)
    client = TestClient(main.app)
    response = client.get("/api/recommendations", params={"seed": "Manchester Orchestra"})
    assert response.status_code == 200
    data = response.json()
    assert data["metadata"]["source_status"]["lastfm_graph"]["status"] == "unavailable"


def test_musicbrainz_missing_credentials_sets_unavailable(monkeypatch) -> None:
    monkeypatch.setattr(main, "_get_lastfm_client", lambda: None)
    monkeypatch.setattr(main, "_get_musicbrainz_client", lambda: None)
    monkeypatch.setattr(main, "_get_spotify_client", lambda: None)
    monkeypatch.setattr(main, "_load_modern_pool", _pool)
    client = TestClient(main.app)
    response = client.get("/api/recommendations", params={"seed": "Manchester Orchestra"})
    assert response.status_code == 200
    data = response.json()
    assert data["metadata"]["source_status"]["musicbrainz"]["status"] == "unavailable"


def test_lastfm_ok_status(monkeypatch) -> None:
    monkeypatch.setattr(main, "_get_lastfm_client", lambda: _make_client(found=True))
    monkeypatch.setattr(main, "_get_musicbrainz_client", lambda: None)
    monkeypatch.setattr(main, "_get_spotify_client", lambda: None)
    monkeypatch.setattr(main, "_load_modern_pool", _pool)
    client = TestClient(main.app)
    response = client.get("/api/recommendations", params={"seed": "Manchester Orchestra"})
    assert response.status_code == 200
    data = response.json()
    assert data["metadata"]["source_status"]["lastfm_graph"]["status"] == "ok"


def test_musicbrainz_ok_status(monkeypatch) -> None:
    monkeypatch.setattr(main, "_get_lastfm_client", lambda: None)
    monkeypatch.setattr(main, "_get_musicbrainz_client", lambda: _make_client(found=True))
    monkeypatch.setattr(main, "_get_spotify_client", lambda: None)
    monkeypatch.setattr(main, "_load_modern_pool", _pool)
    client = TestClient(main.app)
    response = client.get("/api/recommendations", params={"seed": "Manchester Orchestra"})
    assert response.status_code == 200
    data = response.json()
    assert data["metadata"]["source_status"]["musicbrainz"]["status"] == "ok"


def test_lastfm_empty_status(monkeypatch) -> None:
    monkeypatch.setattr(main, "_get_lastfm_client", lambda: _make_client(found=False))
    monkeypatch.setattr(main, "_get_musicbrainz_client", lambda: None)
    monkeypatch.setattr(main, "_get_spotify_client", lambda: None)
    monkeypatch.setattr(main, "_load_modern_pool", _pool)
    client = TestClient(main.app)
    response = client.get("/api/recommendations", params={"seed": "Manchester Orchestra"})
    assert response.status_code == 200
    data = response.json()
    assert data["metadata"]["source_status"]["lastfm_graph"]["status"] == "empty"


def test_musicbrainz_empty_status(monkeypatch) -> None:
    monkeypatch.setattr(main, "_get_lastfm_client", lambda: None)
    monkeypatch.setattr(main, "_get_musicbrainz_client", lambda: _make_client(found=False))
    monkeypatch.setattr(main, "_get_spotify_client", lambda: None)
    monkeypatch.setattr(main, "_load_modern_pool", _pool)
    client = TestClient(main.app)
    response = client.get("/api/recommendations", params={"seed": "Manchester Orchestra"})
    assert response.status_code == 200
    data = response.json()
    assert data["metadata"]["source_status"]["musicbrainz"]["status"] == "empty"


def test_lastfm_failed_status(monkeypatch) -> None:
    monkeypatch.setattr(main, "_get_lastfm_client", lambda: _make_client(fail=True))
    monkeypatch.setattr(main, "_get_musicbrainz_client", lambda: None)
    monkeypatch.setattr(main, "_get_spotify_client", lambda: None)
    monkeypatch.setattr(main, "_load_modern_pool", _pool)
    client = TestClient(main.app)
    response = client.get("/api/recommendations", params={"seed": "Manchester Orchestra"})
    assert response.status_code == 200
    data = response.json()
    assert data["metadata"]["source_status"]["lastfm_graph"]["status"] == "failed"


def test_musicbrainz_failed_status(monkeypatch) -> None:
    monkeypatch.setattr(main, "_get_lastfm_client", lambda: None)
    monkeypatch.setattr(main, "_get_musicbrainz_client", lambda: _make_client(fail=True))
    monkeypatch.setattr(main, "_get_spotify_client", lambda: None)
    monkeypatch.setattr(main, "_load_modern_pool", _pool)
    client = TestClient(main.app)
    response = client.get("/api/recommendations", params={"seed": "Manchester Orchestra"})
    assert response.status_code == 200
    data = response.json()
    assert data["metadata"]["source_status"]["musicbrainz"]["status"] == "failed"
