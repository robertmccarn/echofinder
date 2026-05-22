import json
from pathlib import Path

from backend.app.scoring import (
    calculate_tag_similarity,
    get_weighted_shared_tags,
    normalize_tag,
    normalize_tags,
)


def _load_fixture() -> dict:
    path = Path(__file__).parent / "fixtures" / "tag_variants.json"
    with path.open(encoding="utf-8") as fh:
        return json.load(fh)


def test_normalization_rules_are_applied() -> None:
    fixture = _load_fixture()
    seed_tags = set(fixture["seed_tags"])
    normalized = normalize_tags(seed_tags)
    assert normalized == {"indie rock", "post-hardcore", "emo"}


def test_similarity_is_stable_for_tag_variants() -> None:
    fixture = _load_fixture()
    seed_tags = set(fixture["seed_tags"])
    candidate_variant_tags = set(fixture["candidate_tags_variants"])
    candidate_canonical_tags = set(fixture["candidate_tags_canonical"])

    variant_similarity = calculate_tag_similarity(seed_tags, candidate_variant_tags)
    canonical_similarity = calculate_tag_similarity(seed_tags, candidate_canonical_tags)

    assert variant_similarity == 1.0
    assert canonical_similarity == 1.0
    assert variant_similarity == canonical_similarity


def test_shared_tag_explanations_include_weights() -> None:
    fixture = _load_fixture()
    seed_tags = set(fixture["seed_tags"])
    candidate_variant_tags = set(fixture["candidate_tags_variants"])

    shared = get_weighted_shared_tags(seed_tags, candidate_variant_tags)
    assert [item["tag"] for item in shared] == ["emo", "indie rock", "post-hardcore"]
    assert all(item["weight"] == 0.333 for item in shared)


def test_normalize_tag_removes_stop_words() -> None:
    assert normalize_tag("music") == "music"
    assert "music" not in normalize_tags({"music", "indie rock"})


def test_normalize_tag_handles_special_chars() -> None:
    assert normalize_tag("EMO!!!") == "emo"
    assert normalize_tag("post-hardcore") == "post-hardcore"
    assert normalize_tag(" alt-country ") == "alt-country"


def test_similarity_returns_zero_for_empty_input() -> None:
    assert calculate_tag_similarity(set(), {"indie rock"}) == 0.0
    assert calculate_tag_similarity({"indie rock"}, set()) == 0.0
    assert calculate_tag_similarity(set(), set()) == 0.0
