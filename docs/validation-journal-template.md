# Validation Journal Template

Use this template to record human listening validation for EchoFinder recommendations.

Purpose:

- turn recommendation quality into repeatable evidence
- compare results across seeds over time
- support keep/retag/rescore/remove decisions on manual pool and scoring behavior

## Success/Failure Criteria

### Success Criteria

- User can run backend/frontend (or live demo script) and review recommendations.
- Recommendation cards are understandable (score, tags, sources, explanation, emergence year).
- At least one recommendation per tested seed is judged useful enough to save/follow/listen deeper.
- Source/status metadata is visible and truthful (no hidden failures).
- Journal entries are complete enough to support follow-up changes.

### Failure Criteria

- Recommendations are consistently irrelevant across multiple seeds.
- Explanation fields are missing or not credible for user judgment.
- Source/status metadata is absent or misleading.
- User cannot determine clear keep/retag/rescore/remove action.
- Journal cannot be used to identify concrete next improvements.

## Copyable Entry Template

Copy/paste one block per recommendation reviewed:

```markdown
## Validation Session
- Date:
- Reviewer:
- App mode: (frontend | live demo script)
- Seed artist tested:
- Environment: (local/manual only, or with credentials)

### Recommendation Reviewed
- Artist:
- Classification: (modern_echo | bridge_artist)
- Echo Score:
- Emergence Year:
- Sources:
- Source Note:
- Shared Tags:

### Listening Actions
- Listened? (yes/no):
- Saved or followed? (yes/no):
- Opened Spotify link? (yes/no):

### Rating (1-5)
- Emotional fit:
- Sonic fit:
- Lyrical fit:
- Scene/lineage fit:
- Explanation trust:

### Decision
- Decision: (keep | retag | rescore | remove)
- Notes:
- Suggested change:
```

## Session Summary Template

After reviewing multiple recommendations for a seed, capture summary:

```markdown
## Seed Summary
- Seed artist:
- Total recommendations reviewed:
- Keep:
- Retag:
- Rescore:
- Remove:
- Top 2 strongest recommendations:
- Top 2 weakest recommendations:
- Follow-up issue needed? (yes/no):
- Follow-up issue link:
```

## Recommended Usage

- Use at least one canonical seed each session:
  - Manchester Orchestra
  - Thrice
  - The Decemberists
- Record at least 3 recommendation reviews per session where available.
- Convert recurring failure patterns into scoped GitHub issues.
