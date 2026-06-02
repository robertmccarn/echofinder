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


class SourceStatusOut(BaseModel):
    status: str
    message: str = ""


class ResponseMetadataOut(BaseModel):
    reason: str = ""
    source_status: dict[str, SourceStatusOut] = Field(default_factory=dict)
    model_version: str = "legacy-v1"
    shadow_score_summary: dict[str, float | int | str] = Field(default_factory=dict)
    gating_reason: str = ""


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
    image_url: str = ""
    genres: list[str] = Field(default_factory=list)


class SeedArtist(BaseModel):
    id: str
    name: str
    spotify_url: str
    image_url: str = ""
    genres: list[str] = Field(default_factory=list)


class RecommendationsResponse(BaseModel):
    seed: str
    seed_artist: SeedArtist
    modern_echoes: list[RecommendationCard]
    bridge_artists: list[RecommendationCard]
    metadata: ResponseMetadataOut = Field(default_factory=ResponseMetadataOut)


class ShadowCandidateDiagnostic(BaseModel):
    artist_name: str
    gate_ok: bool
    gate_reason: str = ""
    final_score: float = 0.0
    components: dict[str, float] = Field(default_factory=dict)
    explanation: dict = Field(default_factory=dict)


class DiagnosticsResponse(BaseModel):
    seed: str
    model_version: str
    mode: str
    legacy_count: int
    hybrid_count: int
    candidates: list[ShadowCandidateDiagnostic] = Field(default_factory=list)


class ErrorDetail(BaseModel):
    code: str
    message: str


class ErrorResponse(BaseModel):
    error: ErrorDetail
