from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path

from fastapi import FastAPI, HTTPException, Query, Request
from fastapi.responses import JSONResponse
from .scoring import score_candidate

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

        candidate_tags = {t.lower() for t in artist.get("tags", [])}
        emergence_year = artist.get("first_known_year")
        is_modern_window = isinstance(emergence_year, int) and emergence_year >= min_emergence_year
        scored = score_candidate(
            seed_tags=SEED_TAGS[seed_name],
            candidate_tags=candidate_tags,
            lineage_match=0.9,
            is_modern_window=is_modern_window,
        )

        if scored.classification == "excluded":
            continue

        recommendation = {
            "artist_name": artist.get("name"),
            "echo_score": scored.echo_score,
            "confidence": scored.confidence,
            "emergence_year": emergence_year,
            "shared_tags": scored.shared_tags,
            "sources": ["manual_pool"],
            "source_note": artist.get("source_note", ""),
        }

        if scored.classification == "modern_echo":
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
