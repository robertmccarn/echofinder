# CI Governance (GitHub Actions + Branch Protection)

EchoFinder CI is defined in:

- `.github/workflows/test.yml`

Current automated checks:

- Python compile gate: `python -m compileall backend`
- Test gate: `python -m pytest backend/tests -v`

Both run on:

- `pull_request` to `main` and `test-main`
- `push` to `main` and `test-main`

## External API Rule

Automated CI tests must not depend on live credentials or external API calls.

Expected behavior:

- tests pass without Spotify, Last.fm, or MusicBrainz credentials
- external integrations are mocked/stubbed in test paths

## Branch Protection Requirement

To make red PRs block merge, enable branch protection in repository settings.

Recommended protected branches:

- `test-main` (integration gate)
- `main` (release gate)

Recommended required status check:

- workflow job from `.github/workflows/test.yml` (job name: `test`)

Recommended settings:

- Require a pull request before merging
- Require status checks to pass before merging
- Require branches to be up to date before merging
- Do not allow force pushes

## Current State Snapshot

As of this update, GitHub branch protection API returns `Branch not protected` for:

- `main`
- `test-main`

So CI runs are present, but branch-protection enforcement is not yet enabled.

## Validation Commands

```powershell
python -m compileall backend/app backend/scripts backend/tests
python -m pytest backend/tests -q
```

Optional check of workflow file:

```powershell
Get-Content .github/workflows/test.yml
```
