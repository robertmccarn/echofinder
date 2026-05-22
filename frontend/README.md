# EchoFinder Frontend Skeleton

This folder contains the local Next.js skeleton for issue #8.

## Features

- Legacy artist search form
- Calls backend endpoint: `GET /api/recommendations?seed=...`
- Loading state
- Error state
- Empty-result state
- Basic recommendations display for modern echoes and bridge artists

## Run Locally

1. Start backend API:

```powershell
uvicorn backend.app.main:app --reload
```

2. Start frontend:

```powershell
cd frontend
npm install
npm run dev
```

3. Open:

```text
http://localhost:3000
```

## Environment

Copy `.env.example` to `.env.local` and adjust only if backend is not at default URL:

```text
NEXT_PUBLIC_ECHOFINDER_API_BASE=http://127.0.0.1:8000
```
