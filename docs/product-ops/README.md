# EchoFinder Product Ops (PO/BA/SM)

This folder is a lightweight "operating system" for running EchoFinder as a solo, learning-first project while still getting the benefits of:

- clear MVP scope
- high-quality GitHub Issues
- predictable small batches of work
- consistent acceptance criteria and definitions of done
- clean project board hygiene

It is designed to be used by a human (you) and/or an AI coding agent (Codex) acting as a combined:

- Product Owner (PO)
- Business Analyst (BA)
- Scrum Master (SM)
- Backlog grooming assistant
- Sprint planning assistant
- Issue quality reviewer
- Project board hygiene agent

## What this system does

- Defines EchoFinder-specific issue types, labels, sizes, and status rules.
- Provides Definition of Ready / Done gates to keep work truthful and demo-able.
- Provides playbooks for refinement, sprint planning, board sync, and release readiness.
- Provides copy/paste prompts in `docs/product-ops/prompts/` for repeatable agent work.

## What this system does *not* do

- It does not invent product scope beyond the MVP guardrails.
- It does not "mark done" based on intent; it requires repo evidence.
- It does not move GitHub Project board state by default (unless explicitly instructed and tooling supports it).
- It does not create/close GitHub issues unless explicitly instructed.

## When to use Product Ops

Use this system when you want to:

- turn roadmap bullets into actionable issues
- split a large vague item into smaller, shippable stories
- plan a realistic solo-dev sprint
- review issue quality before starting work
- reconcile "what's in the repo" with GitHub Issues / Project board state
- do an MVP/milestone readiness check before demoing

## Decision rights (what the agent may decide)

The agent may decide, without escalation:

- issue wording improvements, acceptance criteria additions, and splitting suggestions
- size estimates (XS-XL) with justification
- recommended priority (P0/P1/P2/Stretch) with rationale
- proposed sequencing and dependency ordering
- suggested label sets according to `issue-taxonomy.md`

The agent must escalate (ask you) before:

- expanding MVP scope boundaries (`mvp-scope-guardrails.md`)
- changing API contracts or endpoints in ways that break earlier docs/tests
- adding persistent infrastructure (DB, queues), auth, personalization, or production deployment
- changing the canonical project board statuses/priorities/sizes

## Start here

1. Read the charter: `docs/product-ops/agent-charter.md`
2. Align on MVP boundaries: `docs/product-ops/mvp-scope-guardrails.md`
3. Use the prompts in `docs/product-ops/prompts/` to create/refine issues
4. Before you start a story, confirm it meets `docs/product-ops/definition-of-ready.md`
5. Before you mark done, confirm `docs/product-ops/definition-of-done.md`

## Recommended cadence (solo-dev)

- Weekly (or per work block): run backlog refinement and select 1-3 items.
- During work: keep WIP at 1 (2 max) and keep issues small.
- End of work block: update the issue and board status to match reality, not aspiration.

## GitHub Write Strategy

Use `gh` CLI as the primary GitHub write path for Product Ops automation. Connector/API writes may fail with 403 "Resource not accessible by integration"; treat that as a known limitation, not a blocker, when `gh` succeeds.

Connector/API access may be used for read-only convenience unless write capability is proven later. Daily and Weekly automations should prefer `gh issue edit`, `gh issue comment`, `gh pr comment`, `gh label list`, `gh label create`, and `gh project` commands when project access is available. Do not rewrite the canonical taxonomy because connector writes fail. If both `gh` and connector writes fail, report read-only mode and provide manual commands.

