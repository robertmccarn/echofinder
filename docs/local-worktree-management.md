# Local Repository Boundary

EchoFinder development must use one local repository folder only:

```text
Z:\__Swap_Space__\EchoFinder
```

## Absolute Rule

- Do not create or use any additional `EchoFinder*` folders.
- Do not create Git worktrees for EchoFinder.
- Do not run review, lifecycle, or QA scripts from any folder other than the canonical repository root.

## Cleanup Rule

If any extra `EchoFinder*` folders appear under `Z:\__Swap_Space__`, treat that as drift and remove them after confirming no required local-only work exists.

## Validation Rule

Before starting work, confirm only one EchoFinder directory exists:

```powershell
Get-ChildItem Z:\__Swap_Space__ -Directory | Where-Object { $_.Name -like 'EchoFinder*' }
```

Expected result: only `EchoFinder`.
