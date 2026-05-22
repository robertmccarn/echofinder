from backend.app.scoring import (
    calculate_echo_score,
    calculate_confidence,
    classify_recommendation,
    score_candidate,
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
