# Sprint Planning Playbook (EchoFinder)

EchoFinder sprint planning is optimized for a solo developer and small, demo-able increments.

## Capacity rules (solo-dev)

- Plan for **1-3 items** maximum.
- Treat **S/M** as the default; avoid L unless it's the only focus.
- Keep at least **25-40% buffer** for review, refactors, and learning time.

## Inputs

- `docs/mvp-roadmap.md` (truthful roadmap)
- current open issues (Backlog + Ready)
- current repo state (what actually exists)

## Selection rules

Prioritize work that:

1. moves the backend toward truthful API contracts
2. increases recommendation explainability and reliability
3. adds tests or validation harnesses that make future work safer
4. improves local demo readiness (setup docs, sample commands)

Avoid selecting items that:

- expand MVP scope (OAuth, accounts, playlist creation)
- add infrastructure early (DB/pgvector)
- require multiple decisions not yet made (use a spike first)

## Dependency sequencing

Typical sequence for API work:

1. response/request model shape (Pydantic)
2. endpoint skeleton with stubbed data
3. pure scoring/classification functions
4. wiring from sources to scoring
5. tests for pure functions and endpoint behavior
6. docs examples and manual QA notes

## WIP limits

- default WIP: **1 active issue**
- max WIP: **2** (only if one is blocked or waiting on review)

## Planning output (what to write down)

- chosen issues list with priority and size
- explicit "not doing this sprint" list to prevent scope creep
- validation plan for each issue (tests/manual)

## End-of-sprint review

For each issue attempted:

- evidence of completion (PR/commit + validation)
- what was learned / decisions made
- follow-ups split into new issues (small)

