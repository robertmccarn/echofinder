from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
import math
import re
from typing import Any

from .reco_config import RecoConfig


ATTRIBUTE_DEFINITIONS: list[tuple[str, str]] = [
    ("folkiness", "genre_lineage"),
    ("rootsiness", "genre_lineage"),
    ("indie_rockness", "genre_lineage"),
    ("pop_accessibility", "genre_lineage"),
    ("acoustic_texture", "sonic_texture"),
    ("electronic_texture", "sonic_texture"),
    ("orchestral_texture", "sonic_texture"),
    ("rock_energy", "performance"),
    ("danceability", "performance"),
    ("aggression", "performance"),
    ("vocal_intimacy", "vocal_style"),
    ("vocal_theatricality", "vocal_style"),
    ("lyrical_density", "lyrical_style"),
    ("narrative_specificity", "lyrical_style"),
    ("irony_archness", "lyrical_style"),
    ("melancholy", "emotional_tone"),
    ("earnestness", "emotional_tone"),
    ("whimsy", "emotional_tone"),
    ("production_polish", "production"),
    ("lofi_rawness", "production"),
    ("scene_specificity", "positioning"),
    ("nostalgia_marker", "positioning"),
    ("experimentalism", "innovation"),
    ("genre_hybridity", "innovation"),
    ("obscurity_underground", "market_fit"),
    ("darkness", "mood"),
    ("warmth", "mood"),
    ("rhythmic_complexity", "rhythm"),
    ("arrangement_density", "arrangement"),
    ("retro_modern_balance", "era"),
]

ATTRIBUTE_INDEX = {name: idx for idx, (name, _cat) in enumerate(ATTRIBUTE_DEFINITIONS)}


CURATED_PAIRS: list[tuple[str, str, float]] = [
    ("lyrical_density", "pop_accessibility", 1.0),
    ("folkiness", "electronic_texture", 1.0),
    ("vocal_theatricality", "vocal_intimacy", 1.0),
    ("rock_energy", "acoustic_texture", 1.0),
    ("melancholy", "danceability", 1.0),
    ("experimentalism", "production_polish", 1.0),
    ("rootsiness", "electronic_texture", 0.9),
    ("narrative_specificity", "irony_archness", 0.9),
    ("aggression", "vocal_intimacy", 0.9),
    ("indie_rockness", "pop_accessibility", 0.9),
    ("arrangement_density", "acoustic_texture", 0.8),
    ("genre_hybridity", "scene_specificity", 0.8),
    ("darkness", "warmth", 0.8),
    ("lofi_rawness", "production_polish", 1.0),
    ("orchestral_texture", "rock_energy", 0.8),
    ("retro_modern_balance", "nostalgia_marker", 0.9),
    ("obscurity_underground", "pop_accessibility", 0.9),
    ("rhythmic_complexity", "danceability", 0.8),
    ("earnestness", "irony_archness", 0.7),
    ("whimsy", "darkness", 0.7),
]


TOKEN_WEIGHTS: dict[str, dict[str, float]] = {
    "folk": {"folkiness": 1.0, "acoustic_texture": 0.6},
    "americana": {"rootsiness": 1.0, "folkiness": 0.4},
    "alt-country": {"rootsiness": 0.8, "nostalgia_marker": 0.3},
    "indie rock": {"indie_rockness": 1.0, "rock_energy": 0.5},
    "alternative rock": {"indie_rockness": 0.8, "rock_energy": 0.6},
    "emo": {"lyrical_density": 0.4, "melancholy": 0.8, "earnestness": 0.6},
    "post-hardcore": {"aggression": 0.8, "rock_energy": 0.8},
    "punk": {"aggression": 0.7, "rock_energy": 0.6},
    "pop": {"pop_accessibility": 1.0, "production_polish": 0.6},
    "math rock": {"rhythmic_complexity": 0.8, "arrangement_density": 0.5},
    "electronic": {"electronic_texture": 0.9},
    "orchestral": {"orchestral_texture": 1.0, "arrangement_density": 0.6},
    "baroque": {"orchestral_texture": 0.9, "nostalgia_marker": 0.3},
    "lo-fi": {"lofi_rawness": 0.9, "production_polish": 0.2},
    "experimental": {"experimentalism": 1.0, "genre_hybridity": 0.5},
    "narrative": {"narrative_specificity": 0.9, "lyrical_density": 0.5},
    "literary": {"lyrical_density": 0.8, "narrative_specificity": 0.7},
    "melancholy": {"melancholy": 1.0, "darkness": 0.4},
    "whimsical": {"whimsy": 1.0},
    "intense": {"rock_energy": 0.7, "aggression": 0.5},
    "urgent": {"rock_energy": 0.6, "aggression": 0.4},
    "vulnerable": {"vocal_intimacy": 0.8, "earnestness": 0.5},
    "theatrical": {"vocal_theatricality": 0.9},
    "dynamic": {"arrangement_density": 0.5, "rock_energy": 0.3},
}


def _norm_token(value: str) -> str:
    value = value.casefold()
    value = re.sub(r"[^\w\s-]", " ", value)
    value = re.sub(r"\s+", " ", value).strip()
    return value


def _iter_tokens(record: dict[str, Any]) -> list[str]:
    tokens: list[str] = []
    for field in ("genres", "tags", "emotional_tones", "lyrical_themes"):
        for item in record.get(field, []) or []:
            tokens.append(_norm_token(str(item)))
    for field in ("production_style", "vocal_style", "scene_lineage", "notes", "curator_notes"):
        val = record.get(field, "") or ""
        if val:
            tokens.append(_norm_token(str(val)))
    return tokens


def compute_attribute_vector(record: dict[str, Any]) -> dict[str, float]:
    scores = {name: 0.0 for name, _cat in ATTRIBUTE_DEFINITIONS}
    for token in _iter_tokens(record):
        for key, weight_map in TOKEN_WEIGHTS.items():
            if key in token:
                for attr, w in weight_map.items():
                    scores[attr] += w
    max_seen = max(max(scores.values()), 1.0)
    for attr in scores:
        scores[attr] = round(min(scores[attr] / max_seen, 1.0), 4)
    return scores


def raw_vector(attrs: dict[str, float]) -> list[float]:
    return [attrs[name] for name, _cat in ATTRIBUTE_DEFINITIONS]


def centered_vector(raw: list[float]) -> list[float]:
    mu = sum(raw) / max(len(raw), 1)
    return [round(v - mu, 6) for v in raw]


def relational_vector(attrs: dict[str, float], epsilon: float, pair_defs: list[tuple[str, str, float]]) -> list[float]:
    vec: list[float] = []
    for a_i, a_j, _w in pair_defs:
        v_i = attrs.get(a_i, 0.0)
        v_j = attrs.get(a_j, 0.0)
        vec.append(round(math.log((v_i + epsilon) / (v_j + epsilon)), 6))
    return vec


def rank_vector(raw: list[float]) -> list[int]:
    indexed = sorted(enumerate(raw), key=lambda x: x[1], reverse=True)
    out = [0] * len(raw)
    rank = 1
    for idx, _v in indexed:
        out[idx] = rank
        rank += 1
    return out


def cosine_similarity(a: list[float], b: list[float]) -> float:
    if not a or not b or len(a) != len(b):
        return 0.0
    dot = sum(x * y for x, y in zip(a, b))
    na = math.sqrt(sum(x * x for x in a))
    nb = math.sqrt(sum(y * y for y in b))
    if na == 0 or nb == 0:
        return 0.0
    return max(0.0, min(1.0, dot / (na * nb)))


def rank_similarity(a: list[int], b: list[int]) -> float:
    if not a or not b or len(a) != len(b):
        return 0.0
    n = len(a)
    if n < 2:
        return 1.0
    d2 = sum((x - y) ** 2 for x, y in zip(a, b))
    rho = 1 - (6 * d2) / (n * (n**2 - 1))
    return max(0.0, min(1.0, rho))


def relational_similarity(a: list[float], b: list[float], pair_defs: list[tuple[str, str, float]]) -> float:
    if not a or not b or len(a) != len(b):
        return 0.0
    weighted_sq = 0.0
    weight_sum = 0.0
    for idx, (_ai, _aj, w) in enumerate(pair_defs):
        diff = a[idx] - b[idx]
        weighted_sq += w * (diff * diff)
        weight_sum += w
    if weight_sum == 0.0:
        return 0.0
    dist = math.sqrt(weighted_sq / weight_sum)
    # map distance to similarity in (0,1]
    return 1.0 / (1.0 + dist)


def genre_scene_similarity(seed_tags: list[str], candidate_tags: list[str]) -> float:
    s = {_norm_token(x) for x in seed_tags}
    c = {_norm_token(x) for x in candidate_tags}
    if not s or not c:
        return 0.0
    inter = len(s & c)
    union = len(s | c)
    return inter / union if union else 0.0


def activity_score(record: dict[str, Any], now_year: int, gates: RecoConfig) -> float:
    years = [record.get("first_known_year"), record.get("formed_year"), record.get("debut_year"), record.get("emergence_year")]
    years = [y for y in years if isinstance(y, int)]
    if not years:
        return 0.0
    latest = max(years)
    delta = max(0, now_year - latest)
    if delta <= gates.gates.recent_activity_years:
        return 1.0
    if delta <= gates.gates.recent_activity_years + 2:
        return 0.5
    return 0.1


def novelty_score(candidate_name: str, known_names: set[str]) -> float:
    return 0.0 if candidate_name.casefold() in {n.casefold() for n in known_names} else 1.0


def newer_gate(record: dict[str, Any], now_year: int, config: RecoConfig) -> tuple[bool, str]:
    first = record.get("first_known_year") or record.get("debut_year") or record.get("formed_year")
    if not isinstance(first, int):
        return False, "missing_first_release_year"
    age = now_year - first
    if age > config.gates.first_release_window_years:
        return False, "first_release_outside_window"

    recent = max(
        y
        for y in [record.get("first_known_year"), record.get("emergence_year"), record.get("debut_year"), record.get("formed_year")]
        if isinstance(y, int)
    )
    if now_year - recent > config.gates.recent_activity_years:
        return False, "not_recently_active"
    return True, ""


def success_gate(record: dict[str, Any], attrs: dict[str, float], config: RecoConfig) -> tuple[bool, str]:
    release_count = record.get("release_count", 1)
    if release_count < config.gates.min_release_count:
        return False, "insufficient_release_count"
    non_zero = sum(1 for v in attrs.values() if v > 0.0)
    coverage = non_zero / max(len(attrs), 1)
    if coverage < config.gates.min_coverage_score:
        return False, "insufficient_coverage_score"
    return True, ""


def explain_top_relationships(
    seed_rel: list[float], cand_rel: list[float], pair_defs: list[tuple[str, str, float]], top_n: int = 3
) -> list[dict[str, Any]]:
    diffs: list[tuple[float, int]] = []
    for idx, (_a, _b, _w) in enumerate(pair_defs):
        diffs.append((abs(seed_rel[idx] - cand_rel[idx]), idx))
    diffs.sort(key=lambda x: x[0])
    out: list[dict[str, Any]] = []
    for _d, idx in diffs[:top_n]:
        a_i, a_j, _w = pair_defs[idx]
        relation = "~"
        if seed_rel[idx] - cand_rel[idx] > 0.08:
            relation = ">"
        elif cand_rel[idx] - seed_rel[idx] > 0.08:
            relation = "<"
        out.append(
            {
                "relationship": f"{a_i} {relation} {a_j}",
                "seed_strength": round(seed_rel[idx], 4),
                "candidate_strength": round(cand_rel[idx], 4),
            }
        )
    return out


@dataclass(frozen=True)
class HybridScore:
    final_score: float
    components: dict[str, float]
    explanation: dict[str, Any]
    gate_ok: bool
    gate_reason: str
