from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path

from fastapi import FastAPI, HTTPException, Query, Request
from fastapi.responses import JSONResponse

app = FastAPI(
    title="EchoFinder API",
    description="Initial backend API for the EchoFinder prototype.",
    version="0.2.0",
)


SEED_TAGS: dict[str, set[str]] = {
    "Manchester Orchestra": {"indie rock", "emo", "alternative", "post-hardcore"},
    "Thrice": {"post-hardcore", "alternative", "punk", "emo"},
    "The Decemberists": {"indie rock", "indie folk", "folk rock", "alt-country"},
}


def _load_modern_pool() -> list[dict]:
    root = Path(__file__).resolve().parents[2]
    path = root / "backend" / "data" / "modern_candidate_pool.json"
    with path.open(encoding="utf-8") as fh:
        return json.load(fh)


def _score_candidate(seed: str, candidate: dict) -> tuple[float, list[str]]:
    seed_tags = SEED_TAGS[seed]
    candidate_tags = {t.lower() for t in candidate.get("tags", [])}
    shared = sorted(seed_tags.intersection(candidate_tags))
    if not seed_tags:
        return 0.0, shared
    score = (len(shared) / len(seed_tags)) * 100
    return round(score, 1), shared


@app.exception_handler(Exception)
async def handle_unexpected_exception(request: Request, exc: Exception) -> JSONResponse:
    """Return a consistent response shape for unexpected server errors."""
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


@app.get("/api/recommendations")
async def get_recommendations(
    seed: str = Query(..., description="Legacy artist seed, e.g. 'Manchester Orchestra'"),
) -> dict:
    seed_name = seed.strip()
    if seed_name not in SEED_TAGS:
        raise HTTPException(
            status_code=404,
            detail={
                "error": {
                    "code": "seed_not_found",
                    "message": f"Unknown seed '{seed_name}'. Supported seeds: {', '.join(SEED_TAGS)}",
                }
            },
        )

    min_emergence_year = datetime.now().year - 5
    pool = _load_modern_pool()

    modern_echoes: list[dict] = []
    bridge_artists: list[dict] = []

    for artist in pool:
        related_styles = artist.get("related_legacy_styles", [])
        if seed_name not in related_styles:
            continue

        score, shared_tags = _score_candidate(seed_name, artist)
        emergence_year = artist.get("first_known_year")
        recommendation = {
            "artist_name": artist.get("name"),
            "echo_score": score,
            "emergence_year": emergence_year,
            "shared_tags": shared_tags,
            "sources": ["manual_pool"],
            "source_note": artist.get("source_note", ""),
        }

        if isinstance(emergence_year, int) and emergence_year >= min_emergence_year:
            modern_echoes.append(recommendation)
        else:
            bridge_artists.append(recommendation)

    modern_echoes.sort(key=lambda r: r["echo_score"], reverse=True)
    bridge_artists.sort(key=lambda r: r["echo_score"], reverse=True)

    return {
        "seed": seed_name,
        "modern_echoes": modern_echoes,
        "bridge_artists": bridge_artists,
    }
