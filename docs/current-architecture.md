# Current Architecture

EchoFinder is moving from research scripts toward a backend-first MVP.

## What Exists Today

```text
User/Developer
  -> Python scripts
  -> Spotify / Last.fm / MusicBrainz lookups
  -> prototype recommendation runner
  -> console output grouped as Modern Echoes and Bridge Artists
```

Implemented components:

- `backend/scripts/spotify_lookup.py`: Spotify catalog lookup helper.
- `backend/scripts/lastfm_lookup.py`: Last.fm tags and similar-artist lookup helper.
- `backend/scripts/musicbrainz_lookup.py`: MusicBrainz artist lookup helper.
- `backend/scripts/recommendation_prototype.py`: prototype candidate gathering and Echo Score calculation.
- `backend/data/modern_candidate_pool.json`: transparent manual source of newer candidate artists.
- `backend/app/main.py`: FastAPI app entrypoint with `GET /health`.
- `backend/schema.sql`: draft PostgreSQL schema, not yet wired into the app.

## Current Gaps

Not implemented yet:

- `/api/recommendations`.
- Pydantic recommendation response models.
- Extracted service layer.
- Pure scoring module with unit tests.
- OAuth or Spotify login.
- Next.js frontend.
- PostgreSQL runtime integration.
- pgvector similarity search.
- Playlist creation.

## Target MVP Architecture

```text
Client or local user
  -> FastAPI backend
  -> recommendation service layer
  -> candidate sources
       -> Last.fm graph
       -> MusicBrainz emergence data
       -> Spotify metadata
       -> manual modern candidate pool
  -> scoring and classification
  -> JSON response
       -> modern_echoes
       -> bridge_artists
       -> source_status
       -> explanation fields
```

Target backend modules should eventually include:

- API routes for health and recommendations.
- Pydantic request/response/error models.
- Candidate source adapters.
- Pure scoring and classification functions.
- Source status and empty-result metadata.
- Tests that do not call live external APIs.

## Transition Roadmap

Near-term sequence:

1. Keep `/health` stable.
2. Extract Echo Score and classification into pure functions.
3. Define candidate source contracts.
4. Define Pydantic response models.
5. Implement `/api/recommendations` for one seed.
6. Add mocked endpoint and scoring tests.
7. Add API key/local run documentation.
8. Add frontend only after backend JSON is stable.

## Architecture Principles

- Backend-first until the API contract is truthful.
- Metadata-first recommendations before heavy audio analysis.
- Source transparency over false certainty.
- Manual pool is a candidate source, not a hidden override.
- Planned systems stay labeled as planned until implemented.
