# Project Board Sync Playbook (EchoFinder)

Goal: keep GitHub Issues / Project board status aligned with **repo truth**.

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

- Move to **Ready** only when Definition of Ready is met.
- Move to **In Progress** when a branch exists and active work starts.
- Move to **Review** when a PR exists and checks/validation are pending.
- Move to **Done** only when merged + validated + docs updated (Definition of Done).

## When not to update statuses

Do not "optimistically" move items to Done because:

- a branch exists
- code "looks finished"
- a PR is open but not merged
- validation hasn't run (or reason not recorded)

## Branches without issues

If a branch exists without a tracking issue:

- create a small tracking issue (type:task or type:docs) if work is non-trivial
- or delete the branch if abandoned

## Issues without branches

If an issue is In Progress but no branch exists:

- move it back to Ready (or Backlog) unless active work is happening
- create the branch when work actually begins

## Sync report format (recommended)

Produce a short report with:

- items moved to Ready/In Progress/Review/Done (with reasons)
- items blocked (and what's blocking)
- stale items recommended for split/close
- 1-3 recommended next items based on current priority

