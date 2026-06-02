# Current MVP Scope

## Purpose

EchoFinder helps listeners discover modern artists that stylistically connect to legacy favorites.
The repo follows Design v3 framing: preserve the validated backend baseline and productize it in staged phases.

## Active Architecture

- Recommendation candidate generation uses `ManualPoolSource` and local JSON data.
- Candidate source contract exists in `backend/app/candidates.py`.
- API responses are Pydantic-backed and include metadata (`reason`, `source_status`).

## Implemented Live/API-Adjacent Behavior

- Spotify Phase 1 metadata enrichment through Client Credentials (not OAuth).
- Optional Last.fm source-status checks using `LASTFM_API_KEY`.
- Optional MusicBrainz source-status checks using `MUSICBRAINZ_USER_AGENT`.
- Live demo runner at `backend/scripts/run_live_demo.py`.
- Local Next.js frontend skeleton at `frontend/` with search form and backend API integration.
- Hybrid relational-signature engine scaffolding in backend with feature flags:
  - `RECO_ENGINE_MODE=legacy|shadow|hybrid_primary`
  - diagnostics endpoint: `GET /api/recommendations/diagnostics?seed=...`
  - Postgres-backed signature pipeline: `python backend/scripts/build_hybrid_signatures.py`

## Important Clarification

Last.fm and MusicBrainz currently provide credential-aware status checks and do **not** replace manual-pool candidate generation.

## Deferred Work

- Spotify OAuth/login
- Playlist creation
- User accounts and personalized recommendations
- Full live candidate discovery pipeline replacing manual pool
- Full frontend product experience beyond the current local skeleton
- pgvector/vector database architecture
- AI/ML model training/inference
- Production deployment

## Shadow-Mode Note

Default runtime behavior remains `legacy` scoring for recommendation responses.
When `RECO_ENGINE_MODE=shadow`, legacy output is preserved while hybrid diagnostics and
comparison artifacts are computed for evaluation.

## v3 Phase Mapping

- Phase 0 / Backend Validation MVP: active
- Phase 1 / Manual Web MVP: active (local frontend skeleton)
- Phase 2+ (Spotify Account Mode, live discovery expansion, feedback/playlist workflows): planned
