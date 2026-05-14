# Definition of Ready (EchoFinder)

An issue is **Ready** when it is precise enough to implement in one focused solo-dev work session without discovering major missing requirements mid-stream.

## Required fields (in the issue description)

- **Problem**: what’s missing or wrong, stated clearly.
- **Value**: user value or technical value.
- **Acceptance criteria**: testable statements (not “looks good”).
- **Tasks**: a short checklist of steps/subtasks.
- **Dependencies**: linked issues or decisions required (or explicitly “none”).
- **Priority + size**: `prio:*` and `size:*` assigned with rationale.
- **Labels**: `type:*` and `ws:*` set.

## Acceptance criteria expectations

Acceptance criteria should:

- define success in observable terms
- include at least one negative/edge case when relevant
- avoid over-specifying implementation details unless necessary
- be consistent with MVP scope and existing docs

## Testability and validation readiness

Ready issues state:

- how to validate (unit tests, pytest, manual curl, doc example)
- what “done” evidence looks like (files changed, endpoint response, docs updated)

If automated tests don’t exist for that area yet, the issue must include a manual validation checklist.

## Design/architecture readiness

An issue is not Ready if it requires an architectural decision that hasn’t been made. Use a spike first when needed, and record:

- decision options
- tradeoffs
- chosen direction (or what you’ll measure to choose)

## Blocking conditions (not Ready)

- ambiguous API contract (request/response shape unknown)
- “build everything” scope (XL)
- dependencies not identified
- acceptance criteria missing or non-testable
- conflicts with MVP guardrails

