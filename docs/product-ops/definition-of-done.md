# Definition of Done (EchoFinder)

An issue is **Done** only when it is truthful in the repository and demo-able in the current project stage.

## Implementation completeness

- Acceptance criteria are satisfied.
- No known broken behavior is introduced in touched areas.
- Edge cases called out in the issue are handled or explicitly deferred.

## Tests / validation

At least one is true (and recorded in the issue or PR):

- automated tests added/updated and passing (preferred)
- local validation command run and recorded (e.g., `pytest`, `python -m compileall backend`)
- manual validation steps completed and recorded (curl examples, sample outputs)

If tests cannot be run, the reason is stated (missing tool, no tests in repo yet, etc.).

## Docs

- Docs updated when behavior/contracts change (or explicitly "no docs change needed").
- Any new endpoints have at least minimal docs: purpose + inputs + outputs + examples.
- Learning-first note added when a decision was made (why, not just what).

## Branch/PR hygiene

- Work is merged (or committed on the target branch for non-PR workflows).
- No temporary scratch files are committed.
- `git diff --check` is clean (no whitespace errors).

## Project board and issue hygiene

- Issue status is moved to **Done** only after merge + validation evidence.
- Issue references the PR/commit(s) that delivered it.
- Any follow-up work is captured as new issues (not hidden in comments).

## Demo/readme impact

If the change affects what can be demoed locally:

- update the relevant docs (and/or root README docs list) to stay truthful
- note any known limitations clearly

