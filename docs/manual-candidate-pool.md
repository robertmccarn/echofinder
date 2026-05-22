# Manual Candidate Pool Contract

EchoFinder's active MVP candidate source is the manual pool at:

- `backend/data/modern_candidate_pool.json`

This source is intentionally transparent and reviewable. It is not hidden ranking data.

## Required Fields

Each manual pool entry is validated by `backend/scripts/validate_dataset.py` and must include:

- `id`
- `name`
- `formed_year`
- `active_status`
- `spotify_url`
- `monthly_listeners`
- `genres`
- `emotional_tones`
- `lyrical_themes`
- `production_style`
- `vocal_style`
- `scene_lineage`
- `curator_notes`
- `recommended_legacy_matches`

Backward compatibility currently also expects:

- `related_legacy_styles`

Runtime-scoring fields used by the recommendation path include:

- `tags`
- `source_note`
- `first_known_year` (when available)

## Eligibility Rules

`ManualPoolSource` (`backend/app/manual_pool.py`) filters entries by:

- non-empty `name`
- `active_status` is not explicitly `false`
- seed match against `recommended_legacy_matches` (fallback to `related_legacy_styles`)

## Merge and Dedupe Contract

Candidate records use `CandidateSourceRecord` and are merged by `merge_candidate_records` in `backend/app/candidates.py`.

Current merge behavior for duplicates (same normalized `artist_name`):

- `source_name`: joined and sorted with `/`
- `tags`: union + sort
- `confidence_signal`: max value
- year fields (`emergence_year`, `first_known_year`, `debut_year`, `formed_year`): first non-null
- text fields (`production_style`, `vocal_style`, `scene_lineage`): longer value
- explanation fields: concatenated with `; `
- URLs: merged dictionary, later values overwrite duplicate keys

For manual-only candidates, source is `manual_pool`.

## Provenance and Source Disclosure

API responses disclose source provenance through:

- recommendation card `sources` list (includes `manual_pool`)
- recommendation card `source_note`
- response metadata `source_status.manual_pool`

This is required for truthful UX:

- users can see where recommendations came from
- contributors can audit why a candidate appears

## Data Governance Rules

Manual pool entries must remain:

- reviewable (human-readable and inspectable in repo)
- non-sensitive (no personal/private/confidential data)
- grounded in source notes (`source_note` and `curator_notes`)

Do not add hidden or unverifiable scoring signals.

