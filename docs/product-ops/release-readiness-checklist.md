# Release / Milestone Readiness Checklist (EchoFinder)

Use this checklist before declaring an MVP milestone "demo-ready" or "release-ready".

## Milestone readiness (general)

- Scope is explicitly stated (what's in / what's out).
- All P0 issues for the milestone are Done per Definition of Done.
- Known limitations are documented.
- A short demo script exists (manual steps + expected output).

## MVP readiness (EchoFinder-specific)

MVP means:

- artist-based search flow is truthful (even if basic)
- backend provides a recommendation endpoint with explainable fields
- Echo Score v1 exists as pure code with tests (or documented manual validation)
- "Modern Echo vs Bridge Artist" classification is present and explainable
- recommendation results include source transparency (what signals were used)
- manual candidate pool is used and documented as a contract

MVP explicitly excludes:

- Spotify OAuth/login
- playlist creation
- user accounts
- personalization from listening history
- production deployment
- embeddings/vector DB infrastructure

## Demo readiness

- Local run steps work from a clean machine checklist (or are documented as assumptions).
- The demo can be performed in < 5 minutes.
- Example inputs are included (seed artists) and produce non-empty results.
- Empty-result behavior is sensible and documented.

## Technical validation

- `git diff --check` clean.
- Any available tests run (or a documented reason they can't).
- No secrets committed.
- No scratch files committed.

## Documentation validation

- docs reflect what's implemented (no "future tense" for shipped behavior).
- root `README.md` and `docs/README.md` remain truthful.
- new endpoints/contracts have minimal docs and examples.

## Known limitations

- limitations are documented as issues or a "known limitations" section
- any shortcuts are labeled as learning-first prototypes when applicable

