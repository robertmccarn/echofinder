# Development Workflow

EchoFinder uses `test-main` for active, reviewed integration work and `main` for stable releases. When checking whether work exists, validate against the branch that matches the question: active work lives on `test-main`; released work lives on `main`.

## Branch Roles

### `main`

`main` is the stable release branch.

- Only merge release PRs into `main`.
- Do not merge individual feature, docs, or Codex task PRs directly into `main`.
- Use `main` to inspect released behavior and release documentation.
- Tag releases after a release PR lands on `main`.

### `test-main`

`test-main` is the active reviewed integration branch.

- Feature, docs, bug fix, and Codex task PRs target `test-main`.
- Validate completed work on `test-main`.
- Keep reviewed work here until the release rule is met.
- Use `test-main` to inspect active accepted work that has not been released yet.

### Feature and Codex Branches

Work starts from `test-main` on a short-lived branch.

Recommended branch names:

```text
feature/issue-123-short-description
fix/issue-123-short-description
docs/issue-123-short-description
codex/issue-123-short-description
```

Codex branches follow the same rules as human-authored branches. They must be reviewed, validated, and merged to `test-main` before they count toward a release.

## Commit Flow

Use this flow for normal project work:

```text
test-main -> feature branch -> PR review -> test-main -> release PR -> main
```

Use this flow for releases:

```text
test-main -> release PR -> main -> release tag
```

If `test-main` and `main` disagree, that is expected between releases. `test-main` shows integrated work waiting for release; `main` shows what has actually been released.

## PR and Review Expectations

Every task PR should target `test-main` and include:

- Summary of the change.
- Issue number or purpose.
- Validation commands and results.
- Scope guardrails showing what was intentionally not changed.

A successfully reviewed commit is a commit that:

- Landed on `test-main` through a PR or an explicit reviewed equivalent.
- Has a clear reviewer or owner check, even for solo work.
- Has validation evidence appropriate to the change.
- Does not include unrelated changes hidden in the same commit.
- Leaves known gaps documented instead of implied complete.

For Codex work, the review may be a human review, a deliberate owner review, or an explicit validation pass by another Codex session, as long as the result is recorded in the PR, issue, or project notes.

## Validation Expectations

Validate on the branch where the work is being accepted. For active work, that means `test-main`.

Before an issue can be marked complete, record:

- Branch and commit tested.
- Commands run.
- Results observed.
- Any manual checks performed.
- Any acceptance criteria that could not be verified.

Validation should match the risk of the change. Documentation changes may only need review and link checks. Backend changes should run compile or test commands plus any endpoint checks listed in the issue. Release validation should happen from the release candidate state of `test-main`.

## Release Cadence

Release to `main` only after 10 successfully reviewed commits have accumulated on `test-main`.

The 10-commit rule protects `main` from becoming another integration branch. Exceptions should be rare and explicit, such as a critical fix, broken release state, or a demo milestone that the owner approves.

A release PR from `test-main` to `main` should include:

- List of reviewed commits included in the release.
- Summary of delivered behavior.
- Release validation evidence.
- Known limitations or blocked items.
- Planned version tag.

## Issue Closure

Do not close an issue just because the change is absent or present on `main`.

Use this rule:

- Move to Review when the work is merged to `test-main` but still needs validation or cleanup.
- Move to Pending Release when the work is validated on `test-main` but not yet released to `main`.
- Move to Done when the issue satisfies its acceptance criteria and the project's release policy says it is complete.

If an issue's acceptance criteria require released behavior, close it only after the release PR lands on `main`. If the issue explicitly accepts integration-level completion, it may be closed after validation on `test-main`, but that exception should be written down.
