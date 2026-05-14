# Backlog Refinement Playbook (EchoFinder)

Backlog refinement keeps work small and ready to execute without surprise scope.

## Refinement checklist

For each candidate issue:

- Is the title specific and scoped?
- Is it within MVP guardrails?
- Does it have problem + value?
- Are acceptance criteria testable and complete enough?
- Is the size <= L (XL must be split)?
- Are dependencies explicit?
- Is validation defined (tests/manual)?
- Are labels, priority, size set?

If any answer is "no", the output of refinement is: **add missing info** or **split** or **defer/close**.

## Splitting guide (common patterns)

- **Contract first**: "Define model" before "Implement logic".
- **Pure core first**: extract "pure functions + tests" before wiring to API.
- **Docs as separate slice** when it's more than a quick update.
- **Spikes** when uncertainty is high: time-box and require an artifact.

## Ambiguity questions (ask early)

- What is the minimal "truthful" behavior for MVP?
- What does the endpoint return when sources are empty or inconsistent?
- What data do we trust? What do we label as "unknown"?
- What should be explainable in the response?
- What is the smallest demo that proves value?

## Duplicate detection

Look for issues with:

- same nouns ("recommendations endpoint", "echo score")
- overlapping acceptance criteria
- same files/modules likely to be touched

Prefer consolidating to a single "best" issue and closing duplicates.

## Stale issue handling

If an issue is stale:

- confirm it still aligns with `docs/mvp-roadmap.md`
- update its description to match current repo reality
- split it if it grew too broad
- close as "not planned" if it's out of scope

## Scope creep detection

Warning signs:

- adding OAuth, accounts, playlists "because it's needed"
- switching to embeddings/vector DB before Echo Score v1 is defined
- adding new discovery inputs before the first input is truthful
- adding lots of UI polish before backend contracts exist

When detected:

- create a separate "post-MVP" issue or "stretch" label
- keep the current MVP issue narrow and deliverable

