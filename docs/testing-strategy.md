# Testing Strategy (Backend-First MVP)

This document defines validation expectations for EchoFinder's backend-first MVP.

Goals:

- protect recommendation correctness and explainability
- protect API response contracts and error behavior
- prevent regressions while productizing from script prototype to service
- keep automated tests deterministic and credential-independent

## Core Rule: No Live API Calls in Automated Tests

Automated tests must not call live external services:

- Spotify
- Last.fm
- MusicBrainz

Test suites should use local fixtures, stubs, and mocks for all external clients and status checks.

## Validation Layers

### 1) Pure Engine/Scoring Tests

Purpose:

- validate scoring, classification, emergence logic, and tag similarity behavior
- ensure deterministic behavior across edge cases

Examples in repo:

- scoring and classification tests
- emergence resolver tests
- tag normalization/similarity tests

### 2) Candidate Source Contract Tests

Purpose:

- validate `CandidateSourceRecord` contract and merge/dedupe behavior
- validate `ManualPoolSource` eligibility/filtering/provenance behavior

Examples in repo:

- candidate contract tests
- manual pool integration tests

### 3) Endpoint/Contract Tests (FastAPI)

Purpose:

- validate endpoint shape and field presence for:
  - `GET /health`
  - `GET /api/recommendations`
- validate truthful empty responses and flat error responses
- ensure response models remain aligned with runtime payloads

Examples in repo:

- endpoint contract tests
- response model tests

### 4) Data/Taxonomy Validation Scripts

Purpose:

- validate local datasets and taxonomy integrity before merge/release
- catch schema drift or invalid tags/years/required fields

Scripts:

- `python backend/scripts/validate_taxonomy.py`
- `python backend/scripts/validate_dataset.py`
- `python backend/scripts/validate_known_seeds.py`

### 5) Manual QA / Demo Validation

Purpose:

- validate user-facing experience and explainability output
- verify local app/demo usability and trust signals

Primary command:

- `python backend/scripts/run_live_demo.py --seed "Manchester Orchestra"`

For frontend work, also verify:

- search flow
- loading/error/empty states
- results/explanation card rendering

## Baseline Commands

For implementation PRs (non-trivial code changes), expected baseline:

```powershell
python -m compileall backend/app backend/scripts backend/tests
python -m pytest backend/tests -q
python backend/scripts/validate_taxonomy.py
python backend/scripts/validate_dataset.py
python backend/scripts/validate_known_seeds.py
```

## Expected Validation by Change Type

### Backend/Engine Logic Changes

Expected:

- `compileall`
- `pytest`
- `validate_taxonomy.py`
- `validate_dataset.py`
- `validate_known_seeds.py`

Recommended:

- `run_live_demo.py --seed "Manchester Orchestra"`

### API Contract/Model Changes

Expected:

- `compileall`
- `pytest` (including endpoint/contract tests)
- manual endpoint check for changed behavior

Optional manual check examples:

```powershell
curl http://127.0.0.1:8000/health
curl "http://127.0.0.1:8000/api/recommendations?seed=Manchester%20Orchestra"
```

### Data/Taxonomy Changes

Expected:

- `validate_taxonomy.py`
- `validate_dataset.py`
- `validate_known_seeds.py`
- `pytest`

### Frontend Changes

Expected:

- `pytest` (to ensure backend contract remains stable)
- `npm run build` in `frontend/`
- manual frontend verification of states and recommendation rendering via `frontend/manual-qa-checklist.md`
- docs updates when UX behavior changes

### Docs-Only Changes

Expected:

- docs link check script:

```powershell
powershell -ExecutionPolicy Bypass -File scripts/product-ops/check-doc-links.ps1
```

Recommended:

- run `pytest` when docs include behavior/process claims that depend on current implementation

## Release/Board Lifecycle Note

Validation status should be reflected truthfully in PR and issue comments.

- Merged to `test-main` = implemented, pending release
- Merged to `main` = released

Do not mark issues as complete on board/repo until release state matches policy.
