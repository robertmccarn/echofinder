# EchoFinder

> Find the modern echo of the music you love.

EchoFinder is a music discovery project for listeners who want newer, active, decently successful artists that sound stylistically connected to older favorite bands.

The project is currently in a **backend-first manual MVP** phase: single-user, locally curated, and fully usable without external API credentials. Core recommendation generation uses local JSON data and local scoring logic.

EchoFinder is organized around three discovery inputs:

- A specific legacy artist or band.
- A genre.
- A scene or musical lineage.

Core terms:

- **Legacy artists**: older favorite artists or bands that anchor the search.
- **Modern Echoes**: newer artists, preferably emerging within the last 0-5 years, with stylistic overlap and enough activity or traction to be worth recommending.
- **Bridge Artists**: older or non-emerging artists that explain lineage, influence, or transition between the legacy seed and newer artists.

Initial seed artists:

- Manchester Orchestra
- Thrice
- The Decemberists

## Current MVP Truth

Implemented:

- Active recommendation source: `ManualPoolSource` over local datasets.
- FastAPI endpoints:
  - `GET /health`
  - `GET /legacy-artists`
  - `GET /recommendations/{legacy_artist_id}`
  - `GET /api/recommendations?seed=<name>`
- Pydantic response and error models.
- Response metadata with:
  - `metadata.reason`
  - `metadata.source_status`
- Flat error response shape:

```json
{
  "error": {
    "code": "seed_not_found",
    "message": "..."
  }
}
```

- Optional live/API-adjacent support:
  - Spotify metadata enrichment via Client Credentials (no OAuth)
  - Last.fm credential-aware source status checks
  - MusicBrainz credential-aware source status checks
- Frontend skeleton:
  - Next.js app with seed search form and backend API call
  - Loading, error, and empty-result states
- Live demo script for human review and QA:
  - `backend/scripts/run_live_demo.py`

Deferred / not implemented:

- Spotify OAuth/user login
- Playlist creation
- User accounts or listening-history personalization
- Full live candidate discovery replacing manual pool
- Full frontend product UX beyond local skeleton
- pgvector/vector database infrastructure
- AI/ML model training or inference
- Production deployment

## Setup

Prerequisite: Python 3.11+

```powershell
cd backend
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

## Optional Credentials

Core manual MVP behavior requires no external credentials.

Optional environment variables:

- `SPOTIFY_CLIENT_ID`
- `SPOTIFY_CLIENT_SECRET`
- `LASTFM_API_KEY`
- `LASTFM_API_SECRET`
- `MUSICBRAINZ_USER_AGENT` (example: `EchoFinder/0.1.0 (you@example.com)`)
- `DATABASE_URL` (optional/future-facing)

## Commands

Run tests:

```powershell
python -m pytest
```

Run full validation:

```powershell
python -m compileall backend/app backend/scripts backend/tests
python backend/scripts/validate_taxonomy.py
python backend/scripts/validate_dataset.py
python backend/scripts/validate_known_seeds.py
python backend/scripts/run_live_demo.py --seed "Manchester Orchestra"
```

Run API:

```powershell
uvicorn backend.app.main:app --reload
```

Run frontend:

```powershell
cd frontend
npm install
npm run dev
```

Verify API:

```powershell
curl http://127.0.0.1:8000/health
curl http://127.0.0.1:8000/legacy-artists
curl "http://127.0.0.1:8000/api/recommendations?seed=Manchester%20Orchestra"
```

## Documentation

- `docs/README.md`
- `docs/current-mvp-scope.md`
- `docs/design-v3-alignment.md`
- `docs/api-keys-setup.md`
- `docs/development-workflow.md`
- `docs/product-ops/README.md`
