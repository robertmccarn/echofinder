from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path

from typing import Any

from fastapi import FastAPI, HTTPException, Query, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from .candidates import CandidateSourceRecord
from .emergence import compute_emergence_type, resolve_emergence_year
from .hybrid_service import HybridRuntime
from .manual_pool import ManualPoolSource
from .models import DiagnosticsResponse, ErrorResponse, RecommendationsResponse
from .reco_config import load_reco_config
from .scoring import score_dimension_candidate, normalize_tags, get_weighted_shared_tags

app = FastAPI(
    title="EchoFinder API",
    description="Initial backend API for the EchoFinder prototype.",
    version="0.2.0",
)

_RECO_CONFIG: Any | None = None
_HYBRID_RUNTIME: HybridRuntime | None = None

# Local web MVP frontend origins.
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ],
    allow_credentials=False,
    allow_methods=["GET"],
    allow_headers=["*"],
)


def _get_reco_config() -> Any:
    global _RECO_CONFIG
    if _RECO_CONFIG is None:
        _RECO_CONFIG = load_reco_config()
    return _RECO_CONFIG


def _get_hybrid_runtime() -> HybridRuntime:
    global _HYBRID_RUNTIME
    if _HYBRID_RUNTIME is None:
        reco_config = _get_reco_config()
        try:
            _HYBRID_RUNTIME = HybridRuntime.from_config(reco_config)
        except Exception:
            # Fall back to in-memory shadow mode so the legacy API remains usable
            # if Postgres is unavailable or misconfigured.
            _HYBRID_RUNTIME = HybridRuntime(config=reco_config, store=None)
    return _HYBRID_RUNTIME


@dataclass
class LegacyArtist:
    id: str
    name: str
    tags: set[str]
    spotify_url: str
    active_years: str = ""
    genres: list[str] = field(default_factory=list)
    emotional_tones: list[str] = field(default_factory=list)
    lyrical_themes: list[str] = field(default_factory=list)
    production_style: str = ""
    vocal_style: str = ""
    scene_lineage: str = ""
    notes: str = ""


def _load_legacy_artists() -> list[LegacyArtist]:
    root = Path(__file__).resolve().parents[2]
    path = root / "backend" / "data" / "legacy_artists.json"
    with path.open(encoding="utf-8") as fh:
        raw = json.load(fh)
    result: list[LegacyArtist] = []
    for entry in raw:
        entry["tags"] = set(entry.get("tags", []))
        result.append(LegacyArtist(**entry))
    return result


LEGACY_ARTISTS: list[LegacyArtist] = _load_legacy_artists()
SEED_TAGS_BY_ID: dict[str, set[str]] = {a.id: a.tags for a in LEGACY_ARTISTS}
SEED_TAGS_BY_NAME: dict[str, set[str]] = {a.name: a.tags for a in LEGACY_ARTISTS}
LEGACY_ARTISTS_BY_ID: dict[str, LegacyArtist] = {a.id: a for a in LEGACY_ARTISTS}
LEGACY_ARTISTS_BY_NAME: dict[str, LegacyArtist] = {a.name: a for a in LEGACY_ARTISTS}


def _load_modern_pool() -> list[dict]:
    root = Path(__file__).resolve().parents[2]
    path = root / "backend" / "data" / "modern_candidate_pool.json"
    with path.open(encoding="utf-8") as fh:
        return json.load(fh)


def _record_to_scoring_dict(candidate: CandidateSourceRecord) -> dict[str, Any]:
    """Build an ad-hoc dict for ``resolve_emergence_year`` and scoring.

    These legacy functions expect a raw JSON entry dict; this helper
    maps the contract fields back into that shape without requiring
    the functions themselves to change.
    """
    return {
        "first_known_year": candidate.first_known_year,
        "emergence_year": candidate.emergence_year,
        "debut_year": candidate.debut_year,
        "formed_year": candidate.formed_year,
        "emotional_tones": candidate.emotional_tones,
        "lyrical_themes": candidate.lyrical_themes,
        "production_style": candidate.production_style,
        "vocal_style": candidate.vocal_style,
        "scene_lineage": candidate.scene_lineage,
    }


def _build_recommendation(
    candidate: CandidateSourceRecord,
    seed_tags: set[str],
    current_year: int,
    modern_window_years: int,
    seed_artist: LegacyArtist,
) -> dict | None:
    candidate_dict = _record_to_scoring_dict(candidate)
    candidate_tags = normalize_tags(set(candidate.tags))
    emergence = resolve_emergence_year(
        artist=candidate_dict,
        current_year=current_year,
        window_years=modern_window_years,
    )
    scored = score_dimension_candidate(
        seed_emotional_tones=seed_artist.emotional_tones,
        seed_lyrical_themes=seed_artist.lyrical_themes,
        seed_production_style=seed_artist.production_style,
        seed_vocal_style=seed_artist.vocal_style,
        seed_scene_lineage=seed_artist.scene_lineage,
        candidate=candidate_dict,
        is_modern_window=emergence.is_modern_window,
    )

    if scored.classification == "excluded":
        return None

    weighted_shared_tags = get_weighted_shared_tags(seed_tags, candidate_tags)
    shared_tags = [item["tag"] for item in weighted_shared_tags]

    cs = scored.component_scores
    emergence_type = compute_emergence_type(emergence, scored.classification)
    return {
        "artist_name": candidate.artist_name,
        "classification": scored.classification,
        "echo_score": scored.echo_score,
        "confidence": scored.confidence,
        "emergence_type": emergence_type,
        "emergence_year": emergence.resolved_year,
        "emergence_resolution": {
            "source_field": emergence.source_field,
            "fallback_used": emergence.fallback_used,
            "is_modern_window": emergence.is_modern_window,
            "window_start_year": emergence.window_start_year,
            "window_end_year": emergence.window_end_year,
            "note": emergence.note,
        },
        "shared_tags": shared_tags,
        "shared_tag_weights": weighted_shared_tags,
        "component_scores": {
            "emotional_match": cs.emotional_match,
            "scene_match": cs.scene_match,
            "lyrical_match": cs.lyrical_match,
            "production_match": cs.production_match,
            "vocal_match": cs.vocal_match,
            "emerging_bonus": cs.emerging_bonus,
        },
        "sources": ["manual_pool"],
        "source_note": candidate.match_explanation,
        "spotify_url": candidate.external_urls.get("spotify", ""),
        "image_url": "",
        "genres": [],
    }


@app.exception_handler(HTTPException)
async def handle_http_exception(request: Request, exc: HTTPException) -> JSONResponse:
    if isinstance(exc.detail, dict) and "error" in exc.detail:
        content: dict = exc.detail
    else:
        content = {"error": {"code": "http_error", "message": str(exc.detail)}}
    return JSONResponse(status_code=exc.status_code, content=content)


@app.exception_handler(Exception)
async def handle_unexpected_exception(request: Request, exc: Exception) -> JSONResponse:
    return JSONResponse(
        status_code=500,
        content={
            "error": {
                "code": "internal_server_error",
                "message": "An unexpected error occurred.",
            }
        },
    )


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/legacy-artists")
async def get_legacy_artists() -> list[dict]:
    return [
        {
            "id": a.id,
            "name": a.name,
            "tags": sorted(a.tags),
            "spotify_url": a.spotify_url,
            "active_years": a.active_years,
            "genres": a.genres,
            "emotional_tones": a.emotional_tones,
            "lyrical_themes": a.lyrical_themes,
            "production_style": a.production_style,
            "vocal_style": a.vocal_style,
            "scene_lineage": a.scene_lineage,
            "notes": a.notes,
        }
        for a in LEGACY_ARTISTS
    ]


def _get_spotify_client():
    from .spotify import SpotifyClient
    return SpotifyClient.from_env()


def _get_lastfm_client():
    from .lastfm import LastFmClient
    return LastFmClient.from_env()


def _get_musicbrainz_client():
    from .musicbrainz import MusicBrainzClient
    return MusicBrainzClient.from_env()


def _enrich_lastfm_source_status(response: dict, seed_artist: LegacyArtist) -> None:
    # Status check only: does not contribute recommendation candidates yet.
    client = _get_lastfm_client()
    if client is None:
        response["metadata"]["source_status"]["lastfm_graph"] = {
            "status": "unavailable",
            "message": "Last.fm API key not configured",
        }
        return

    try:
        found = client.search_artist_exists(seed_artist.name)
        if found:
            response["metadata"]["source_status"]["lastfm_graph"] = {
                "status": "ok",
                "message": "",
            }
        else:
            response["metadata"]["source_status"]["lastfm_graph"] = {
                "status": "empty",
                "message": "No Last.fm artist match found",
            }
    except Exception:
        response["metadata"]["source_status"]["lastfm_graph"] = {
            "status": "failed",
            "message": "Last.fm lookup failed",
        }


def _enrich_musicbrainz_source_status(response: dict, seed_artist: LegacyArtist) -> None:
    # Status check only: does not contribute recommendation candidates yet.
    client = _get_musicbrainz_client()
    if client is None:
        response["metadata"]["source_status"]["musicbrainz"] = {
            "status": "unavailable",
            "message": "MusicBrainz user agent not configured",
        }
        return

    try:
        found = client.search_artist_exists(seed_artist.name)
        if found:
            response["metadata"]["source_status"]["musicbrainz"] = {
                "status": "ok",
                "message": "",
            }
        else:
            response["metadata"]["source_status"]["musicbrainz"] = {
                "status": "empty",
                "message": "No MusicBrainz artist match found",
            }
    except Exception:
        response["metadata"]["source_status"]["musicbrainz"] = {
            "status": "failed",
            "message": "MusicBrainz lookup failed",
        }


def _enrich_recommendation_response(response: dict, seed_artist: LegacyArtist) -> None:
    _enrich_lastfm_source_status(response, seed_artist)
    _enrich_musicbrainz_source_status(response, seed_artist)
    client = _get_spotify_client()
    if client is None:
        response["metadata"]["source_status"]["spotify"] = {
            "status": "unavailable",
            "message": "Spotify credentials not configured",
        }
        return

    enriched_count = 0
    try:
        seed_meta = client.search_artist(seed_artist.name)
        if seed_meta:
            if seed_meta.spotify_url:
                response["seed_artist"]["spotify_url"] = seed_meta.spotify_url
            response["seed_artist"]["image_url"] = seed_meta.image_url
            response["seed_artist"]["genres"] = seed_meta.genres
            enriched_count += 1

        for card in response["modern_echoes"] + response["bridge_artists"]:
            meta = client.search_artist(card["artist_name"])
            if meta:
                if meta.spotify_url:
                    card["spotify_url"] = meta.spotify_url
                card["image_url"] = meta.image_url
                card["genres"] = meta.genres
                enriched_count += 1

        if enriched_count > 0:
            response["metadata"]["source_status"]["spotify"] = {
                "status": "ok",
                "message": "",
            }
        else:
            response["metadata"]["source_status"]["spotify"] = {
                "status": "empty",
                "message": "No Spotify metadata found",
            }
    except Exception:
        response["metadata"]["source_status"]["spotify"] = {
            "status": "failed",
            "message": "Spotify lookup failed",
        }


def _build_sorted_response(seed_artist: LegacyArtist, modern_window_years: int = 5) -> dict:
    current_year = datetime.now().year
    try:
        raw_pool = _load_modern_pool()
        manual_pool_status = "ok"
    except Exception:
        raise HTTPException(
            status_code=500,
            detail={
                "error": {
                    "code": "internal_server_error",
                    "message": "An unexpected error occurred.",
                }
            },
        )

    source = ManualPoolSource(raw_pool)
    seed_tags = SEED_TAGS_BY_NAME[seed_artist.name]
    candidates = source.get_candidates(seed_artist.name)

    if not candidates:
        manual_pool_status = "empty"

    modern_echoes: list[dict] = []
    bridge_artists: list[dict] = []

    for candidate in candidates:
        rec = _build_recommendation(candidate, seed_tags, current_year, modern_window_years, seed_artist)
        if rec is None:
            continue
        if rec["classification"] == "modern_echo":
            modern_echoes.append(rec)
        else:
            bridge_artists.append(rec)

    modern_echoes.sort(key=lambda r: r["echo_score"], reverse=True)
    bridge_artists.sort(key=lambda r: r["echo_score"], reverse=True)

    if modern_echoes and bridge_artists:
        reason = "results_found"
    elif modern_echoes and not bridge_artists:
        reason = "no_bridge_artists_found"
    elif not modern_echoes and bridge_artists:
        reason = "no_modern_echoes_found"
    else:
        reason = "no_results_found"

    response = {
        "seed": seed_artist.name,
        "seed_artist": {
            "id": seed_artist.id,
            "name": seed_artist.name,
            "spotify_url": seed_artist.spotify_url,
            "image_url": "",
            "genres": [],
        },
        "modern_echoes": modern_echoes,
        "bridge_artists": bridge_artists,
        "metadata": {
            "reason": reason,
            "model_version": "legacy-v1",
            "shadow_score_summary": {},
            "gating_reason": "",
            "source_status": {
                "manual_pool": {"status": manual_pool_status, "message": ""},
                "lastfm_graph": {"status": "planned", "message": "Not implemented in manual MVP"},
                "musicbrainz": {"status": "planned", "message": "Not implemented in manual MVP"},
                "spotify": {"status": "planned", "message": "Not implemented in manual MVP"},
            },
        },
    }

    _enrich_recommendation_response(response, seed_artist)

    reco_config = _get_reco_config()
    if reco_config.mode in {"shadow", "hybrid_primary"}:
        diagnostics = _build_shadow_diagnostics(seed_artist, modern_window_years, candidates, modern_echoes, bridge_artists)
        response["metadata"]["model_version"] = reco_config.model_version
        response["metadata"]["shadow_score_summary"] = {
            "legacy_count": diagnostics["legacy_count"],
            "hybrid_count": diagnostics["hybrid_count"],
            "topk_overlap": diagnostics["topk_overlap"],
        }
        if reco_config.mode == "hybrid_primary":
            promoted = [c for c in diagnostics["candidates"] if c["gate_ok"]]
            promoted.sort(key=lambda x: x["final_score"], reverse=True)
            modern_echoes = []
            bridge_artists = []
            for row in promoted:
                original = row["original_card"]
                if original["classification"] == "modern_echo":
                    modern_echoes.append(original)
                elif original["classification"] == "bridge_artist":
                    bridge_artists.append(original)
            response["modern_echoes"] = modern_echoes
            response["bridge_artists"] = bridge_artists
    return response


def _build_shadow_diagnostics(
    seed_artist: LegacyArtist,
    modern_window_years: int,
    candidates: list[CandidateSourceRecord],
    legacy_modern: list[dict],
    legacy_bridge: list[dict],
) -> dict:
    seed_record = {
        "id": seed_artist.id,
        "name": seed_artist.name,
        "genres": seed_artist.genres,
        "tags": list(SEED_TAGS_BY_NAME.get(seed_artist.name, set())),
        "emotional_tones": seed_artist.emotional_tones,
        "lyrical_themes": seed_artist.lyrical_themes,
        "production_style": seed_artist.production_style,
        "vocal_style": seed_artist.vocal_style,
        "scene_lineage": seed_artist.scene_lineage,
        "notes": seed_artist.notes,
        "first_known_year": None,
        "formed_year": None,
        "release_count": 1,
    }
    hybrid_runtime = _get_hybrid_runtime()
    seed_profile = hybrid_runtime.compute_signature(seed_artist.id, seed_record)
    seed_profile["name"] = seed_artist.name
    seed_profile["tags"] = list(SEED_TAGS_BY_NAME.get(seed_artist.name, set()))

    legacy_cards = legacy_modern + legacy_bridge
    by_name = {c["artist_name"]: c for c in legacy_cards}
    shadow_candidates: list[dict] = []
    known_names = {seed_artist.name}
    promoted_names: list[str] = []
    for cand in candidates:
        cand_record = {
            "id": cand.artist_name.strip().casefold().replace(" ", "-"),
            "name": cand.artist_name,
            "genres": [],
            "tags": cand.tags,
            "emotional_tones": cand.emotional_tones,
            "lyrical_themes": cand.lyrical_themes,
            "production_style": cand.production_style,
            "vocal_style": cand.vocal_style,
            "scene_lineage": cand.scene_lineage,
            "notes": cand.match_explanation,
            "first_known_year": cand.first_known_year,
            "formed_year": cand.formed_year,
            "debut_year": cand.debut_year,
            "emergence_year": cand.emergence_year,
            "release_count": 1,
        }
        cand_profile = hybrid_runtime.compute_signature(cand_record["id"], cand_record)
        cand_profile["name"] = cand.artist_name
        cand_profile["tags"] = cand.tags
        result = hybrid_runtime.score_candidate_shadow(seed_profile, cand_profile, known_names=known_names)
        row = {
            "artist_name": cand.artist_name,
            "gate_ok": result.gate_ok,
            "gate_reason": result.gate_reason,
            "final_score": result.final_score,
            "components": result.components,
            "explanation": result.explanation,
            "original_card": by_name.get(cand.artist_name, {}),
        }
        shadow_candidates.append(row)
        if result.gate_ok:
            promoted_names.append(cand.artist_name)

    legacy_names = [c["artist_name"] for c in legacy_cards]
    hybrid_runtime.write_shadow_artifact(seed_artist.id, seed_artist.name, legacy_names, promoted_names)
    topk = min(5, len(legacy_names), len(promoted_names))
    overlap = 0.0 if topk == 0 else len(set(legacy_names[:topk]) & set(promoted_names[:topk])) / topk
    return {
        "legacy_count": len(legacy_names),
        "hybrid_count": len(promoted_names),
        "topk_overlap": round(overlap, 6),
        "candidates": shadow_candidates,
    }


@app.get(
    "/recommendations/{legacy_artist_id}",
    response_model=RecommendationsResponse,
    responses={
        404: {"model": ErrorResponse, "description": "Seed not found"},
        500: {"model": ErrorResponse, "description": "Internal server error"},
    },
)
async def get_recommendations_by_id(
    legacy_artist_id: str,
    modern_window_years: int = Query(5, ge=0, le=20, description="How many years back to treat as modern. Default is 5."),
) -> dict:
    seed_artist = LEGACY_ARTISTS_BY_ID.get(legacy_artist_id)
    if not seed_artist:
        raise HTTPException(
            status_code=404,
            detail={
                "error": {
                    "code": "seed_not_found",
                    "message": f"Unknown legacy artist '{legacy_artist_id}'. Supported IDs: {', '.join(LEGACY_ARTISTS_BY_ID)}",
                }
            },
        )
    return _build_sorted_response(seed_artist, modern_window_years)


@app.get(
    "/api/recommendations",
    response_model=RecommendationsResponse,
    responses={
        404: {"model": ErrorResponse, "description": "Seed not found"},
        500: {"model": ErrorResponse, "description": "Internal server error"},
    },
)
async def get_recommendations(
    seed: str = Query(..., description="Legacy artist seed, e.g. 'Manchester Orchestra'"),
    modern_window_years: int = Query(5, ge=0, le=20, description="How many years back to treat as modern. Default is 5."),
) -> dict:
    seed_name = seed.strip()
    seed_artist = LEGACY_ARTISTS_BY_NAME.get(seed_name)
    if not seed_artist:
        raise HTTPException(
            status_code=404,
            detail={
                "error": {
                    "code": "seed_not_found",
                    "message": f"Unknown seed '{seed_name}'. Supported seeds: {', '.join(LEGACY_ARTISTS_BY_NAME)}",
                }
            },
        )
    return _build_sorted_response(seed_artist, modern_window_years)


@app.get(
    "/api/recommendations/diagnostics",
    response_model=DiagnosticsResponse,
    responses={
        404: {"model": ErrorResponse, "description": "Seed not found"},
        500: {"model": ErrorResponse, "description": "Internal server error"},
    },
)
async def get_recommendations_diagnostics(
    seed: str = Query(..., description="Legacy artist seed, e.g. 'Manchester Orchestra'"),
    modern_window_years: int = Query(5, ge=0, le=20, description="How many years back to treat as modern."),
) -> dict:
    seed_name = seed.strip()
    reco_config = _get_reco_config()
    seed_artist = LEGACY_ARTISTS_BY_NAME.get(seed_name)
    if not seed_artist:
        raise HTTPException(
            status_code=404,
            detail={"error": {"code": "seed_not_found", "message": f"Unknown seed '{seed_name}'."}},
        )
    raw_pool = _load_modern_pool()
    source = ManualPoolSource(raw_pool)
    candidates = source.get_candidates(seed_artist.name)

    response = _build_sorted_response(seed_artist, modern_window_years)
    diagnostics = _build_shadow_diagnostics(
        seed_artist=seed_artist,
        modern_window_years=modern_window_years,
        candidates=candidates,
        legacy_modern=response["modern_echoes"],
        legacy_bridge=response["bridge_artists"],
    )
    return {
        "seed": seed_artist.name,
        "model_version": reco_config.model_version,
        "mode": reco_config.mode,
        "legacy_count": diagnostics["legacy_count"],
        "hybrid_count": diagnostics["hybrid_count"],
        "candidates": [
            {
                "artist_name": c["artist_name"],
                "gate_ok": c["gate_ok"],
                "gate_reason": c["gate_reason"],
                "final_score": c["final_score"],
                "components": c["components"],
                "explanation": c["explanation"],
            }
            for c in diagnostics["candidates"]
        ],
    }
