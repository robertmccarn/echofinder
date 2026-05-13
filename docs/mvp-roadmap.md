# MVP Roadmap

## Phase 1: Research & Prototyping (Current)
- [x] Spotify/Last.fm/MusicBrainz API Scripts
- [x] Basic "Echo Score" calculation in Python
- [x] 2nd-degree similarity crawl
- [ ] Manual review of first 25 recommendations for quality

## Phase 2: Backend Foundations
- [ ] Initialize PostgreSQL database
- [ ] Create FastAPI application skeleton
- [ ] Implement Background Workers (Celery/RQ) for data enrichment
- [ ] Build Artist Resolution logic (linking a Spotify ID to a MusicBrainz ID)

## Phase 3: Core API Features
- [ ] `GET /search`: Search for legacy artists
- [ ] `POST /echo-profile`: Generate DNA from seeds
- [ ] `GET /recommendations`: Retrieve scored and filtered matches
- [ ] Spotify OAuth Integration (User login)

## Phase 4: Frontend Development (Next.js)
- [ ] Landing Page (The "Pitch")
- [ ] Spotify Import Screen
- [ ] Echo Profile Visualization (DNA Bars)
- [ ] Recommendation Cards with "Why this fits" explanations

## Phase 5: Polish & Feedback
- [ ] Thumbs up/down feedback loop
- [ ] "Save to Spotify" playlist functionality
- [ ] Final UI/UX polish (Waveform dividers, ripple icons)
