from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path

from typing import Any

from fastapi import FastAPI, HTTPException, Query, Request
from fastapi.responses import JSONResponse
from .candidates import CandidateSourceRecord
from .emergence import compute_emergence_type, resolve_emergence_year
from .manual_pool import ManualPoolSource
from .models import ErrorResponse, RecommendationsResponse
from .scoring import score_dimension_candidate, normalize_tags, get_weighted_shared_tags

app = FastAPI(
    title="EchoFinder API",
    description="Initial backend API for the EchoFinder prototype.",
    version="0.2.0",
)


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
            "source_status": {
                "manual_pool": {"status": manual_pool_status, "message": ""},
                "lastfm_graph": {"status": "planned", "message": "Not implemented in manual MVP"},
                "musicbrainz": {"status": "planned", "message": "Not implemented in manual MVP"},
                "spotify": {"status": "planned", "message": "Not implemented in manual MVP"},
            },
        },
    }

    _enrich_recommendation_response(response, seed_artist)
    return response


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
