# Learning-First Development

EchoFinder is a learning-first project. The goal is not only to build a music discovery app, but to make the technical path understandable.

## Principles

- Explain why decisions are made.
- Prefer small, reviewable changes.
- Keep prototype code readable before making it abstract.
- Document tradeoffs and limitations honestly.
- Label planned features as planned until implemented and validated.
- Avoid fake implementations that appear real to users.

## Code Comments

Use comments when they help a reader understand non-obvious API behavior, scoring choices, data limitations, or workflow constraints.

Avoid comments that simply repeat the code.

Good comments explain context:

```python
# MusicBrainz begin dates are imperfect, but they are less prone to re-release noise than Spotify album dates.
```

Weak comments repeat syntax:

```python
# Set score to zero
score = 0
```

## Documentation Standard

Every major change should leave behind enough context for the next contributor or Codex session to continue safely:

- What exists now.
- What is planned.
- What was intentionally not changed.
- What validation was run.
- What assumptions remain risky.

## Scope Discipline

When a task is backend-only, do not add frontend behavior.

When a task is docs-only, do not change application behavior.

When a task depends on live APIs, provide mocks or clear skip reasons unless the issue explicitly asks for live validation.

## Truthfulness

EchoFinder should not claim:

- Spotify login exists before OAuth is implemented.
- Playlists can be created before playlist creation exists.
- `/api/recommendations` exists before the endpoint is implemented.
- Database or pgvector behavior exists before runtime integration exists.

Truthful docs make the project easier to learn from and safer to evolve.
