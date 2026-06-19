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

## Issue lifecycle

1. **Backlog**: captured, but not ready to start.
2. **Ready**: meets `definition-of-ready.md`.
3. **In Progress**: active work; has a branch (ideally) and current status note.
4. **Review**: PR exists and is awaiting review/validation.
5. **Pending Release**: merged into `test-main`, reviewed, QA'd, and waiting for the next `main` release batch.
6. **Done**: released to `main`; validation evidence is present.

Expected project board path:

```text
Backlog -> In Progress -> Review -> Pending Release -> Done
```

**Blocked** is an exception status for work that cannot proceed. Write the blocker down before moving an item there.

Board movement should be hands off during normal work:

- Create issues with `scripts/product-ops/create-project-issue.ps1` so they land on the project board in **Backlog**.
- Move active issues through lifecycle automation when work starts, PRs open, PRs merge, and releases validate.
- Use manual board edits only to correct automation failures or intentionally re-triage work.

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

Use the issue creation helper from the repository root:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\product-ops\create-project-issue.ps1 `
  -Title "Docs: Document MVP refactor scope and non-goals" `
  -BodyFile .\path\to\issue-body.md `
  -Labels "type:docs","ws:docs","prio:P0"
```

The helper creates the issue, adds it to the GitHub Project board, and sets Status to **Backlog**.

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

When closing a completed (not rejected) issue, the issue body must include:

- **Delivered by:** PR #N (or commit hash for non-PR workflows).

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

