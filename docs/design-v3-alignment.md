# Design v3 Alignment

Source reference:

- `C:/Users/Robert/Downloads/EchoFinder_Design_Document_v3_Brand_Integrated.docx`

This file maps the repository to the v3 design direction and clarifies what is already delivered versus staged next.

## North Star

EchoFinder should answer:

`What current artists carry forward the sound, scene, mood, or lyrical DNA of the older music I love?`

Product tone:

- curated, not chaotic
- nostalgic but current
- explainable and trust-building

## v3 Framing Applied

v3 framing in this repo is:

- keep the validated backend as the foundation
- productize it incrementally
- keep manual/local data as quality anchor while live breadth expands

## Current State (Aligned)

The repository currently aligns with the v3 "gold-star backend baseline":

- backend recommendation API is active and tested
- explainable score metadata is exposed
- manual candidate pool is active source
- optional live enrichment/status checks exist (Spotify/Last.fm/MusicBrainz)
- live demo script exists
- local frontend MVP skeleton exists with search and explanation cards

## Staged Product Roadmap (v3)

This is the repo-aligned interpretation of v3 phases:

1. Backend Validation MVP (completed baseline in this repo)
2. Manual Web MVP (now active via `frontend/` local skeleton, expanding UX quality)
3. Spotify Account MVP (future: OAuth/login + user-linked taste context)
4. Live Candidate Discovery Expansion (future: broader source ingestion)
5. Feedback + Playlist Workflows (future: thumbs/reasons/save/export/playlist after OAuth)

## Explicit Non-Claims

Not implemented yet unless explicitly delivered in code:

- Spotify OAuth account login
- playlist creation in Spotify
- account-based personalization from listening history
- full live candidate discovery replacing manual pool
- production deployment

## Brand Direction Applied to Frontend Skeleton

v3 brand direction says dark-mode native, lineage-focused discovery cards.

Repository alignment update:

- frontend base theme updated to dark-mode-first visual system
- recommendation cards remain explanation-forward (score/year/tags/sources/note)
- Spotify handoff stays explicit per recommendation card

## Next Alignment Tasks

- Add phase markers to project board issues (`web-mvp`, `spotify-account-mvp`, `live-discovery`)
- Add visual regression screenshots for frontend discovery cards
- Add a v3 "manual web MVP done" checklist doc tied to release gating
