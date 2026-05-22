# MVP Scope Guardrails (EchoFinder)

EchoFinder is learning-first and portfolio-ready. MVP must stay narrow.

## MVP includes (in scope)

- Artist-based search (legacy seed artist/band)
- FastAPI backend foundation
- Recommendation endpoint
- Echo Score v1 (transparent rules-based v1)
- "Modern Echo" vs "Bridge Artist" classification
- Explainable recommendation results (why it was recommended)
- Manual candidate pool (explicit contract + documented limitations)
- Spotify artist links (catalog references, not login)
- Basic frontend (minimal UI to exercise the backend) after backend recommendation contracts are truthful
- Basic tests and/or documented manual validation
- Demo-ready documentation

## MVP excludes (out of scope for now)

- Spotify OAuth/login
- Playlist creation/export
- User accounts/profiles
- Personalization from listening history
- Full genre/scene discovery mode expansions
- pgvector/vector embeddings/advanced ML similarity
- Production deployment / hosting

## Scope clarification

For the current manual MVP refactor phase, Next.js frontend implementation remains deferred.
This aligns with `docs/mvp-refactor-epic.md`, which keeps frontend work out of scope until backend data contracts and recommendation behavior are stable and validated.

## Post-MVP candidates (explicitly deferred)

- Saved searches
- Candidate pool automation / enrichment jobs
- Better ranking and calibration (still explainable)
- Caching/persistence layer (only when needed)
- Frontend polish and UX iteration

## Scope creep warning signs

- "We should add OAuth now so it feels real"
- "Let's add a database before the response contract is stable"
- "We should do embeddings because it's modern"
- "Let's add genre and scene discovery before artist discovery is solid"

## Decision rules (accept/reject new work)

Accept into MVP only if:

- it directly supports the MVP included list
- it reduces uncertainty for the recommendation contract
- it improves truthfulness, explainability, or demo readiness
- it can be done as a small issue (<= L)

Otherwise:

- label as `prio:Stretch` or create a post-MVP issue
- keep current sprint focused on P0/P1 MVP enablers

