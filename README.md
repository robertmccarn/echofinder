# EchoFinder

> Find the modern echo of the music you love.

EchoFinder is a Spotify-centered music discovery project for listeners who want newer, active, decently successful artists that sound stylistically connected to older favorite bands.

The project is currently backend-first and learning-first. Today it contains Python research scripts, a prototype recommendation runner, a small manual modern candidate pool, and an initial FastAPI backend with `GET /health`.

## Product Direction

EchoFinder is organized around three discovery inputs:

- A specific legacy artist or band.
- A genre.
- A scene or musical lineage.

Core terms:

- Legacy artists: older favorite artists or bands that anchor the search.
- Modern Echoes: newer artists, preferably emerging within the last 0-5 years, with stylistic overlap and enough activity or traction to be worth recommending.
- Bridge Artists: older or non-emerging artists that explain lineage, influence, or transition between the legacy seed and newer artists.

Initial seed examples:

- Manchester Orchestra
- Thrice
- The Decemberists

## Current Status

Implemented:

- Python lookup scripts for Spotify, Last.fm, and MusicBrainz.
- Prototype recommendation logic in `backend/scripts/recommendation_prototype.py`.
- Manual modern candidate pool in `backend/data/modern_candidate_pool.json`.
- FastAPI app entrypoint in `backend/app/main.py`.
- `GET /health` endpoint.
- Documentation for branch workflow and local PR review automation.

Planned, not yet implemented:

- Spotify login/OAuth.
- Playlist creation.
- `/api/recommendations`.
- Next.js frontend.
- PostgreSQL/pgvector-backed persistence.
- Production deployment.

## Learning-First Approach

EchoFinder is intentionally built in small, inspectable steps:

1. Research external APIs through simple scripts.
2. Prototype recommendation logic in readable Python.
3. Extract stable service and scoring layers.
4. Add FastAPI endpoints and tests.
5. Add frontend and Spotify login only after backend contracts are truthful.

The repository should explain both what exists and why decisions were made. Planned capabilities must be labeled as planned until implemented and validated.

## Setup

Prerequisites:

- Python 3.10+
- Spotify Developer credentials for Spotify catalog access
- Last.fm API credentials
- A MusicBrainz user agent contact value

Copy the example environment file and fill in local values:

```powershell
cp .env.example .env
```

Backend setup:

```powershell
cd backend
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

Run the prototype from the repository root:

```powershell
python backend/scripts/recommendation_prototype.py
```

Run the FastAPI health endpoint:

```powershell
uvicorn backend.app.main:app --reload
curl http://127.0.0.1:8000/health
```

Expected response:

```json
{"status":"ok"}
```

## Documentation

Start with the docs index:

- [Docs README](./docs/README.md)
- [Product Vision](./docs/product-vision.md)
- [Current Architecture](./docs/current-architecture.md)
- [MVP Roadmap](./docs/mvp-roadmap.md)
- [Development Workflow](./docs/development-workflow.md)
- [PR Review Automation](./docs/pr-review-automation.md)
- [Local Worktree Management](./docs/local-worktree-management.md)
- [Learning-First Development](./docs/learning-first-development.md)
