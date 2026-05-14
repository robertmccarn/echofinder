# Manual MVP Refactor Epic

EchoFinder is shifting from an API-discovery prototype toward a constrained solo-developer MVP. The goal is to validate whether manually curated "modern echo" recommendations can feel emotionally meaningful before adding scale, automation, or social features.

This document is the scope contract for the refactor. It should guide issue planning, PR review, and README updates until the manual MVP is complete.

## MVP Constraints

The manual MVP is intentionally small:

- Single-user workflow.
- Local/manual curation of legacy artists and modern candidates.
- No AI, ML, embeddings, or vector search.
- No multi-user accounts, community features, or playlist creation.
- No production deployment target.
- No Next.js frontend until the backend data and recommendation contracts are truthful.

The MVP should answer one product question:

> Can a small, carefully tagged dataset produce recommendations that feel emotionally, lyrically, sonically, and scene-wise meaningful?

## In Scope

- Richer manual artist schema.
- Canonical legacy artist seed dataset.
- Expanded modern candidate dataset.
- Controlled manual tagging taxonomy.
- Dataset validation script.
- Rule-based Echo Score model using local/manual tags.
- Recommendation ranking script.
- FastAPI read endpoints for local MVP data.
- Validation journal template for listening notes.
- README and docs updates that match actual repo behavior.

## Out Of Scope

- AI/ML recommendation models.
- Embeddings or pgvector.
- Postgres or production persistence.
- Multi-user accounts.
- Spotify playlist creation.
- Next.js frontend.
- Community/social features.
- Production deployment.

## Relationship To The Existing Prototype

The current Spotify, MusicBrainz, and Last.fm scripts remain useful as research artifacts and possible future enrichment tools. They are no longer the primary MVP path.

For this refactor:

- Local JSON datasets are the source of truth.
- No API credentials should be required to validate data or score recommendations.
- API-driven discovery should be documented as experimental or previous-prototype work.
- Existing prototype scripts should keep running unless a later issue explicitly deprecates or archives them.

## Branch And Review Workflow

Use the existing repository workflow. Board movement should be hands off during normal work; status changes should come from issue creation, PR lifecycle automation, merge automation, and release validation rather than manual board dragging.

- Create each MVP refactor issue and place it in `Backlog`.
- Pick up one issue at a time and move it to `In Progress`.
- Create a small feature branch from `test-main`.
- Make and locally verify the changes for that issue.
- Open a PR targeting `test-main`.
- Run the PR review automation and self-approve when it returns an approval-ready result.
- Merge reviewed work into `test-main`.
- Move the linked issue to `Pending Release` after it is reviewed, QA'd, and integrated into `test-main`.
- Validate release readiness after 10 reviewed commits, then release to `main`.

Each issue should leave the repository in a runnable state. If an issue intentionally defers behavior, the README or relevant docs should say so clearly.

## Implementation Sequence

1. Document MVP refactor scope and non-goals.
2. Add canonical legacy artist dataset.
3. Expand modern candidate schema.
4. Add controlled tagging taxonomy.
5. Implement dataset validation script.
6. Refactor Echo Score to the manual weighted model.
7. Add recommendation ranking script.
8. Add FastAPI recommendation endpoints.
9. Add validation journal template.
10. Update README to reflect MVP reality.

## Definition Of Done For The Refactor

The refactor is complete when:

- A local user can validate the datasets without external API credentials.
- A local user can score recommendations for Manchester Orchestra, Thrice, and The Decemberists.
- FastAPI exposes health, legacy artist, and recommendation read endpoints.
- Recommendation output includes score, explanation, Spotify URL, tags, and curator notes.
- The validation journal provides a repeatable way to judge recommendation quality.
- README setup and commands describe the manual MVP path first.
