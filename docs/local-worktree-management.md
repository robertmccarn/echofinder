# Local Worktree Management

Use one canonical local checkout for EchoFinder:

```text
Z:\__Swap_Space__\EchoFinder
```

Temporary worktrees are useful for isolated review or implementation, but they should be created intentionally and removed after use.

## Naming

Use this pattern:

```text
EchoFinder-wt-pr-<number>-<short-name>
```

Examples:

```text
EchoFinder-wt-pr-22-issue21-workflow
EchoFinder-wt-pr-25-roadmap-docs
```

Avoid random duplicate folders such as:

```text
EchoFinder-docs-workflow
EchoFinder-test-main-review
EchoFinder-remediate-main
```

## Cleanup

Before removing a worktree, verify it is clean:

```powershell
git status --short
git log -1 --oneline
```

Remove completed worktrees from the canonical repo:

```powershell
git worktree remove Z:\__Swap_Space__\EchoFinder-wt-pr-<number>-<short-name>
git worktree prune
```

Do not use raw recursive deletion for registered worktrees.

Do not touch unrelated projects under `Z:\__Swap_Space__`, including `SellThrough`.

## Branch Context

Validate active work against `test-main`.

Validate released state against `main`.

Create feature/Codex branches from `test-main` and target PRs back to `test-main`.
