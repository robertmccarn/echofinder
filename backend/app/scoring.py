from __future__ import annotations

from dataclasses import dataclass


MODERN_ECHO_MIN_SCORE = 30.0
BRIDGE_MIN_SCORE = 20.0


@dataclass(frozen=True)
class ScoreResult:
    echo_score: float
    confidence: float
    shared_tags: list[str]
    classification: str


def calculate_tag_similarity(seed_tags: set[str], candidate_tags: set[str]) -> float:
    if not seed_tags or not candidate_tags:
        return 0.0
    intersection = seed_tags.intersection(candidate_tags)
    union = seed_tags.union(candidate_tags)
    return len(intersection) / len(union)


def calculate_echo_score(
    seed_tags: set[str],
    candidate_tags: set[str],
    lineage_match: float,
    is_modern_window: bool,
) -> float:
    tag_similarity = calculate_tag_similarity(seed_tags, candidate_tags)
    emergence_bonus = 30.0 if is_modern_window else 0.0
    score = (tag_similarity * 100.0 * 0.5) + (lineage_match * 100.0 * 0.2) + emergence_bonus
    return round(score, 1)


def classify_recommendation(is_modern_window: bool, echo_score: float) -> str:
    if is_modern_window and echo_score >= MODERN_ECHO_MIN_SCORE:
        return "modern_echo"
    if (not is_modern_window) and echo_score >= BRIDGE_MIN_SCORE:
        return "bridge_artist"
    return "excluded"


def calculate_confidence(seed_tags: set[str], candidate_tags: set[str], lineage_match: float) -> float:
    # Confidence is intentionally simple and transparent for MVP:
    # blend tag overlap (70%) with source lineage strength (30%).
    tag_similarity = calculate_tag_similarity(seed_tags, candidate_tags)
    confidence = (tag_similarity * 0.7) + (lineage_match * 0.3)
    return round(confidence, 3)


def score_candidate(
    seed_tags: set[str],
    candidate_tags: set[str],
    lineage_match: float,
    is_modern_window: bool,
) -> ScoreResult:
    shared_tags = sorted(seed_tags.intersection(candidate_tags))
    echo_score = calculate_echo_score(seed_tags, candidate_tags, lineage_match, is_modern_window)
    confidence = calculate_confidence(seed_tags, candidate_tags, lineage_match)
    classification = classify_recommendation(is_modern_window, echo_score)
    return ScoreResult(
        echo_score=echo_score,
        confidence=confidence,
        shared_tags=shared_tags,
        classification=classification,
    )
