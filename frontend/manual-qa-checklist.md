# Frontend Manual QA Checklist (Issue #136)

Use this checklist for frontend changes when automated frontend tests are not yet in place.

## Prerequisites

1. Backend running locally:

```powershell
uvicorn backend.app.main:app --reload
```

2. Frontend running locally:

```powershell
cd frontend
npm install
npm run dev
```

3. Open `http://localhost:3000`.

## Build Gate

- [ ] `npm run build` passes.
- [ ] `npm run lint` passes if lint config is present.

## UX Smoke Checks

- [ ] Search form renders with seed input and submit button.
- [ ] Submitting `Manchester Orchestra` returns a non-crashing result view.
- [ ] Modern Echoes section renders (with results or section-level empty copy).
- [ ] Bridge Artists section renders (with results or section-level empty copy).
- [ ] Recommendation cards show explanation fields (score, emergence year, shared tags, sources, source note).
- [ ] Spotify link behavior is clear (link present or "unavailable" copy).

## State Checks

- [ ] Loading state appears while a request is in flight.
- [ ] Unknown seed (for example `NOT_A_REAL_SEED_123`) shows readable error copy.
- [ ] Empty-result messaging is readable when results are empty.
- [ ] Backend unavailable state is readable (stop backend, then submit search).

## Notes Template

Record outcome before merging:

```text
Date:
Branch/PR:
Tester:
Build:
Lint:
Search flow:
Loading state:
Error state:
Empty state:
Backend offline state:
Follow-up issues:
```
