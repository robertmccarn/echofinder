from __future__ import annotations

from dataclasses import dataclass
import re


MODERN_ECHO_MIN_SCORE = 30.0
BRIDGE_MIN_SCORE = 20.0
TAG_ALIASES: dict[str, str] = {
    "alt rock": "alternative rock",
    "alt-rock": "alternative rock",
    "indie-rock": "indie rock",
    "post hardcore": "post-hardcore",
    "posthardcore": "post-hardcore",
    "emo rock": "emo",
    "folk-rock": "folk rock",
    "alt country": "alt-country",
}
STOP_TAGS: set[str] = {
    "music",
    "artist",
    "artists",
    "band",
    "bands",
}
_NON_WORD_RE = re.compile(r"[^\w\s-]")
_SPACE_RE = re.compile(r"\s+")


@dataclass(frozen=True)
class ScoreResult:
    echo_score: float
    confidence: float
    shared_tags: list[str]
    shared_tag_weights: list[dict[str, float | str]]
    classification: str


def normalize_tag(tag: str) -> str:
    normalized = _NON_WORD_RE.sub(" ", tag.casefold())
    normalized = _SPACE_RE.sub(" ", normalized).strip()
    normalized = TAG_ALIASES.get(normalized, normalized)
    return normalized


def normalize_tags(tags: set[str]) -> set[str]:
    normalized: set[str] = set()
    for tag in tags:
        value = normalize_tag(tag)
        if value and value not in STOP_TAGS:
            normalized.add(value)
    return normalized


def calculate_tag_similarity(seed_tags: set[str], candidate_tags: set[str]) -> float:
    normalized_seed_tags = normalize_tags(seed_tags)
    normalized_candidate_tags = normalize_tags(candidate_tags)
    if not normalized_seed_tags or not normalized_candidate_tags:
        return 0.0
    intersection = normalized_seed_tags.intersection(normalized_candidate_tags)
    union = normalized_seed_tags.union(normalized_candidate_tags)
    return len(intersection) / len(union)


def get_weighted_shared_tags(seed_tags: set[str], candidate_tags: set[str], top_n: int = 5) -> list[dict[str, float | str]]:
    normalized_seed_tags = normalize_tags(seed_tags)
    normalized_candidate_tags = normalize_tags(candidate_tags)
    shared = sorted(normalized_seed_tags.intersection(normalized_candidate_tags))
    if not shared:
        return []
    weight = round(1.0 / len(shared), 3)
    return [{"tag": tag, "weight": weight} for tag in shared[:top_n]]


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
    weighted_shared_tags = get_weighted_shared_tags(seed_tags, candidate_tags)
    shared_tags = [item["tag"] for item in weighted_shared_tags]
    echo_score = calculate_echo_score(seed_tags, candidate_tags, lineage_match, is_modern_window)
    confidence = calculate_confidence(seed_tags, candidate_tags, lineage_match)
    classification = classify_recommendation(is_modern_window, echo_score)
    return ScoreResult(
        echo_score=echo_score,
        confidence=confidence,
        shared_tags=shared_tags,
        shared_tag_weights=weighted_shared_tags,
        classification=classification,
    )
