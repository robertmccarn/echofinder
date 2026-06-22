# Project Board Sync Playbook (EchoFinder)

Goal: keep GitHub Issues / Project board status aligned with **repo truth** through automation-first lifecycle movement.

Repository boundary rule: run Product Ops automation from the active EchoFinder repository root or an EchoFinder worktree rooted in the same repository. Do not run these commands from unrelated sibling folders or stale repo copies.

## Inputs (source of truth order)

1. repository state (merged code/docs)
2. PRs and branches
3. GitHub Issues and Project board
4. roadmap/docs

## How to compare repo state vs issue state

For each In Progress / Review / Done issue:

- Is there a branch or PR tied to it?
- Is there a merged commit/PR that satisfies acceptance criteria?
- Is there validation evidence recorded?
- Do docs match the implemented behavior?

## Status update rules

- Create issues into **Backlog** with `scripts/product-ops/create-project-issue.ps1`.
- Move to **In Progress** when a branch exists and active work starts.
- Move to **Review** when a PR exists and checks/validation are pending.
- Move to **Pending Release** only when the PR is reviewed, QA'd, merged into `test-main`, and post-merge validation passes.
- Move to **Done** only when released to `main` and release validation passes.
- Keep `Priority` and `Workstream` board fields aligned with the issue's canonical `prio:*` and `ws:*` labels.

Expected path:

```text
Backlog -> In Progress -> Review -> Pending Release -> Done
```

Manual board edits are exceptions. Use them only to repair automation failures, unblock stale items, or intentionally re-triage work.

## Field consistency rules

- `Status` is lifecycle-driven.
- `Priority` should mirror one canonical priority label (`prio:*`).
- `Workstream` should mirror one primary workstream label (`ws:*`).
- Avoid leaving `Priority` or `Workstream` blank when an issue is active on the board.
- If legacy labels conflict with canonical labels, preserve legacy labels for history but set board fields from canonical labels.

## When not to update statuses

Do not "optimistically" move items forward because:

- a branch exists
- code "looks finished"
- a PR is open but not merged
- validation hasn't run (or reason not recorded)
- the item reached `test-main` but has not been released to `main`

## Branches without issues

If a branch exists without a tracking issue:

- create a small tracking issue (type:task or type:docs) if work is non-trivial
- or delete the branch if abandoned

## Issues without branches

If an issue is In Progress but no branch exists:

- move it back to Ready (or Backlog) unless active work is happening
- create the branch when work actually begins

## Automation commands

Create a project-backed issue in **Backlog**:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\product-ops\create-project-issue.ps1 `
  -Title "Issue title" `
  -BodyFile .\issue-body.md
```

Move a picked-up issue to **In Progress**:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\product-ops\set-project-status.ps1 `
  -IssueNumber <number> `
  -BoardStatus "In Progress"
```

Run full PR lifecycle after opening a PR:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\pr-lifecycle.ps1 `
  -PrNumber <number> `
  -AutoApprove `
  -AllowSelfApproval `
  -AutoMerge `
  -ValidateAfterMerge `
  -MoveBoard `
  -PostComment
```

## Sync report format (recommended)

Produce a short report with:

- items moved to Backlog/In Progress/Review/Pending Release/Done (with reasons)
- items blocked (and what's blocking)
- stale items recommended for split/close
- 1-3 recommended next items based on current priority
- field-drift summary:
  - issues where `Priority` field mismatched `prio:*`
  - issues where `Workstream` field mismatched primary `ws:*`

