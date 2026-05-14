# MVP Roadmap

EchoFinder's MVP is backend-first. The goal is to move from prototype scripts to a truthful API before adding a full frontend or Spotify login.

## Phase 1: Research And Prototype

- [x] Spotify lookup script.
- [x] Last.fm lookup script.
- [x] MusicBrainz lookup script.
- [x] Prototype recommendation runner.
- [x] Manual modern candidate pool.
- [ ] Manual review of first recommendation samples for quality.

## Phase 2: Backend Foundation

- [x] FastAPI app entrypoint.
- [x] `GET /health`.
- [ ] API key and local run documentation.
- [ ] Pure Echo Score and classification functions.
- [ ] Candidate source contract.
- [ ] Pydantic response and error models.
- [ ] Mocked tests for scoring and endpoint behavior.

## Phase 3: Recommendation API

- [ ] `GET /api/recommendations` for one legacy seed.
- [ ] `modern_echoes` and `bridge_artists` response sections.
- [ ] Source status metadata for Spotify, Last.fm, MusicBrainz, and manual pool.
- [ ] Empty-result rules that do not invent recommendations.
- [ ] Explainability fields such as shared tags, sources, emergence year, confidence, and score.

## Phase 4: Frontend And Spotify Account Features

Planned after the backend contract is stable:

- [ ] Next.js app skeleton.
- [ ] Search form for legacy artist input.
- [ ] Result cards with explanation fields.
- [ ] Spotify login.
- [ ] Spotify library import.
- [ ] Playlist creation.

## Phase 5: Persistence And Scaling

Planned after the MVP API shape is proven:

- [ ] PostgreSQL-backed metadata cache.
- [ ] Artist and signal persistence.
- [ ] Background enrichment jobs.
- [ ] pgvector or other similarity acceleration if the simpler model needs it.

## Current Priority

Prioritize:

1. Truthful backend contracts.
2. Pure scoring functions and tests.
3. Candidate source transparency.
4. Local setup and API key documentation.
5. Frontend only after backend responses are stable.
