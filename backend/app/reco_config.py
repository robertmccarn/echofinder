from __future__ import annotations

import os
from dataclasses import dataclass


@dataclass(frozen=True)
class RecoWeights:
    relational: float = 0.45
    raw: float = 0.20
    rank: float = 0.15
    genre_scene: float = 0.10
    activity: float = 0.05
    novelty: float = 0.05


@dataclass(frozen=True)
class GateConfig:
    # first release must be within this many years from current year
    first_release_window_years: int = 8
    # must have activity in this window
    recent_activity_years: int = 2
    # release + metadata coverage floor
    min_release_count: int = 1
    min_coverage_score: float = 0.25


@dataclass(frozen=True)
class RecoConfig:
    mode: str
    model_version: str
    epsilon: float
    pair_set_id: str
    weights: RecoWeights
    gates: GateConfig


def load_reco_config() -> RecoConfig:
    mode = os.getenv("RECO_ENGINE_MODE", "legacy").strip().lower()
    if mode not in {"legacy", "shadow", "hybrid_primary"}:
        mode = "legacy"

    return RecoConfig(
        mode=mode,
        model_version=os.getenv("RECO_MODEL_VERSION", "hybrid-v1"),
        epsilon=float(os.getenv("RECO_EPSILON", "0.05")),
        pair_set_id=os.getenv("RECO_PAIR_SET_ID", "default-v1"),
        weights=RecoWeights(
            relational=float(os.getenv("RECO_WEIGHT_RELATIONAL", "0.45")),
            raw=float(os.getenv("RECO_WEIGHT_RAW", "0.20")),
            rank=float(os.getenv("RECO_WEIGHT_RANK", "0.15")),
            genre_scene=float(os.getenv("RECO_WEIGHT_GENRE_SCENE", "0.10")),
            activity=float(os.getenv("RECO_WEIGHT_ACTIVITY", "0.05")),
            novelty=float(os.getenv("RECO_WEIGHT_NOVELTY", "0.05")),
        ),
        gates=GateConfig(
            first_release_window_years=int(os.getenv("RECO_FIRST_RELEASE_WINDOW_YEARS", "8")),
            recent_activity_years=int(os.getenv("RECO_RECENT_ACTIVITY_YEARS", "2")),
            min_release_count=int(os.getenv("RECO_MIN_RELEASE_COUNT", "1")),
            min_coverage_score=float(os.getenv("RECO_MIN_COVERAGE_SCORE", "0.25")),
        ),
    )

