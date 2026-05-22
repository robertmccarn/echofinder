# Current MVP Scope

## Purpose

EchoFinder helps listeners discover modern artists that stylistically connect to legacy favorites.

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
