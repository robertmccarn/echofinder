# EchoFinder Development Workflow

EchoFinder uses a staged branch workflow so active development can be reviewed and stabilized before being released to `main`.

Validate active work against `test-main`. Validate release state against `main`.

## Branch Roles

### `main`

`main` is the stable release branch.

Use `main` when checking the current released state of the project. Do not assume active work is missing simply because it has not reached `main` yet.

### `test-main`

`test-main` is the active reviewed integration branch.

Use `test-main` when validating current completed work, recently reviewed commits, and issue acceptance criteria.

### Feature or Codex Branches

Feature/Codex branches are short-lived branches used for individual issues or small related batches of work.

A feature branch should usually target one issue. Larger changes should be split into smaller reviewable issues when possible.

## Standard Flow

1. Create the issue and place it in **Backlog**.
2. Pick up the issue and move it to **In Progress**.
3. Create or use a feature/Codex branch from `test-main`.
4. Implement one issue or a clearly related small set of changes.
5. Run local validation or document why validation could not be run.
6. Open a PR targeting `test-main`.
7. Run the PR review automation.
   - Confirm linked issue Acceptance Criteria and Validation checklists are checked.
8. Self-approve the PR when review automation returns an approval-ready result.
9. Merge reviewed work into `test-main`.
10. Move the issue to **Pending Release** after review, QA, merge, and post-merge validation are complete.
11. Count the reviewed commit toward the release batch.
12. Release from `test-main` to `main` only after 10 successfully reviewed commits are accumulated.

Project board movement should be hands off during normal work. Use repository and lifecycle automation to move issues through **Backlog**, **In Progress**, **Review**, **Pending Release**, and **Done**. Manual board edits are reserved for correcting automation failures or explicitly re-triaging work.

## Validation Rules

Active work should be validated against `test-main`, not `main`, unless the task is explicitly reviewing release state.

If work exists on `test-main` but not `main`, its status should be:

> Implemented on `test-main`, not yet released to `main`.

Do not mark an issue incomplete only because the change is missing from `main`.

## Local Repository Rule

Use one local repository only:

```text
Z:\__Swap_Space__\EchoFinder
```

Do not create or use additional `EchoFinder*` folders or worktrees. All development, QA, lifecycle, and board-automation commands must run from this canonical repository root.

## Successfully Reviewed Commit

A commit counts as successfully reviewed when:

- The change satisfies the related issue acceptance criteria.
- Validation commands have been run, or missing validation is explicitly documented.
- The reviewer has checked for scope creep.
- Documentation was updated when behavior, setup, or workflow changed.
- The commit has been merged into `test-main`.

## Project State Model

EchoFinder uses these statuses to track work across the integration and release branches:

- **Backlog**: Work that is not yet ready to start or is pending refinement.
- **Ready**: Refined work that is ready for implementation.
- **In Progress**: Active implementation or research.
- **Review**: Work with an open PR targeting `test-main`.
- **Pending Release**: Work merged into `test-main` but not yet released to `main`.
- **Done**: Work released to the stable `main` branch or otherwise explicitly considered complete.

Expected status path:

```text
Backlog -> In Progress -> Review -> Pending Release -> Done
```

The board should follow the issue and PR lifecycle automatically wherever possible:

- Issue created: **Backlog**.
- Issue picked up: **In Progress**.
- PR opened against `test-main`: **Review**.
- PR reviewed, QA'd, merged to `test-main`, and post-merge validated: **Pending Release**.
- Release validated and merged to `main`: **Done**.

## Issue Done Rules

An issue should only move to **Done** when it has reached the stable `main` branch.

Work that has been integrated into `test-main` but is waiting for a release batch should stay in **Pending Release**.

An issue satisfies "Done" criteria when:
- Acceptance criteria are satisfied on `main`.
- Validation evidence is present.
- Documentation is accurate for the release state.
- No unresolved review feedback remains.

## Validation Evidence Format

Use this format in issue comments, PR summaries, or Codex completion notes:

```text
Validation
- Branch validated:
- Commands run:
- Result:
- Not run:
- Reason not run:

Status
- Implemented on test-main:
- Released to main:
```

## Release Rule

EchoFinder releases to `main` only after 10 successfully reviewed commits have accumulated on `test-main`.

Before release, confirm:

- The 10 reviewed commits are present on `test-main`.
- No known blocking issues remain.
- Required validation evidence exists.
- README and docs are accurate for the release state.
