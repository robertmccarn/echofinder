from __future__ import annotations

from pydantic import BaseModel, Field


class EmergenceResolutionOut(BaseModel):
    source_field: str | None
    fallback_used: bool
    is_modern_window: bool
    window_start_year: int
    window_end_year: int
    note: str


class ComponentScoresOut(BaseModel):
    emotional_match: float = 0.0
    scene_match: float = 0.0
    lyrical_match: float = 0.0
    production_match: float = 0.0
    vocal_match: float = 0.0
    emerging_bonus: float = 0.0


class SharedTagWeight(BaseModel):
    tag: str
    weight: float


class RecommendationCard(BaseModel):
    artist_name: str
    classification: str
    echo_score: float
    confidence: float
    emergence_type: str
    emergence_year: int | None
    emergence_resolution: EmergenceResolutionOut
    shared_tags: list[str]
    shared_tag_weights: list[SharedTagWeight]
    component_scores: ComponentScoresOut
    sources: list[str]
    source_note: str
    spotify_url: str


class SeedArtist(BaseModel):
    id: str
    name: str
    spotify_url: str


class RecommendationsResponse(BaseModel):
    seed: str
    seed_artist: SeedArtist
    modern_echoes: list[RecommendationCard]
    bridge_artists: list[RecommendationCard]


class ErrorDetail(BaseModel):
    code: str
    message: str


class ErrorResponse(BaseModel):
    error: ErrorDetail
