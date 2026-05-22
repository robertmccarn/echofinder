from backend.app.scoring import (
    calculate_echo_score,
    calculate_confidence,
    calculate_dimension_echo_score,
    calculate_dimension_confidence,
    classify_recommendation,
    ComponentScores,
    compute_component_scores,
    score_candidate,
    score_dimension_candidate,
)


def test_classify_modern_echo_when_in_window_and_score_high() -> None:
    result = classify_recommendation(is_modern_window=True, echo_score=50.0)
    assert result == "modern_echo"


def test_classify_modern_echo_at_threshold() -> None:
    result = classify_recommendation(is_modern_window=True, echo_score=30.0)
    assert result == "modern_echo"


def test_classify_modern_echo_excluded_below_threshold() -> None:
    result = classify_recommendation(is_modern_window=True, echo_score=29.9)
    assert result == "excluded"


def test_classify_bridge_artist_when_outside_window_and_score_high() -> None:
    result = classify_recommendation(is_modern_window=False, echo_score=25.0)
    assert result == "bridge_artist"


def test_classify_bridge_artist_at_threshold() -> None:
    result = classify_recommendation(is_modern_window=False, echo_score=20.0)
    assert result == "bridge_artist"


def test_classify_bridge_artist_excluded_below_threshold() -> None:
    result = classify_recommendation(is_modern_window=False, echo_score=19.9)
    assert result == "excluded"


def test_classify_outside_window_never_modern_echo() -> None:
    result = classify_recommendation(is_modern_window=False, echo_score=100.0)
    assert result == "bridge_artist"


def test_calculate_echo_score_includes_emergence_bonus() -> None:
    seed = {"indie rock", "emo"}
    candidate = {"indie rock", "emo", "alternative"}

    modern_score = calculate_echo_score(seed, candidate, lineage_match=0.9, is_modern_window=True)
    legacy_score = calculate_echo_score(seed, candidate, lineage_match=0.9, is_modern_window=False)
    assert modern_score > legacy_score
    assert modern_score == round(legacy_score + 30.0, 1)


def test_calculate_echo_score_zero_similarity() -> None:
    seed = {"indie rock"}
    candidate = {"jazz"}
    score = calculate_echo_score(seed, candidate, lineage_match=0.0, is_modern_window=False)
    assert score == 0.0


def test_calculate_confidence_returns_consistent_values() -> None:
    seed = {"indie rock", "emo"}
    candidate = {"indie rock", "emo", "alternative"}
    confidence = calculate_confidence(seed, candidate, lineage_match=0.9)
    assert 0.0 <= confidence <= 1.0


def test_calculate_confidence_zero_when_no_overlap() -> None:
    seed = {"indie rock"}
    candidate = {"jazz"}
    confidence = calculate_confidence(seed, candidate, lineage_match=0.0)
    assert confidence == 0.0


def test_score_candidate_modern_echo() -> None:
    seed = {"indie rock", "emo"}
    candidate = {"indie rock", "emo"}
    result = score_candidate(
        seed_tags=seed,
        candidate_tags=candidate,
        lineage_match=0.9,
        is_modern_window=True,
    )
    assert result.classification == "modern_echo"
    assert result.echo_score > 0.0
    assert result.confidence > 0.0
    assert "indie rock" in result.shared_tags
    assert "emo" in result.shared_tags


def test_score_candidate_bridge_artist() -> None:
    seed = {"indie rock", "emo"}
    candidate = {"indie rock", "emo"}
    result = score_candidate(
        seed_tags=seed,
        candidate_tags=candidate,
        lineage_match=0.9,
        is_modern_window=False,
    )
    assert result.classification == "bridge_artist"


def test_score_candidate_excluded() -> None:
    seed = {"indie rock", "emo"}
    candidate = {"jazz", "classical"}
    result = score_candidate(
        seed_tags=seed,
        candidate_tags=candidate,
        lineage_match=0.0,
        is_modern_window=False,
    )
    assert result.classification == "excluded"


def test_score_candidate_shared_tag_weights() -> None:
    seed = {"indie rock", "emo", "post-hardcore"}
    candidate = {"indie rock", "emo", "post-hardcore"}
    result = score_candidate(
        seed_tags=seed,
        candidate_tags=candidate,
        lineage_match=0.9,
        is_modern_window=True,
    )
    assert len(result.shared_tag_weights) == 3
    assert all("tag" in item and "weight" in item for item in result.shared_tag_weights)


# --- Dimension-based scoring tests ---


def test_component_scores_all_match() -> None:
    seed_emotional = ["cathartic", "introspective"]
    seed_lyrical = ["existential doubt", "relationships"]
    seed_production = "layered dynamic builds"
    seed_vocal = "earnest tenor"
    seed_scene = "emo revival indie"
    candidate: dict = {
        "emotional_tones": ["cathartic", "introspective"],
        "lyrical_themes": ["existential doubt", "relationships"],
        "production_style": "layered dynamic builds",
        "vocal_style": "earnest tenor",
        "scene_lineage": "emo revival indie",
    }
    cs = compute_component_scores(
        seed_emotional_tones=seed_emotional,
        seed_lyrical_themes=seed_lyrical,
        seed_production_style=seed_production,
        seed_vocal_style=seed_vocal,
        seed_scene_lineage=seed_scene,
        candidate=candidate,
        is_modern_window=True,
    )
    assert cs.emotional_match == 1.0
    assert cs.lyrical_match == 1.0
    assert cs.production_match == 1.0
    assert cs.vocal_match == 1.0
    assert cs.scene_match == 1.0
    assert cs.emerging_bonus == 1.0


def test_component_scores_no_match() -> None:
    seed_emotional = ["cathartic", "introspective"]
    seed_lyrical = ["existential doubt", "relationships"]
    seed_production = "layered dynamic builds"
    seed_vocal = "earnest tenor"
    seed_scene = "emo revival"
    candidate: dict = {
        "emotional_tones": ["whimsical"],
        "lyrical_themes": ["folklore"],
        "production_style": "acoustic orchestral",
        "vocal_style": "nasal theatrical",
        "scene_lineage": "folk portland",
    }
    cs = compute_component_scores(
        seed_emotional_tones=seed_emotional,
        seed_lyrical_themes=seed_lyrical,
        seed_production_style=seed_production,
        seed_vocal_style=seed_vocal,
        seed_scene_lineage=seed_scene,
        candidate=candidate,
        is_modern_window=False,
    )
    assert cs.emotional_match == 0.0
    assert cs.lyrical_match == 0.0
    assert cs.production_match == 0.0
    assert cs.vocal_match == 0.0
    assert cs.scene_match == 0.0
    assert cs.emerging_bonus == 0.0


def test_component_scores_partial_match() -> None:
    seed_emotional = ["cathartic", "introspective", "vulnerable"]
    seed_lyrical = ["existential doubt", "relationships", "melancholy"]
    candidate: dict = {
        "emotional_tones": ["cathartic", "introspective", "whimsical"],
        "lyrical_themes": ["existential doubt", "folklore"],
        "production_style": "",
        "vocal_style": "",
        "scene_lineage": "",
    }
    cs = compute_component_scores(
        seed_emotional_tones=seed_emotional,
        seed_lyrical_themes=seed_lyrical,
        seed_production_style="",
        seed_vocal_style="",
        seed_scene_lineage="",
        candidate=candidate,
        is_modern_window=True,
    )
    assert cs.emotional_match == 0.5
    assert cs.lyrical_match == 0.25
    assert cs.production_match == 0.0
    assert cs.emerging_bonus == 1.0


def test_dimension_echo_score_perfect_match() -> None:
    cs = ComponentScores(
        emotional_match=1.0,
        scene_match=1.0,
        lyrical_match=1.0,
        production_match=1.0,
        vocal_match=1.0,
        emerging_bonus=1.0,
    )
    score = calculate_dimension_echo_score(cs)
    assert score == 100.0


def test_dimension_echo_score_modern_window_only() -> None:
    cs = ComponentScores(emerging_bonus=1.0)
    score = calculate_dimension_echo_score(cs)
    assert score == 5.0


def test_dimension_echo_score_no_match() -> None:
    cs = ComponentScores()
    score = calculate_dimension_echo_score(cs)
    assert score == 0.0


def test_dimension_confidence_all_match() -> None:
    cs = ComponentScores(
        emotional_match=1.0,
        scene_match=1.0,
        lyrical_match=1.0,
        production_match=1.0,
        vocal_match=1.0,
    )
    confidence = calculate_dimension_confidence(cs)
    assert confidence == 1.0


def test_dimension_confidence_no_match() -> None:
    cs = ComponentScores()
    confidence = calculate_dimension_confidence(cs)
    assert confidence == 0.0


def test_score_dimension_candidate_modern_echo() -> None:
    candidate: dict = {
        "emotional_tones": ["cathartic", "introspective"],
        "lyrical_themes": ["existential doubt", "relationships"],
        "production_style": "layered dynamic builds",
        "vocal_style": "earnest tenor",
        "scene_lineage": "emo revival indie",
    }
    result = score_dimension_candidate(
        seed_emotional_tones=["cathartic", "introspective"],
        seed_lyrical_themes=["existential doubt", "relationships"],
        seed_production_style="layered dynamic builds",
        seed_vocal_style="earnest tenor",
        seed_scene_lineage="emo revival indie",
        candidate=candidate,
        is_modern_window=True,
    )
    assert result.classification == "modern_echo"
    assert result.echo_score > 50.0
    assert result.confidence > 0.0
    assert result.component_scores is not None
    assert result.component_scores.emotional_match == 1.0


def test_score_dimension_candidate_bridge_artist() -> None:
    candidate: dict = {
        "emotional_tones": ["cathartic", "introspective"],
        "lyrical_themes": ["existential doubt", "relationships"],
        "production_style": "layered dynamic builds",
        "vocal_style": "earnest tenor",
        "scene_lineage": "emo revival indie",
    }
    result = score_dimension_candidate(
        seed_emotional_tones=["cathartic", "introspective"],
        seed_lyrical_themes=["existential doubt", "relationships"],
        seed_production_style="layered dynamic builds",
        seed_vocal_style="earnest tenor",
        seed_scene_lineage="emo revival indie",
        candidate=candidate,
        is_modern_window=False,
    )
    assert result.classification == "bridge_artist"
    assert result.component_scores is not None
    assert result.component_scores.emerging_bonus == 0.0


def test_score_dimension_candidate_excluded() -> None:
    candidate: dict = {
        "emotional_tones": [],
        "lyrical_themes": [],
        "production_style": "",
        "vocal_style": "",
        "scene_lineage": "",
    }
    result = score_dimension_candidate(
        seed_emotional_tones=["cathartic", "introspective"],
        seed_lyrical_themes=["existential doubt", "relationships"],
        seed_production_style="layered dynamic builds",
        seed_vocal_style="earnest tenor",
        seed_scene_lineage="emo revival indie",
        candidate=candidate,
        is_modern_window=False,
    )
    assert result.classification == "excluded"


def test_score_dimension_candidate_returns_component_scores() -> None:
    candidate: dict = {
        "emotional_tones": ["cathartic"],
        "lyrical_themes": [],
        "production_style": "",
        "vocal_style": "",
        "scene_lineage": "",
    }
    result = score_dimension_candidate(
        seed_emotional_tones=["cathartic", "introspective"],
        seed_lyrical_themes=["existential doubt", "relationships"],
        seed_production_style="layered dynamic builds",
        seed_vocal_style="earnest tenor",
        seed_scene_lineage="emo revival indie",
        candidate=candidate,
        is_modern_window=True,
    )
    assert result.component_scores is not None
    assert result.component_scores.emotional_match == 0.5


def test_api_response_includes_component_scores(monkeypatch) -> None:
    pool = [
        {
            "name": "Test Artist",
            "first_known_year": 2022,
            "formed_year": 2022,
            "active_status": True,
            "spotify_url": "",
            "monthly_listeners": 0,
            "genres": ["indie rock", "emo"],
            "emotional_tones": ["cathartic", "introspective"],
            "lyrical_themes": ["existential doubt", "relationships"],
            "production_style": "layered dynamic builds",
            "vocal_style": "earnest tenor",
            "scene_lineage": "emo revival indie",
            "curator_notes": "test",
            "recommended_legacy_matches": ["Manchester Orchestra"],
            "tags": ["indie rock", "emo"],
            "source_note": "test",
            "related_legacy_styles": ["Manchester Orchestra"],
        },
    ]
    monkeypatch.setattr("backend.app.main._load_modern_pool", lambda: pool)
    from fastapi.testclient import TestClient
    from backend.app import main as main_module

    client = TestClient(main_module.app)
    response = client.get("/recommendations/manchester-orchestra")
    assert response.status_code == 200
    card = response.json()["modern_echoes"][0]
    assert "component_scores" in card
    cs = card["component_scores"]
    assert "emotional_match" in cs
    assert "scene_match" in cs
    assert "lyrical_match" in cs
    assert "production_match" in cs
    assert "vocal_match" in cs
    assert "emerging_bonus" in cs
    assert cs["emotional_match"] > 0.0
