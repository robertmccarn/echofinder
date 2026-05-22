from __future__ import annotations

from dataclasses import dataclass, field
import re
from typing import Any


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

# --- Manual weighted model dimensions ---

DIMENSION_WEIGHTS: dict[str, float] = {
    "emotional_match": 0.35,
    "scene_match": 0.25,
    "lyrical_match": 0.15,
    "production_match": 0.10,
    "vocal_match": 0.10,
    "emerging_bonus": 0.05,
}

_LIST_FIELDS = frozenset({"emotional_tones", "lyrical_themes"})
_TEXT_FIELDS = frozenset({"production_style", "vocal_style", "scene_lineage"})


@dataclass(frozen=True)
class ComponentScores:
    emotional_match: float = 0.0
    scene_match: float = 0.0
    lyrical_match: float = 0.0
    production_match: float = 0.0
    vocal_match: float = 0.0
    emerging_bonus: float = 0.0


@dataclass(frozen=True)
class ScoreResult:
    echo_score: float
    confidence: float
    shared_tags: list[str]
    shared_tag_weights: list[dict[str, float | str]]
    classification: str
    component_scores: ComponentScores | None = None


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


# --- Manual weighted model helpers ---


def _tokenize(text: str) -> set[str]:
    return set(re.findall(r"[a-z0-9]+", text.casefold()))


def _jaccard_similarity(a: list[str], b: list[str]) -> float:
    set_a = set(a)
    set_b = set(b)
    if not set_a or not set_b:
        return 0.0
    intersection = set_a & set_b
    union = set_a | set_b
    return len(intersection) / len(union)


def _token_overlap(a: str, b: str) -> float:
    tokens_a = _tokenize(a)
    tokens_b = _tokenize(b)
    if not tokens_a or not tokens_b:
        return 0.0
    intersection = tokens_a & tokens_b
    union = tokens_a | tokens_b
    return len(intersection) / len(union)


_DIMENSION_COMPUTERS: dict[str, Any] = {}


def _init_computers() -> None:
    for field in _LIST_FIELDS:
        _DIMENSION_COMPUTERS[field] = _jaccard_similarity
    for field in _TEXT_FIELDS:
        _DIMENSION_COMPUTERS[field] = _token_overlap


_init_computers()


_DIMENSION_TO_FIELD: dict[str, str] = {
    "emotional_match": "emotional_tones",
    "scene_match": "scene_lineage",
    "lyrical_match": "lyrical_themes",
    "production_match": "production_style",
    "vocal_match": "vocal_style",
}


def compute_dimension_similarity(
    dimension: str,
    seed_values: Any,
    candidate_values: Any,
) -> float:
    field = _DIMENSION_TO_FIELD.get(dimension)
    if field is None:
        return 0.0
    computer = _DIMENSION_COMPUTERS.get(field)
    if computer is None:
        return 0.0
    return computer(seed_values, candidate_values)


def compute_component_scores(
    seed_emotional_tones: list[str],
    seed_lyrical_themes: list[str],
    seed_production_style: str,
    seed_vocal_style: str,
    seed_scene_lineage: str,
    candidate: dict[str, Any],
    is_modern_window: bool,
) -> ComponentScores:
    dim_inputs: dict[str, tuple[Any, Any]] = {
        "emotional_match": (seed_emotional_tones, candidate.get("emotional_tones", [])),
        "scene_match": (seed_scene_lineage, candidate.get("scene_lineage", "")),
        "lyrical_match": (seed_lyrical_themes, candidate.get("lyrical_themes", [])),
        "production_match": (seed_production_style, candidate.get("production_style", "")),
        "vocal_match": (seed_vocal_style, candidate.get("vocal_style", "")),
    }

    scores: dict[str, float] = {}
    for dim, (seed_val, cand_val) in dim_inputs.items():
        scores[dim] = compute_dimension_similarity(dim, seed_val, cand_val)
    scores["emerging_bonus"] = 1.0 if is_modern_window else 0.0

    return ComponentScores(
        emotional_match=scores["emotional_match"],
        scene_match=scores["scene_match"],
        lyrical_match=scores["lyrical_match"],
        production_match=scores["production_match"],
        vocal_match=scores["vocal_match"],
        emerging_bonus=scores["emerging_bonus"],
    )


def calculate_dimension_echo_score(
    component_scores: ComponentScores,
) -> float:
    raw = (
        component_scores.emotional_match * DIMENSION_WEIGHTS["emotional_match"]
        + component_scores.scene_match * DIMENSION_WEIGHTS["scene_match"]
        + component_scores.lyrical_match * DIMENSION_WEIGHTS["lyrical_match"]
        + component_scores.production_match * DIMENSION_WEIGHTS["production_match"]
        + component_scores.vocal_match * DIMENSION_WEIGHTS["vocal_match"]
        + component_scores.emerging_bonus * DIMENSION_WEIGHTS["emerging_bonus"]
    )
    return round(raw * 100.0, 1)


def calculate_dimension_confidence(
    component_scores: ComponentScores,
) -> float:
    numerator = DIMENSION_WEIGHTS["emotional_match"] + DIMENSION_WEIGHTS["scene_match"] + DIMENSION_WEIGHTS["lyrical_match"] + DIMENSION_WEIGHTS["production_match"] + DIMENSION_WEIGHTS["vocal_match"]
    weighted = (
        component_scores.emotional_match * DIMENSION_WEIGHTS["emotional_match"]
        + component_scores.scene_match * DIMENSION_WEIGHTS["scene_match"]
        + component_scores.lyrical_match * DIMENSION_WEIGHTS["lyrical_match"]
        + component_scores.production_match * DIMENSION_WEIGHTS["production_match"]
        + component_scores.vocal_match * DIMENSION_WEIGHTS["vocal_match"]
    )
    if numerator == 0.0:
        return 0.0
    return round(weighted / numerator, 3)


def score_dimension_candidate(
    seed_emotional_tones: list[str],
    seed_lyrical_themes: list[str],
    seed_production_style: str,
    seed_vocal_style: str,
    seed_scene_lineage: str,
    candidate: dict[str, Any],
    is_modern_window: bool,
) -> ScoreResult:
    cs = compute_component_scores(
        seed_emotional_tones=seed_emotional_tones,
        seed_lyrical_themes=seed_lyrical_themes,
        seed_production_style=seed_production_style,
        seed_vocal_style=seed_vocal_style,
        seed_scene_lineage=seed_scene_lineage,
        candidate=candidate,
        is_modern_window=is_modern_window,
    )
    echo_score = calculate_dimension_echo_score(cs)
    confidence = calculate_dimension_confidence(cs)
    classification = classify_recommendation(is_modern_window, echo_score)

    return ScoreResult(
        echo_score=echo_score,
        confidence=confidence,
        shared_tags=[],
        shared_tag_weights=[],
        classification=classification,
        component_scores=cs,
    )


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
