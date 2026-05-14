# Backlog Governance (EchoFinder)

This document defines how EchoFinder work items are created, shaped, sequenced, and closed so the backlog stays small, truthful, and portfolio-ready.

## Work item types

- **Epic**: a milestone-sized outcome composed of multiple stories (usually spans multiple sessions).
- **User story**: a small, user-value slice that should fit in one focused work session.
- **Task**: a technical work item that supports a story/epic (can be standalone if it delivers clear value).
- **Bug**: incorrect behavior compared to intended behavior (must include repro steps).
- **Spike**: time-boxed exploration to reduce uncertainty (must produce a concrete output artifact).
- **Chore**: maintenance work (dependencies, cleanup) with explicit non-feature scope.
- **Docs**: documentation updates (must point to source-of-truth code behavior).

## Issue lifecycle (recommended)

1. **Backlog**: captured, but not ready to start.
2. **Ready**: meets `definition-of-ready.md`.
3. **In Progress**: active work; has a branch (ideally) and current status note.
4. **Blocked**: cannot proceed; blocker is written down.
5. **Review**: PR exists and is awaiting review/validation.
6. **Done**: merged + validated + docs updated as needed; board matches reality.

## Creation rules (never create vague issues)

Every issue must contain:

- Problem statement (what's wrong / missing)
- Value (user value or technical value)
- Acceptance criteria (testable, specific)
- Tasks/subtasks (checklist)
- Dependencies (other issues/decisions)
- Priority (P0/P1/P2/Stretch)
- Size (XS/S/M/L/XL)
- Labels (type + workstream + priority)

If any of these are missing, the issue stays in **Backlog** until refined.

## Splitting rules (prefer smaller issues)

Split an item when:

- size is **XL** or unclear
- acceptance criteria mix multiple outcomes
- it touches multiple modules (API + scoring + docs + frontend) without a small seam
- it can't be demoed until everything is done

Common splits:

- "Define response model" -> "Implement endpoint skeleton" -> "Add scoring logic" -> "Add tests" -> "Add docs"
- "Recommendation endpoint" -> "Echo score v1" -> "Classification rules" -> "Explainability fields"

## Closing rules

Close work when:

- it no longer matches MVP scope (mark as **not planned** with rationale)
- it's a duplicate (link the canonical issue)
- it's stale and superseded (link replacement)

Never close without leaving:

- a short reason
- pointers (links) to the issue(s) that replace it, when applicable

## Duplicate handling

When duplicates are found:

- pick a single canonical issue (best-written, closest to repo truth)
- link duplicates to it and close duplicates
- preserve any useful acceptance criteria by copying it into the canonical issue

## Stale branches and issue mapping

Branch naming (recommended):

- `epic/<short-name>`
- `story/<issue-number>-<short-name>`
- `docs/<issue-number>-<short-name>`
- `tooling/<short-name>`
- `fix/<issue-number>-<short-name>`

Rules:

- Every non-trivial branch should reference an issue number (except small tooling/docs when no issue exists yet).
- If a branch exists without an issue: create a small "tracking issue" or delete the branch if abandoned.
- If an issue is In Progress without a branch: either create the branch or move the issue back to Ready/Backlog.

