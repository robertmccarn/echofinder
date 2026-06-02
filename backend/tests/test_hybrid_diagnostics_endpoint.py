from __future__ import annotations

from fastapi.testclient import TestClient

from backend.app import main


def test_diagnostics_endpoint_returns_shape(monkeypatch) -> None:
    pool = [
        {
            "name": "Modern Echo",
            "first_known_year": 2024,
            "formed_year": 2023,
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
    monkeypatch.setattr(main, "_enrich_recommendation_response", lambda response, seed_artist: None)

    client = TestClient(main.app)
    response = client.get("/api/recommendations/diagnostics", params={"seed": "Manchester Orchestra"})
    assert response.status_code == 200
    data = response.json()
    assert data["seed"] == "Manchester Orchestra"
    assert "model_version" in data
    assert "mode" in data
    assert "legacy_count" in data
    assert "hybrid_count" in data
    assert isinstance(data["candidates"], list)
    if data["candidates"]:
        c = data["candidates"][0]
        assert "artist_name" in c
        assert "gate_ok" in c
        assert "gate_reason" in c
        assert "final_score" in c
        assert "components" in c
        assert "explanation" in c

