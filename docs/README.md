# EchoFinder Docs

This directory keeps EchoFinder's product, architecture, workflow, and learning notes aligned with what is actually implemented.

## Product And Architecture

- [Manual MVP Refactor Epic](./mvp-refactor-epic.md): scope contract for the solo-developer manual MVP refactor.
- [Product Vision](./product-vision.md): problem, users, core terms, and product boundaries.
- [Current Architecture](./current-architecture.md): source of truth for implemented components and the transition path.
- [MVP Roadmap](./mvp-roadmap.md): backend-first path from prototype scripts to usable MVP.
- [Design Summary](./design-summary.md): early concept notes; read alongside [Product Vision](./product-vision.md) for current 0–5 year scope.
- [Architecture Notes](./architecture-notes.md): earlier architecture ideas; [Current Architecture](./current-architecture.md) is the source of truth for implemented vs planned state.

## Development Workflow

- [Development Workflow](./development-workflow.md): branch roles, project state model (Pending Release), and release cadence.
- [PR Review Automation](./pr-review-automation.md): local PR review helper and lifecycle automation workflow.
- [Local Worktree Management](./local-worktree-management.md): canonical repo/worktree naming and cleanup rules.

## Product Ops (PO/BA/SM)

- [Product Ops README](./product-ops/README.md): how to run the Product Ops agent system.
- [MVP Scope Guardrails](./product-ops/mvp-scope-guardrails.md): what’s in/out of MVP.
- [Definition of Ready](./product-ops/definition-of-ready.md): gate for “Ready” issues.
- [Definition of Done](./product-ops/definition-of-done.md): gate for “Done” issues.
- [Prompts](./product-ops/prompts/): copy/paste prompts for issue creation, refinement, and planning.

## Learning And Research

- [Learning-First Development](./learning-first-development.md): standards for transparent, incremental development.
- [Learning Goals](./learning-goals.md): project learning objectives.
- [API Research Notes](./api-research-notes.md): research context; note that older cutoff assumptions are historical.

## Planned Docs

These topics are intentionally tracked as issues until the implementation is stable enough to document truthfully:

- Echo Score model contract.
- API keys and local run guide.
- Manual candidate pool contract.
- Testing strategy.
- MVP demo script and manual QA checklist.
