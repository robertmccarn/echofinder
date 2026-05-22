# EchoFinder

> Find the modern echo of the music you love.

EchoFinder is a music discovery project for listeners who want newer, active, decently successful artists that sound stylistically connected to older favorite bands.

The project is currently in a **manual MVP** phase: single-user, locally curated, no external API keys required. All data lives in local JSON files, and the scoring engine runs entirely offline.

EchoFinder is organized around three discovery inputs:

- A specific legacy artist or band.
- A genre.
- A scene or musical lineage.

Core terms:

- **Legacy artists**: older favorite artists or bands that anchor the search.
- **Modern Echoes**: newer artists, preferably emerging within the last 0–5 years, with stylistic overlap and enough activity or traction to be worth recommending.
- **Bridge Artists**: older or non-emerging artists that explain lineage, influence, or transition between the legacy seed and newer artists.

Initial seed artists:

- Manchester Orchestra
- Thrice
- The Decemberists

## MVP Scope

### Implemented

- Manual modern candidate pool in `backend/data/modern_candidate_pool.json`.
- Scoring engine (`backend/app/scoring.py`) with tag similarity, emergence filtering, and Modern Echo vs Bridge classification.
- FastAPI endpoints:
  - `GET /health`
  - `GET /legacy-artists` — returns seed artist list with metadata and Spotify URLs.
  - `GET /recommendations/{legacy_artist_id}` — returns ranked recommendation cards with scores, shared tags, and source notes.
  - `GET /api/recommendations?seed=<name>` — query-param version of the above.
- Emergence year resolution (`backend/app/emergence.py`) with configurable modern window.
- Unit test suite (36 tests) covering scoring, classification, emergence, and endpoint behavior — no live API calls.
- CI workflow that runs tests on push/PR to `main` and `test-main`.

### MVP Non-Goals

The following are explicitly out of scope for the manual MVP phase:

- Spotify login / OAuth
- Playlist creation
- User accounts or personalization from listening history
- External API integrations (Spotify, Last.fm, MusicBrainz) for live data
- Embeddings or vector-database infrastructure (pgvector)
- AI/ML model training or inference
- Production deployment or hosting
- Frontend application (Next.js or otherwise)

### Previous Prototype (External API Era)

Before the manual MVP refactor, EchoFinder included Python research scripts that queried Spotify, Last.fm, and MusicBrainz APIs. Those scripts remain in `backend/scripts/` as reference but are not part of the current MVP flow. The MVP uses only local data.

## Setup (No API Keys Required)

Prerequisites:

- Python 3.10+

```powershell
cd backend
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

## Commands

Validate dataset files:

```powershell
python backend\scripts\validate_dataset.py
```

Validate tag values against the controlled taxonomy:

```powershell
python backend\scripts\validate_taxonomy.py
```

Run tests:

```powershell
python -m pytest backend\tests -v
```

Run the FastAPI server:

```powershell
uvicorn backend.app.main:app --reload
```

Verify the server:

```powershell
curl http://127.0.0.1:8000/health
curl http://127.0.0.1:8000/legacy-artists
curl http://127.0.0.1:8000/recommendations/manchester-orchestra
```

Expected health response:

```json
{"status":"ok"}
```

## Learning-First Approach

EchoFinder is intentionally built in small, inspectable steps. The repository should explain both what exists and why decisions were made. Planned capabilities must be labeled as planned until implemented and validated.
