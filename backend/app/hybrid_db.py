from __future__ import annotations

import json
import os
import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import (
    JSON,
    Column,
    Date,
    DateTime,
    Float,
    Integer,
    MetaData,
    String,
    Table,
    Text,
    and_,
    create_engine,
    select,
)


metadata = MetaData()

artists = Table(
    "reco_artists",
    metadata,
    Column("artist_id", String, primary_key=True),
    Column("canonical_name", Text, nullable=False),
    Column("country", Text, nullable=True),
    Column("formed_year", Integer, nullable=True),
    Column("first_release_date", Date, nullable=True),
    Column("active_status", Text, nullable=True),
    Column("image_url", Text, nullable=True),
    Column("created_at", DateTime, default=datetime.utcnow),
    Column("updated_at", DateTime, default=datetime.utcnow),
)

artist_external_ids = Table(
    "reco_artist_external_ids",
    metadata,
    Column("artist_id", String, nullable=False),
    Column("source", String(64), nullable=False),
    Column("external_id", String(255), nullable=False),
    Column("external_url", Text, nullable=True),
)

attribute_definitions = Table(
    "reco_attribute_definitions",
    metadata,
    Column("attribute_id", Integer, primary_key=True, autoincrement=True),
    Column("name", String(128), nullable=False, unique=True),
    Column("category", String(64), nullable=False),
    Column("description", Text, nullable=True),
    Column("default_weight", Float, nullable=False, default=1.0),
    Column("is_active", Integer, nullable=False, default=1),
)

artist_attributes = Table(
    "reco_artist_attributes",
    metadata,
    Column("artist_id", String, nullable=False),
    Column("attribute_name", String(128), nullable=False),
    Column("score", Float, nullable=False),
    Column("confidence", Float, nullable=True),
    Column("source_method", Text, nullable=True),
    Column("evidence", JSON, nullable=True),
    Column("updated_at", DateTime, default=datetime.utcnow),
)

signature_pair_definitions = Table(
    "reco_signature_pair_definitions",
    metadata,
    Column("pair_id", Integer, primary_key=True, autoincrement=True),
    Column("pair_set_id", String(64), nullable=False),
    Column("attribute_i", String(128), nullable=False),
    Column("attribute_j", String(128), nullable=False),
    Column("weight", Float, nullable=False, default=1.0),
    Column("is_active", Integer, nullable=False, default=1),
)

artist_signature_vectors = Table(
    "reco_artist_signature_vectors",
    metadata,
    Column("artist_id", String, primary_key=True),
    Column("raw_vector", JSON, nullable=False),
    Column("centered_vector", JSON, nullable=False),
    Column("relational_vector", JSON, nullable=False),
    Column("rank_vector", JSON, nullable=False),
    Column("attribute_version", String(64), nullable=False),
    Column("pair_set_id", String(64), nullable=False),
    Column("epsilon", Float, nullable=False, default=0.05),
    Column("created_at", DateTime, default=datetime.utcnow),
)

artist_similarity_edges = Table(
    "reco_artist_similarity_edges",
    metadata,
    Column("edge_id", String, primary_key=True),
    Column("source_artist_id", String, nullable=False),
    Column("target_artist_id", String, nullable=False),
    Column("relational_similarity", Float, nullable=False),
    Column("raw_similarity", Float, nullable=False),
    Column("rank_similarity", Float, nullable=False),
    Column("genre_scene_similarity", Float, nullable=False),
    Column("activity_score", Float, nullable=False),
    Column("novelty_score", Float, nullable=False),
    Column("final_score", Float, nullable=False),
    Column("explanation", JSON, nullable=False),
    Column("model_version", String(64), nullable=False),
    Column("created_at", DateTime, default=datetime.utcnow),
)

shadow_comparison_artifacts = Table(
    "reco_shadow_comparison_artifacts",
    metadata,
    Column("artifact_id", String, primary_key=True),
    Column("seed_artist_id", String, nullable=False),
    Column("seed_name", String(255), nullable=False),
    Column("legacy_count", Integer, nullable=False),
    Column("hybrid_count", Integer, nullable=False),
    Column("topk_overlap", Float, nullable=False),
    Column("novelty_delta", Float, nullable=False),
    Column("diversity_delta", Float, nullable=False),
    Column("false_positive_flags", JSON, nullable=False),
    Column("model_version", String(64), nullable=False),
    Column("created_at", DateTime, default=datetime.utcnow),
)


class HybridStore:
    def __init__(self, database_url: str):
        self.engine = create_engine(database_url, future=True)

    @classmethod
    def from_env(cls) -> HybridStore | None:
        url = os.getenv("DATABASE_URL", "").strip()
        if not url:
            return None
        return cls(url)

    def ensure_schema(self) -> None:
        metadata.create_all(self.engine)

    def upsert_artist_signature(
        self,
        artist_id: str,
        raw_vector: list[float],
        centered_vector: list[float],
        relational_vector: list[float],
        rank_vector: list[int],
        attribute_version: str,
        pair_set_id: str,
        epsilon: float,
    ) -> None:
        with self.engine.begin() as conn:
            existing = conn.execute(
                select(artist_signature_vectors.c.artist_id).where(artist_signature_vectors.c.artist_id == artist_id)
            ).first()
            payload = {
                "artist_id": artist_id,
                "raw_vector": raw_vector,
                "centered_vector": centered_vector,
                "relational_vector": relational_vector,
                "rank_vector": rank_vector,
                "attribute_version": attribute_version,
                "pair_set_id": pair_set_id,
                "epsilon": epsilon,
                "created_at": datetime.utcnow(),
            }
            if existing:
                conn.execute(
                    artist_signature_vectors.update()
                    .where(artist_signature_vectors.c.artist_id == artist_id)
                    .values(**payload)
                )
            else:
                conn.execute(artist_signature_vectors.insert().values(**payload))

    def fetch_signature(self, artist_id: str, pair_set_id: str) -> dict[str, Any] | None:
        with self.engine.begin() as conn:
            row = conn.execute(
                select(artist_signature_vectors).where(
                    and_(
                        artist_signature_vectors.c.artist_id == artist_id,
                        artist_signature_vectors.c.pair_set_id == pair_set_id,
                    )
                )
            ).mappings().first()
            return dict(row) if row else None

    def fetch_pair_defs(self, pair_set_id: str) -> list[dict[str, Any]]:
        with self.engine.begin() as conn:
            rows = (
                conn.execute(
                    select(signature_pair_definitions).where(
                        and_(
                            signature_pair_definitions.c.pair_set_id == pair_set_id,
                            signature_pair_definitions.c.is_active == 1,
                        )
                    )
                )
                .mappings()
                .all()
            )
            return [dict(r) for r in rows]

    def insert_pair_defs(self, pair_set_id: str, pairs: list[tuple[str, str, float]]) -> None:
        with self.engine.begin() as conn:
            existing = conn.execute(
                select(signature_pair_definitions.c.pair_id).where(signature_pair_definitions.c.pair_set_id == pair_set_id)
            ).first()
            if existing:
                return
            for a_i, a_j, weight in pairs:
                conn.execute(
                    signature_pair_definitions.insert().values(
                        pair_set_id=pair_set_id,
                        attribute_i=a_i,
                        attribute_j=a_j,
                        weight=weight,
                        is_active=1,
                    )
                )

    def write_similarity_edge(
        self,
        source_artist_id: str,
        target_artist_id: str,
        components: dict[str, float],
        final_score: float,
        explanation: dict[str, Any],
        model_version: str,
    ) -> None:
        with self.engine.begin() as conn:
            conn.execute(
                artist_similarity_edges.insert().values(
                    edge_id=str(uuid.uuid4()),
                    source_artist_id=source_artist_id,
                    target_artist_id=target_artist_id,
                    relational_similarity=components["relational"],
                    raw_similarity=components["raw"],
                    rank_similarity=components["rank"],
                    genre_scene_similarity=components["genre_scene"],
                    activity_score=components["activity"],
                    novelty_score=components["novelty"],
                    final_score=final_score,
                    explanation=explanation,
                    model_version=model_version,
                    created_at=datetime.utcnow(),
                )
            )

    def write_shadow_artifact(
        self,
        seed_artist_id: str,
        seed_name: str,
        legacy_count: int,
        hybrid_count: int,
        topk_overlap: float,
        novelty_delta: float,
        diversity_delta: float,
        false_positive_flags: list[str],
        model_version: str,
    ) -> None:
        with self.engine.begin() as conn:
            conn.execute(
                shadow_comparison_artifacts.insert().values(
                    artifact_id=str(uuid.uuid4()),
                    seed_artist_id=seed_artist_id,
                    seed_name=seed_name,
                    legacy_count=legacy_count,
                    hybrid_count=hybrid_count,
                    topk_overlap=topk_overlap,
                    novelty_delta=novelty_delta,
                    diversity_delta=diversity_delta,
                    false_positive_flags=false_positive_flags,
                    model_version=model_version,
                    created_at=datetime.utcnow(),
                )
            )

