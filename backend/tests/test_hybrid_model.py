from __future__ import annotations

from backend.app.hybrid_model import (
    CURATED_PAIRS,
    compute_attribute_vector,
    newer_gate,
    rank_vector,
    raw_vector,
    relational_vector,
    success_gate,
)
from backend.app.reco_config import load_reco_config


def test_relational_vector_deterministic() -> None:
    record = {
        "genres": ["indie rock", "emo", "post-hardcore"],
        "tags": ["indie rock", "melancholy", "narrative"],
        "emotional_tones": ["intense", "vulnerable"],
        "lyrical_themes": ["existential doubt"],
    }
    attrs = compute_attribute_vector(record)
    rel_a = relational_vector(attrs, 0.05, CURATED_PAIRS)
    rel_b = relational_vector(attrs, 0.05, CURATED_PAIRS)
    assert rel_a == rel_b
    assert len(rel_a) == len(CURATED_PAIRS)


def test_rank_vector_stable_length() -> None:
    attrs = {"folkiness": 0.2, "rootsiness": 0.8}
    vec = raw_vector(
        {
            "folkiness": 0.2,
            "rootsiness": 0.8,
            "indie_rockness": 0.1,
            "pop_accessibility": 0.3,
            "acoustic_texture": 0.4,
            "electronic_texture": 0.1,
            "orchestral_texture": 0.1,
            "rock_energy": 0.6,
            "danceability": 0.1,
            "aggression": 0.3,
            "vocal_intimacy": 0.5,
            "vocal_theatricality": 0.2,
            "lyrical_density": 0.4,
            "narrative_specificity": 0.5,
            "irony_archness": 0.1,
            "melancholy": 0.7,
            "earnestness": 0.6,
            "whimsy": 0.1,
            "production_polish": 0.4,
            "lofi_rawness": 0.2,
            "scene_specificity": 0.1,
            "nostalgia_marker": 0.3,
            "experimentalism": 0.2,
            "genre_hybridity": 0.2,
            "obscurity_underground": 0.5,
            "darkness": 0.6,
            "warmth": 0.2,
            "rhythmic_complexity": 0.4,
            "arrangement_density": 0.5,
            "retro_modern_balance": 0.2,
        }
    )
    ranks = rank_vector(vec)
    assert len(ranks) == len(vec)
    assert min(ranks) == 1
    assert max(ranks) == len(vec)


def test_newer_and_success_gates() -> None:
    cfg = load_reco_config()
    record_ok = {
        "first_known_year": 2023,
        "emergence_year": 2025,
        "release_count": 2,
    }
    attrs_ok = {"folkiness": 0.5, "rock_energy": 0.3, "melancholy": 0.2, "lyrical_density": 0.6}
    ok_newer, _ = newer_gate(record_ok, 2026, cfg)
    ok_success, _ = success_gate(record_ok, attrs_ok, cfg)
    assert ok_newer
    assert ok_success

    record_old = {"first_known_year": 2000, "emergence_year": 2001, "release_count": 1}
    bad_newer, reason = newer_gate(record_old, 2026, cfg)
    assert not bad_newer
    assert reason in {"first_release_outside_window", "not_recently_active"}

