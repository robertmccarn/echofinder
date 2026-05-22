from fastapi.testclient import TestClient

from backend.app import main


def test_recommendations_use_configurable_modern_window(monkeypatch) -> None:
    pool = [
        {
            "name": "Recent Candidate",
            "first_known_year": 2021,
            "formed_year": 2021,
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
            "source_note": "recent",
            "related_legacy_styles": ["Manchester Orchestra"],
        },
        {
            "name": "Older Candidate",
            "first_known_year": 2019,
            "formed_year": 2019,
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


def test_unknown_seed_returns_404(monkeypatch) -> None:
    monkeypatch.setattr(main, "_load_modern_pool", lambda: [])
    client = TestClient(main.app)
    response = client.get("/api/recommendations", params={"seed": "Unknown Artist"})
    assert response.status_code == 404


def test_recommendations_empty_when_no_match(monkeypatch) -> None:
    pool = [
        {
            "name": "No Match",
            "first_known_year": 2022,
            "formed_year": 2022,
            "active_status": True,
            "spotify_url": "",
            "monthly_listeners": 0,
            "genres": ["jazz"],
            "emotional_tones": [],
            "lyrical_themes": [],
            "production_style": "",
            "vocal_style": "",
            "scene_lineage": "",
            "curator_notes": "test",
            "recommended_legacy_matches": ["Thrice"],
            "tags": ["jazz"],
            "source_note": "no match",
            "related_legacy_styles": ["Thrice"],
        },
    ]
    monkeypatch.setattr(main, "_load_modern_pool", lambda: pool)
    client = TestClient(main.app)

    response = client.get("/api/recommendations", params={"seed": "Manchester Orchestra"})
    assert response.status_code == 200
    data = response.json()
    assert data["modern_echoes"] == []
    assert data["bridge_artists"] == []


def test_legacy_artists_returns_all_seeds(monkeypatch) -> None:
    monkeypatch.setattr(main, "_load_modern_pool", lambda: [])
    client = TestClient(main.app)
    response = client.get("/legacy-artists")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 3
    ids = [a["id"] for a in data]
    assert "manchester-orchestra" in ids
    assert "thrice" in ids
    assert "the-decemberists" in ids
    for artist in data:
        assert "name" in artist
        assert "tags" in artist
        assert "spotify_url" in artist
        assert artist["spotify_url"].startswith("https://open.spotify.com/")


def test_recommendations_by_id_returns_ranked_cards(monkeypatch) -> None:
    pool = [
        {
            "name": "Top Match",
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
            "scene_lineage": "emo revival indie scene",
            "curator_notes": "strong match",
            "recommended_legacy_matches": ["Manchester Orchestra"],
            "tags": ["indie rock", "emo", "post-hardcore"],
            "source_note": "strong match",
            "related_legacy_styles": ["Manchester Orchestra"],
        },
        {
            "name": "Weak Match",
            "first_known_year": 2020,
            "formed_year": 2020,
            "active_status": True,
            "spotify_url": "",
            "monthly_listeners": 0,
            "genres": ["indie rock"],
            "emotional_tones": ["melancholic"],
            "lyrical_themes": ["melancholy"],
            "production_style": "indie rock",
            "vocal_style": "conversational",
            "scene_lineage": "indie",
            "curator_notes": "partial",
            "recommended_legacy_matches": ["Manchester Orchestra"],
            "tags": ["indie rock"],
            "source_note": "partial",
            "related_legacy_styles": ["Manchester Orchestra"],
        },
    ]
    monkeypatch.setattr(main, "_load_modern_pool", lambda: pool)
    client = TestClient(main.app)
    response = client.get("/recommendations/manchester-orchestra")
    assert response.status_code == 200
    data = response.json()
    assert data["seed"] == "Manchester Orchestra"
    assert data["seed_artist"]["id"] == "manchester-orchestra"
    assert data["seed_artist"]["spotify_url"].startswith("https://")
    assert len(data["modern_echoes"]) > 0
    card = data["modern_echoes"][0]
    assert "artist_name" in card
    assert "echo_score" in card
    assert "confidence" in card
    assert "emergence_type" in card
    assert "spotify_url" in card
    assert "shared_tags" in card
    assert "shared_tag_weights" in card
    assert "source_note" in card
    assert card["echo_score"] >= data["modern_echoes"][-1]["echo_score"]


def test_recommendations_by_id_unknown_artist_returns_404(monkeypatch) -> None:
    monkeypatch.setattr(main, "_load_modern_pool", lambda: [])
    client = TestClient(main.app)
    response = client.get("/recommendations/not-a-real-artist")
    assert response.status_code == 404
    error = response.json()["detail"]["error"]
    assert error["code"] == "seed_not_found"


def test_case_insensitive_seed_matching(monkeypatch) -> None:
    pool = [
        {
            "name": "Case Variant Candidate",
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
            "scene_lineage": "emo revival indie",
            "curator_notes": "test",
            "recommended_legacy_matches": ["  manchester orchestra  "],
            "tags": ["indie rock", "emo"],
            "source_note": "whitespace padded",
            "related_legacy_styles": ["  manchester orchestra  "],
        },
    ]
    monkeypatch.setattr(main, "_load_modern_pool", lambda: pool)
    client = TestClient(main.app)
    response = client.get("/api/recommendations", params={"seed": "Manchester Orchestra"})
    assert response.status_code == 200
    data = response.json()
    modern_names = [item["artist_name"] for item in data["modern_echoes"]]
    assert "Case Variant Candidate" in modern_names


def test_recommendations_by_id_includes_emergence_details(monkeypatch) -> None:
    pool = [
        {
            "name": "Modern Artist",
            "first_known_year": 2022,
            "formed_year": 2022,
            "active_status": True,
            "spotify_url": "",
            "monthly_listeners": 0,
            "genres": ["indie rock", "emo"],
            "emotional_tones": ["reflective", "urgent"],
            "lyrical_themes": ["existential questions", "social critique"],
            "production_style": "polished post-hardcore atmospheric",
            "vocal_style": "melodic punk tenor",
            "scene_lineage": "Orange County post-hardcore scene",
            "curator_notes": "test",
            "recommended_legacy_matches": ["Thrice"],
            "tags": ["emo", "indie rock"],
            "source_note": "modern",
            "related_legacy_styles": ["Thrice"],
        },
    ]
    monkeypatch.setattr(main, "_load_modern_pool", lambda: pool)
    client = TestClient(main.app)
    response = client.get("/recommendations/thrice")
    assert response.status_code == 200
    card = response.json()["modern_echoes"][0]
    assert card["emergence_year"] == 2022
    assert card["emergence_resolution"]["source_field"] == "first_known_year"
    assert card["emergence_resolution"]["is_modern_window"] is True
