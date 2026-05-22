# API Keys and Local Run Guide

This guide reflects the current EchoFinder manual MVP behavior.

## Current MVP Reality

- API keys are **not required** for core MVP usage.
- Recommendations run from local datasets and local scoring logic.
- FastAPI endpoints run without external credentials.
- Spotify metadata enrichment is optional and only affects metadata fields when configured.

## Environment Variables

EchoFinder reads environment variables from your shell (or a local `.env` you load into your shell).

### Spotify (optional for metadata enrichment)

- `SPOTIFY_CLIENT_ID`
- `SPOTIFY_CLIENT_SECRET`

When both are present:

- `/api/recommendations` and `/recommendations/{legacy_artist_id}` may include enriched `spotify_url`, `image_url`, and `genres`.
- `metadata.source_status.spotify.status` can become `ok`, `empty`, or `failed` based on lookup outcome.

When either is missing:

- Endpoints still return HTTP 200 for known seeds.
- Response stays truthful with `metadata.source_status.spotify.status = "unavailable"`.

### Last.fm (prototype-era only, not used by manual MVP flow)

- `LASTFM_API_KEY`
- `LASTFM_API_SECRET`

These are not required for current manual MVP recommendation flow.

### MusicBrainz (prototype-era only, not used by manual MVP flow)

- `MUSICBRAINZ_USER_AGENT`

This is not required for current manual MVP recommendation flow.

### Database (optional / future-facing)

- `DATABASE_URL`

No database is required for current manual MVP behavior.

## Local Setup

```powershell
cd backend
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

## Run FastAPI Locally

From repository root:

```powershell
uvicorn backend.app.main:app --reload
```

Verify:

```powershell
curl http://127.0.0.1:8000/health
curl "http://127.0.0.1:8000/api/recommendations?seed=Manchester Orchestra"
```

## Optional Spotify Credential Check

With Spotify credentials set:

```powershell
python backend/scripts/run_live_demo.py --seed "Manchester Orchestra"
```

Look for:

- `Source Status: spotify: ok` (or `empty`/`failed` based on lookup outcome), instead of `unavailable`.
