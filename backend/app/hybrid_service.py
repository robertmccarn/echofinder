from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any

from .hybrid_db import HybridStore
from .hybrid_model import (
    CURATED_PAIRS,
    HybridScore,
    activity_score,
    centered_vector,
    compute_attribute_vector,
    cosine_similarity,
    explain_top_relationships,
    genre_scene_similarity,
    newer_gate,
    novelty_score,
    rank_similarity,
    rank_vector,
    raw_vector,
    relational_similarity,
    relational_vector,
    success_gate,
)
from .reco_config import RecoConfig


@dataclass
class HybridRuntime:
    config: RecoConfig
    store: HybridStore | None

    @classmethod
    def from_config(cls, config: RecoConfig) -> HybridRuntime:
        store = HybridStore.from_env()
        if store:
            store.ensure_schema()
            store.insert_pair_defs(config.pair_set_id, CURATED_PAIRS)
        return cls(config=config, store=store)

    def _pair_defs(self) -> list[tuple[str, str, float]]:
        if not self.store:
            return CURATED_PAIRS
        rows = self.store.fetch_pair_defs(self.config.pair_set_id)
        if not rows:
            return CURATED_PAIRS
        return [(r["attribute_i"], r["attribute_j"], float(r["weight"])) for r in rows]

    def compute_signature(self, artist_id: str, record: dict[str, Any]) -> dict[str, Any]:
        attrs = compute_attribute_vector(record)
        raw = raw_vector(attrs)
        centered = centered_vector(raw)
        pair_defs = self._pair_defs()
        rel = relational_vector(attrs, self.config.epsilon, pair_defs)
        rank = rank_vector(raw)

        if self.store:
            self.store.upsert_artist_signature(
                artist_id=artist_id,
                raw_vector=raw,
                centered_vector=centered,
                relational_vector=rel,
                rank_vector=rank,
                attribute_version=self.config.model_version,
                pair_set_id=self.config.pair_set_id,
                epsilon=self.config.epsilon,
            )
        return {
            "artist_id": artist_id,
            "attrs": attrs,
            "raw_vector": raw,
            "centered_vector": centered,
            "relational_vector": rel,
            "rank_vector": rank,
        }

    def score_candidate_shadow(
        self,
        seed_profile: dict[str, Any],
        candidate_profile: dict[str, Any],
        known_names: set[str] | None = None,
    ) -> HybridScore:
        now_year = datetime.now().year
        known_names = known_names or set()
        pair_defs = self._pair_defs()

        newer_ok, newer_reason = newer_gate(candidate_profile, now_year, self.config)
        seed_attrs = seed_profile["attrs"]
        cand_attrs = candidate_profile["attrs"]
        success_ok, success_reason = success_gate(candidate_profile, cand_attrs, self.config)

        if not newer_ok:
            return HybridScore(
                final_score=0.0,
                components={k: 0.0 for k in ("relational", "raw", "rank", "genre_scene", "activity", "novelty")},
                explanation={"top_shared_relationships": []},
                gate_ok=False,
                gate_reason=newer_reason,
            )
        if not success_ok:
            return HybridScore(
                final_score=0.0,
                components={k: 0.0 for k in ("relational", "raw", "rank", "genre_scene", "activity", "novelty")},
                explanation={"top_shared_relationships": []},
                gate_ok=False,
                gate_reason=success_reason,
            )

        rel = relational_similarity(seed_profile["relational_vector"], candidate_profile["relational_vector"], pair_defs)
        raw = cosine_similarity(seed_profile["raw_vector"], candidate_profile["raw_vector"])
        rank = rank_similarity(seed_profile["rank_vector"], candidate_profile["rank_vector"])
        gsp = genre_scene_similarity(seed_profile.get("tags", []), candidate_profile.get("tags", []))
        act = activity_score(candidate_profile, now_year, self.config)
        nov = novelty_score(candidate_profile.get("name", ""), known_names)

        w = self.config.weights
        final_score = (
            w.relational * rel
            + w.raw * raw
            + w.rank * rank
            + w.genre_scene * gsp
            + w.activity * act
            + w.novelty * nov
        )
        explanation = {
            "seed_artist": seed_profile.get("name", ""),
            "candidate_artist": candidate_profile.get("name", ""),
            "top_shared_relationships": explain_top_relationships(
                seed_profile["relational_vector"],
                candidate_profile["relational_vector"],
                pair_defs,
            ),
        }
        components = {
            "relational": rel,
            "raw": raw,
            "rank": rank,
            "genre_scene": gsp,
            "activity": act,
            "novelty": nov,
        }
        if self.store:
            self.store.write_similarity_edge(
                source_artist_id=seed_profile["artist_id"],
                target_artist_id=candidate_profile["artist_id"],
                components=components,
                final_score=final_score,
                explanation=explanation,
                model_version=self.config.model_version,
            )
        return HybridScore(
            final_score=round(final_score, 6),
            components={k: round(v, 6) for k, v in components.items()},
            explanation=explanation,
            gate_ok=True,
            gate_reason="",
        )

    def write_shadow_artifact(
        self,
        seed_artist_id: str,
        seed_name: str,
        legacy_names: list[str],
        hybrid_names: list[str],
    ) -> None:
        if not self.store:
            return
        topk = min(5, len(legacy_names), len(hybrid_names))
        overlap = 0.0
        if topk > 0:
            overlap = len(set(legacy_names[:topk]) & set(hybrid_names[:topk])) / topk
        novelty_delta = (len(set(hybrid_names) - set(legacy_names)) / max(len(hybrid_names), 1)) - (
            len(set(legacy_names) - set(hybrid_names)) / max(len(legacy_names), 1)
        )
        diversity_delta = len(set(hybrid_names)) / max(len(hybrid_names), 1) - len(set(legacy_names)) / max(len(legacy_names), 1)
        false_flags: list[str] = []
        self.store.write_shadow_artifact(
            seed_artist_id=seed_artist_id,
            seed_name=seed_name,
            legacy_count=len(legacy_names),
            hybrid_count=len(hybrid_names),
            topk_overlap=round(overlap, 6),
            novelty_delta=round(novelty_delta, 6),
            diversity_delta=round(diversity_delta, 6),
            false_positive_flags=false_flags,
            model_version=self.config.model_version,
        )

