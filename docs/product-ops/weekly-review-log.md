# EchoFinder Weekly Review Log

Lightweight durable record of what the weekly PO/BA/SM automation executed.

---

## 2026-06-21 (America/Chicago)

**Selected action:** Normalize Phase 2 parent issue #129 as a backlog epic container.

**What changed (GitHub):**
- Updated #129 labels from `type:story`/`ws:backend` to `type:epic`, `ws:frontend`, `size:XL`, `codex`, and `codex-automation`.
- Added a refinement comment documenting that #129 is a parent tracker, not a directly executable Ready story.
- Moved #129 from `Ready` to `Backlog` on the EchoFinder Project Board.

**What changed (repo):**
- Updated this weekly review log on the existing Product Ops documentation PR branch.

**Validation:**
- `gh issue view 129 --repo robertmccarn/echofinder`
- `gh project item-list 2 --owner robertmccarn --limit 100 --format json`
- `git diff --check`
- `powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\product-ops\check-doc-links.ps1`

**Next recommended focus:**
- Continue Phase 2 execution through child issue #132 after current #131 review/closure, keeping #129 as the parent backlog tracker.

## 2026-06-19 (America/Chicago)

**Selected action:** Product Ops documentation truth pass for current automation and board workflow.

**What changed (GitHub):**
- Reviewed open PRs, recently merged PRs, open issues, and issues #40-#45.
- Confirmed the current label set includes `type:test`, `ws:testing`, `codex-automation`, and other workflow labels not fully captured in Product Ops docs.
- Prepared follow-up issue comments to record the docs alignment outcome against Product Ops backlog items.

**What changed (repo):**
- Updated Product Ops docs to remove the obsolete hardcoded `Z:\__Swap_Space__\EchoFinder` path rule and allow active EchoFinder worktrees.
- Added missing board/label reality to `docs/product-ops/issue-taxonomy.md`, including `Pending Release`, `type:test`, and currently used optional workflow labels.
- Fixed stale label examples in `docs/product-ops/backlog-governance.md`.
- Aligned `docs/development-workflow.md` and `docs/product-ops/project-board-sync-playbook.md` with the repo's current worktree-based workflow.

**Validation:**
- `git status --short`
- `git diff --check`
- `powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\product-ops\check-doc-links.ps1`

**Next recommended focus:**
- Resolve #41 by verifying live GitHub Project fields/statuses against the newly corrected docs and capturing any remaining board-only drift.

## 2026-05-14 (America/Chicago)

**Selected action:** Label taxonomy alignment + issue labeling for new Product Ops items.

**What changed (GitHub):**
- Labeled new Product Ops issues (#40–#45) using the repository’s existing `priority/P*`, `type/*`, and `workstream/*` labels where possible.
- Added issue comments documenting the current label reality and the preferred “structured label” set to use until `docs/product-ops/issue-taxonomy.md` can be fully reconciled with the repo labels.

**What changed (repo):**
- Updated `docs/product-ops/issue-taxonomy.md` to include a “Current GitHub label reality” section reflecting the labels currently present in the repository.

**Validation:**
- `git status --short`
- `git diff --check`

**Next recommended focus:**
- Resolve #40 by creating the missing `type:*`, `ws:*`, `prio:*`, `size:*`, `codex`, and `codex-automation` labels in GitHub (requires a tool with label-create permissions).

