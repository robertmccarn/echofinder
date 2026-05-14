# PR Review Automation

EchoFinder includes a local PowerShell helper for repeatable pull request review. The helper inspects a PR, finds or checks out the review branch, runs validation based on changed files, and prints a review recommendation.

The script assists review. It does not approve, merge, close issues, delete worktrees, or push changes.

## Command

Run from the repository root:

```powershell
.\scripts\review-pr.ps1 -PrNumber 22
```

If the local PowerShell execution policy blocks script execution, use:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\review-pr.ps1 -PrNumber 22
```

Common options:

```powershell
.\scripts\review-pr.ps1 `
  -PrNumber 22 `
  -Repo robertmccarn/echofinder `
  -BaseBranch test-main `
  -WorktreeRoot Z:\__Swap_Space__
```

Optional flags:

- `-SkipCheckout`: use the current checkout if no matching worktree is found.
- `-DocsOnly`: force docs-only classification.
- `-VerboseReview`: reserved for more detailed future checks.
- `-OutputMarkdown <path>`: save the review report to a Markdown file.
- `-PostComment`: post the report as a PR comment. This only happens when explicitly passed.
- `-MoveBoard`: move linked issues on the GitHub Project board. This only happens when explicitly passed.
- `-BoardStatus <status>`: target board status. Defaults to `Review`.
- `-ProjectOwner <owner>` and `-ProjectNumber <number>`: project board location. Defaults to `robertmccarn/2`.
- `-DryRun`: show intended board movement without changing the board.

## What It Checks

The script verifies local tooling, GitHub CLI authentication, PR metadata, the expected base branch, changed files, and changed-file categories.

It always runs:

- `git status --short`
- `git diff --check`
- `git diff --check origin/<base>...HEAD` when the remote base exists, otherwise `<base>...HEAD`

For docs-only changes, it confirms changed Markdown files exist and checks local Markdown links for obvious broken relative paths.

For backend/Python changes, it runs:

- `python -m compileall backend`
- `pytest` when pytest-style tests exist and `pytest` is available

For frontend changes, it detects package manager files but does not install dependencies or run broad frontend commands unless the project documents those commands.

## Workflow Fit

EchoFinder uses `test-main` as the active reviewed integration branch and `main` as the stable release branch. PR review automation should validate feature and Codex PRs against `test-main` unless the task is explicitly reviewing release state.

Use the helper before approving a PR into `test-main`. A passing helper report is review evidence, not an automatic approval.

## Recommendations

The script prints one of these recommendations:

- `APPROVE_READY`: automated checks passed and no obvious scope or risk notes were found.
- `NEEDS_MANUAL_REVIEW`: checks passed, but the reviewer should inspect a risk note, draft state, branch mismatch, or scope question.
- `REQUEST_CHANGES`: validation failed or a sensitive-looking change was detected.

## Board Movement

By default, the helper reports what it would do with linked issues and does not change the GitHub Project board.

To move linked issues after a successful review check, pass `-MoveBoard`:

```powershell
.\scripts\review-pr.ps1 `
  -PrNumber 22 `
  -Repo robertmccarn/echofinder `
  -BaseBranch test-main `
  -MoveBoard `
  -BoardStatus Review
```

Use `-DryRun` first when testing a board move:

```powershell
.\scripts\review-pr.ps1 `
  -PrNumber 22 `
  -Repo robertmccarn/echofinder `
  -BaseBranch test-main `
  -MoveBoard `
  -DryRun
```

The helper finds linked issues from GitHub closing references and PR body keywords such as `Closes #21`. If a linked issue is not already on the configured project, `-MoveBoard` adds it before setting the Status field.

If validation recommends `REQUEST_CHANGES`, board movement is skipped even when `-MoveBoard` is passed.

## Safety Rules

- The script never auto-approves a PR.
- The script never auto-merges a PR.
- The script never closes linked issues.
- The script never deletes worktrees.
- The script does not print token values or credential contents.
- The script only posts a PR comment when `-PostComment` is explicitly passed.
- The script only changes GitHub Project board status when `-MoveBoard` is explicitly passed.

## Example: PR #22

```powershell
.\scripts\review-pr.ps1 `
  -PrNumber 22 `
  -Repo robertmccarn/echofinder `
  -BaseBranch test-main
```

For PR #22, the expected classification is docs-only. The helper should run whitespace/link checks and skip backend validation because no backend or application code changed.
