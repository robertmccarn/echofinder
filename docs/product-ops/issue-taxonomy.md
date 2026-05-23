# Issue Taxonomy (EchoFinder)

This taxonomy keeps GitHub Issues consistent so they are easy to search, plan, and review.

## Current GitHub label reality

The repository now uses a consolidated canonical set with prefix conventions:

- `type:*`
- `prio:*`
- `ws:*`
- `size:*`

Older duplicate label families were removed as part of issue #77 cleanup.

## Issue types (labels)

Use exactly one:

- `type:epic`
- `type:story`
- `type:task`
- `type:bug`
- `type:spike`
- `type:chore`
- `type:docs`

## Workstreams (labels)

Use 1-2:

- `ws:backend`
- `ws:recommendations`
- `ws:scoring`
- `ws:data`
- `ws:docs`
- `ws:tooling`
- `ws:testing`
- `ws:frontend` (MVP-light only)

## Priorities (labels)

Use exactly one:

- `prio:P0` required for local MVP demo
- `prio:P1` important for quality/usability
- `prio:P2` useful but not blocking
- `prio:Stretch` post-MVP

## Status (project board)

GitHub Project board "Status" field values (recommended):

- Backlog
- Ready
- In Progress
- Review
- Pending Release
- Blocked
- Done

Expected lifecycle path:

```text
Backlog -> In Progress -> Review -> Pending Release -> Done
```

## Project field mapping (board fields)

When labels are updated, keep Project v2 single-select fields aligned:

- `Priority` field:
  - `prio:P0` -> `P0 - Critical`
  - `prio:P1` -> `P1 - High`
  - `prio:P2` -> `P2 - Medium`
  - `prio:Stretch` -> `P3 - Low`
- `Workstream` field:
  - `ws:backend` -> `api-access`
  - `ws:scoring` / `ws:data` / `ws:recommendations` -> `core-data`
  - `ws:docs` -> `documentation`
  - `ws:frontend` -> `dashboard-web`
  - `ws:tooling` -> `project-hygiene`
  - `ws:testing` (or testing-focused issues) -> `testing`

If an issue has multiple workstream labels, pick one primary workstream for the board field and keep secondary context in labels.

## Sizes (labels)

Use exactly one:

- `size:XS` (< 1 hour)
- `size:S` (1-3 hours)
- `size:M` (half day)
- `size:L` (1-2 days)
- `size:XL` (must split)

## Additional optional labels

- `good first issue` (small, low-risk)
- `blocked` (in addition to board status when useful)
- `needs decision` (waiting on a human choice)
- `needs research` (spike needed)
- `needs tests`
- `needs docs`

## Examples: good issue titles

- "Define `GET /api/recommendations` response model (Pydantic)"
- "Extract Echo Score v1 into pure functions with tests"
- "Add candidate source contract for manual pool"
- "Docs: add local API key setup guide"
- "Fix: recommendation prototype crashes on missing artist genres"

## Examples: bad issue titles

- "Recommendations endpoint"
- "Fix stuff"
- "Make it better"
- "Implement MVP"
- "Frontend"
