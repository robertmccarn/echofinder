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

1. Create or use a feature/Codex branch from the current integration base.
2. Implement one issue or a clearly related small set of changes.
3. Run local validation or document why validation could not be run.
4. Review the change for acceptance criteria, scope, and regression risk.
5. Merge reviewed work into `test-main`.
6. Count the reviewed commit toward the release batch.
7. Release from `test-main` to `main` only after 10 successfully reviewed commits are accumulated.

## Validation Rules

Active work should be validated against `test-main`, not `main`, unless the task is explicitly reviewing release state.

If work exists on `test-main` but not `main`, its status should be:

> Implemented on `test-main`, not yet released to `main`.

Do not mark an issue incomplete only because the change is missing from `main`.

## Local Worktree Management

Use `Z:\__Swap_Space__\EchoFinder` as the canonical local repository for EchoFinder.

Create temporary PR worktrees only when they are needed for review or isolated implementation. Put them beside the canonical repo and use this naming convention:

```text
EchoFinder-wt-pr-<number>-<short-name>
```

Examples:

```text
EchoFinder-wt-pr-22-issue21-workflow
EchoFinder-wt-pr-24-setup-docs
```

Avoid random duplicate folders such as `EchoFinder-docs-workflow`, `EchoFinder-test-main-review`, or `EchoFinder-remediate-main` unless there is a clear temporary reason.

After a PR is merged or abandoned, remove the local worktree from the canonical repo:

```powershell
git worktree remove Z:\__Swap_Space__\EchoFinder-wt-pr-<number>-<short-name>
git worktree prune
```

Before removing any worktree, confirm it has no uncommitted or local-only work:

```powershell
git status --short
git log -1 --oneline
```

Do not use raw recursive folder deletion for registered worktrees. Do not touch unrelated projects under `Z:\__Swap_Space__`, such as `SellThrough`.

## Successfully Reviewed Commit

A commit counts as successfully reviewed when:

- The change satisfies the related issue acceptance criteria.
- Validation commands have been run, or missing validation is explicitly documented.
- The reviewer has checked for scope creep.
- Documentation was updated when behavior, setup, or workflow changed.
- The commit has been merged into `test-main`.

## Issue Done Rules

An issue may move to Done when:

- Acceptance criteria are satisfied on `test-main`.
- Validation evidence is posted in the issue, PR, or commit summary.
- Required documentation has been updated.
- There is no unresolved review feedback.
- Any unreleased status is clearly noted when the change has not yet reached `main`.

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
