# API Keys and Local Run Guide

Core manual MVP flow runs without external API credentials.

## Optional Variables

- `SPOTIFY_CLIENT_ID`
- `SPOTIFY_CLIENT_SECRET`
- `LASTFM_API_KEY`
- `LASTFM_API_SECRET`
- `MUSICBRAINZ_USER_AGENT`
- `DATABASE_URL` (optional/future-facing)

## Runtime Behavior

When optional credentials are missing, API responses still succeed for valid manual seeds and report truthful status in `metadata.source_status`.

Typical status values:

- `ok`
- `empty`
- `failed`
- `unavailable`
- `planned` (for not-yet-integrated source roles)

## Local Run

```powershell
cd backend
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
uvicorn backend.app.main:app --reload
```

## Validation

```powershell
python -m pytest
python -m compileall backend/app backend/scripts backend/tests
python backend/scripts/validate_taxonomy.py
python backend/scripts/validate_dataset.py
python backend/scripts/run_live_demo.py --seed "Manchester Orchestra"
```
