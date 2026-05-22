from __future__ import annotations

import json
from pathlib import Path

from backend.app.scoring import (
    calculate_tag_similarity,
    get_weighted_shared_tags,
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
