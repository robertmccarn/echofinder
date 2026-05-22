from backend.app.models import (
    ComponentScoresOut,
    EmergenceResolutionOut,
    ErrorResponse,
    RecommendationCard,
    RecommendationsResponse,
    ResponseMetadataOut,
    SeedArtist,
    SharedTagWeight,
    SourceStatusOut,
)


def test_recommendation_card_roundtrip() -> None:
    raw = {
        "artist_name": "Test Artist",
        "classification": "modern_echo",
        "echo_score": 85.0,
        "confidence": 0.75,
        "emergence_type": "formed_recent",
        "emergence_year": 2022,
        "emergence_resolution": {
            "source_field": "formed_year",
            "fallback_used": False,
            "is_modern_window": True,
            "window_start_year": 2021,
            "window_end_year": 2026,
            "note": "resolved",
        },
        "shared_tags": ["emo", "indie rock"],
        "shared_tag_weights": [{"tag": "emo", "weight": 0.5}, {"tag": "indie rock", "weight": 0.5}],
        "component_scores": {
            "emotional_match": 0.8,
            "scene_match": 0.6,
            "lyrical_match": 0.4,
            "production_match": 0.7,
            "vocal_match": 0.5,
            "emerging_bonus": 1.0,
        },
        "sources": ["manual_pool"],
        "source_note": "test",
        "spotify_url": "",
    }
    card = RecommendationCard.model_validate(raw)
    assert card.artist_name == "Test Artist"
    assert card.classification == "modern_echo"
    assert card.echo_score == 85.0
    assert card.confidence == 0.75
    assert card.emergence_type == "formed_recent"
    assert card.emergence_year == 2022
    assert card.emergence_resolution.source_field == "formed_year"
    assert card.emergence_resolution.fallback_used is False
    assert card.shared_tags == ["emo", "indie rock"]
    assert card.shared_tag_weights[0].tag == "emo"
    assert card.shared_tag_weights[0].weight == 0.5
    assert card.component_scores.emotional_match == 0.8
    assert card.component_scores.emerging_bonus == 1.0
    assert card.sources == ["manual_pool"]

    serialized = card.model_dump(mode="json")
    assert serialized["artist_name"] == "Test Artist"
    assert serialized["component_scores"]["emotional_match"] == 0.8
    assert serialized["emergence_resolution"]["source_field"] == "formed_year"


def test_recommendation_card_none_emergence_year() -> None:
    raw = {
        "artist_name": "Unknown Year",
        "classification": "bridge_artist",
        "echo_score": 45.0,
        "confidence": 0.3,
        "emergence_type": "unknown",
        "emergence_year": None,
        "emergence_resolution": {
            "source_field": None,
            "fallback_used": True,
            "is_modern_window": False,
            "window_start_year": 2021,
            "window_end_year": 2026,
            "note": "unresolved_year",
        },
        "shared_tags": [],
        "shared_tag_weights": [],
        "component_scores": {
            "emotional_match": 0.0,
            "scene_match": 0.0,
            "lyrical_match": 0.0,
            "production_match": 0.0,
            "vocal_match": 0.0,
            "emerging_bonus": 0.0,
        },
        "sources": ["manual_pool"],
        "source_note": "",
        "spotify_url": "",
    }
    card = RecommendationCard.model_validate(raw)
    assert card.emergence_year is None
    assert card.emergence_resolution.source_field is None
    assert card.shared_tags == []
    assert card.shared_tag_weights == []

    serialized = card.model_dump(mode="json")
    assert serialized["emergence_year"] is None
    assert serialized["shared_tag_weights"] == []


def test_recommendations_response_roundtrip() -> None:
    data = {
        "seed": "Manchester Orchestra",
        "seed_artist": {
            "id": "manchester-orchestra",
            "name": "Manchester Orchestra",
            "spotify_url": "https://open.spotify.com/artist/...",
        },
        "modern_echoes": [
            {
                "artist_name": "Echo Artist",
                "classification": "modern_echo",
                "echo_score": 90.0,
                "confidence": 0.8,
                "emergence_type": "formed_recent",
                "emergence_year": 2022,
                "emergence_resolution": {
                    "source_field": "formed_year",
                    "fallback_used": False,
                    "is_modern_window": True,
                    "window_start_year": 2021,
                    "window_end_year": 2026,
                    "note": "resolved",
                },
                "shared_tags": ["emo"],
                "shared_tag_weights": [{"tag": "emo", "weight": 1.0}],
                "component_scores": {
                    "emotional_match": 0.9,
                    "scene_match": 0.8,
                    "lyrical_match": 0.7,
                    "production_match": 0.6,
                    "vocal_match": 0.5,
                    "emerging_bonus": 1.0,
                },
                "sources": ["manual_pool"],
                "source_note": "",
                "spotify_url": "",
            }
        ],
        "bridge_artists": [],
    }
    resp = RecommendationsResponse.model_validate(data)
    assert resp.seed == "Manchester Orchestra"
    assert resp.seed_artist.id == "manchester-orchestra"
    assert len(resp.modern_echoes) == 1
    assert len(resp.bridge_artists) == 0
    assert resp.modern_echoes[0].artist_name == "Echo Artist"

    serialized = resp.model_dump(mode="json")
    assert serialized["seed_artist"]["name"] == "Manchester Orchestra"


def test_error_response_roundtrip() -> None:
    raw = {"error": {"code": "seed_not_found", "message": "Unknown seed"}}
    err = ErrorResponse.model_validate(raw)
    assert err.error.code == "seed_not_found"
    assert err.error.message == "Unknown seed"

    serialized = err.model_dump(mode="json")
    assert serialized["error"]["code"] == "seed_not_found"


def test_component_scores_defaults() -> None:
    cs = ComponentScoresOut()
    assert cs.emotional_match == 0.0
    assert cs.scene_match == 0.0
    assert cs.lyrical_match == 0.0
    assert cs.production_match == 0.0
    assert cs.vocal_match == 0.0
    assert cs.emerging_bonus == 0.0


def test_shared_tag_weight_roundtrip() -> None:
    raw = {"tag": "post-hardcore", "weight": 0.333}
    stw = SharedTagWeight.model_validate(raw)
    assert stw.tag == "post-hardcore"
    assert stw.weight == 0.333


def test_source_status_out_roundtrip() -> None:
    raw = {"status": "ok", "message": "Candidates found"}
    ss = SourceStatusOut.model_validate(raw)
    assert ss.status == "ok"
    assert ss.message == "Candidates found"

    serialized = ss.model_dump(mode="json")
    assert serialized["status"] == "ok"
    assert serialized["message"] == "Candidates found"


def test_source_status_out_default_message() -> None:
    raw = {"status": "planned"}
    ss = SourceStatusOut.model_validate(raw)
    assert ss.status == "planned"
    assert ss.message == ""


def test_response_metadata_out_roundtrip() -> None:
    raw = {
        "reason": "results_found",
        "source_status": {
            "manual_pool": {"status": "ok", "message": ""},
            "lastfm_graph": {"status": "planned", "message": "Not implemented"},
        },
    }
    md = ResponseMetadataOut.model_validate(raw)
    assert md.reason == "results_found"
    assert md.source_status["manual_pool"].status == "ok"
    assert md.source_status["lastfm_graph"].status == "planned"

    serialized = md.model_dump(mode="json")
    assert serialized["reason"] == "results_found"
    assert serialized["source_status"]["manual_pool"]["status"] == "ok"


def test_response_metadata_out_defaults() -> None:
    md = ResponseMetadataOut()
    assert md.reason == ""
    assert md.source_status == {}


def test_recommendations_response_with_metadata_roundtrip() -> None:
    data = {
        "seed": "Manchester Orchestra",
        "seed_artist": {
            "id": "manchester-orchestra",
            "name": "Manchester Orchestra",
            "spotify_url": "https://open.spotify.com/artist/...",
        },
        "modern_echoes": [
            {
                "artist_name": "Echo Artist",
                "classification": "modern_echo",
                "echo_score": 90.0,
                "confidence": 0.8,
                "emergence_type": "formed_recent",
                "emergence_year": 2022,
                "emergence_resolution": {
                    "source_field": "formed_year",
                    "fallback_used": False,
                    "is_modern_window": True,
                    "window_start_year": 2021,
                    "window_end_year": 2026,
                    "note": "resolved",
                },
                "shared_tags": ["emo"],
                "shared_tag_weights": [{"tag": "emo", "weight": 1.0}],
                "component_scores": {
                    "emotional_match": 0.9,
                    "scene_match": 0.8,
                    "lyrical_match": 0.7,
                    "production_match": 0.6,
                    "vocal_match": 0.5,
                    "emerging_bonus": 1.0,
                },
                "sources": ["manual_pool"],
                "source_note": "",
                "spotify_url": "",
            }
        ],
        "bridge_artists": [],
        "metadata": {
            "reason": "no_bridge_artists_found",
            "source_status": {
                "manual_pool": {"status": "ok", "message": ""},
                "lastfm_graph": {"status": "planned", "message": "Not implemented in manual MVP"},
                "musicbrainz": {"status": "planned", "message": "Not implemented in manual MVP"},
                "spotify": {"status": "planned", "message": "Not implemented in manual MVP"},
            },
        },
    }
    resp = RecommendationsResponse.model_validate(data)
    assert resp.seed == "Manchester Orchestra"
    assert resp.seed_artist.id == "manchester-orchestra"
    assert len(resp.modern_echoes) == 1
    assert len(resp.bridge_artists) == 0
    assert resp.metadata.reason == "no_bridge_artists_found"
    assert resp.metadata.source_status["manual_pool"].status == "ok"
    assert resp.metadata.source_status["lastfm_graph"].status == "planned"

    serialized = resp.model_dump(mode="json")
    assert serialized["metadata"]["reason"] == "no_bridge_artists_found"
    assert serialized["metadata"]["source_status"]["manual_pool"]["status"] == "ok"


def test_recommendation_card_defaults_image_url_and_genres() -> None:
    raw = {
        "artist_name": "Test Artist",
        "classification": "modern_echo",
        "echo_score": 85.0,
        "confidence": 0.75,
        "emergence_type": "formed_recent",
        "emergence_year": 2022,
        "emergence_resolution": {
            "source_field": "formed_year",
            "fallback_used": False,
            "is_modern_window": True,
            "window_start_year": 2021,
            "window_end_year": 2026,
            "note": "resolved",
        },
        "shared_tags": ["emo"],
        "shared_tag_weights": [{"tag": "emo", "weight": 1.0}],
        "component_scores": {
            "emotional_match": 0.0,
            "scene_match": 0.0,
            "lyrical_match": 0.0,
            "production_match": 0.0,
            "vocal_match": 0.0,
            "emerging_bonus": 0.0,
        },
        "sources": ["manual_pool"],
        "source_note": "",
        "spotify_url": "",
    }
    card = RecommendationCard.model_validate(raw)
    assert card.image_url == ""
    assert card.genres == []
    serialized = card.model_dump(mode="json")
    assert serialized["image_url"] == ""
    assert serialized["genres"] == []


def test_seed_artist_defaults_image_url_and_genres() -> None:
    raw = {"id": "test", "name": "Test", "spotify_url": ""}
    sa = SeedArtist.model_validate(raw)
    assert sa.image_url == ""
    assert sa.genres == []
    serialized = sa.model_dump(mode="json")
    assert serialized["image_url"] == ""
    assert serialized["genres"] == []
