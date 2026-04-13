# Manual Test Checklist: Robust Dependabot Auto-Approval

**Purpose**: Structured manual validation mapped to acceptance scenarios
**Constitution note**: GitHub Actions workflow logic lacks a standard unit test
framework. This checklist provides structured manual validation to satisfy the
constitution testing requirement (all code MUST have tests) within this
constraint. This is pre-existing across all org-infra workflows and is not
introduced by this feature.

## Prerequisites

- A test repository with the updated workflows deployed
- `make lint` passes before manual testing

## US1: Reliable Auto-Approval for Safe Dependency Updates

| # | Scenario | Steps | Expected Result | Pass? |
|---|----------|-------|-----------------|-------|
| 1 | Patch update, 24h+ release, no vulnerabilities | Trigger dependabot PR with patch update for a dependency released >24h ago | PR is auto-approved even if usage data is unavailable | [ ] |
| 2 | Minor update, 24h+ release, usage shows 0 | Trigger dependabot PR with minor update, >24h release, usage=0 | PR is auto-approved | [ ] |
| 3 | Patch update, <24h release | Trigger dependabot PR for a version released <24h ago | PR is NOT auto-approved (release too recent) | [ ] |
| 4 | Minor update with known vulnerability | Trigger dependabot PR where dependency review flags a vulnerability | PR is NOT auto-approved | [ ] |
| 5 | Major version bump, all criteria met | Trigger dependabot PR with major update, >24h release, no vulnerabilities | PR is NOT auto-approved (major updates require manual review) | [ ] |

## US2: Dependency Usage as Informational Context

| # | Scenario | Steps | Expected Result | Pass? |
|---|----------|-------|-----------------|-------|
| 1 | Usage data available | Trigger dependabot PR where usage search succeeds | PR comment displays usage count as informational (not approval criterion) | [ ] |
| 2 | Usage data unavailable | Trigger dependabot PR where usage search fails or returns 0 | PR comment shows "unavailable", no impact on auto-approval outcome | [ ] |

## US3: Release Age Verification

| # | Scenario | Steps | Expected Result | Pass? |
|---|----------|-------|-----------------|-------|
| 1 | Release >24h old | Trigger dependabot PR for dependency released >24h ago | release_age_hours >= 24, does not block approval | [ ] |
| 2 | Release <24h old | Trigger dependabot PR for dependency released <24h ago | release_age_hours < 24, PR not auto-approved | [ ] |
| 3 | Release date unknown | Trigger dependabot PR for an unknown ecosystem | release_age_hours = -1, PR not auto-approved, comment shows "unknown" | [ ] |
| 4 | Release exactly 24h | Trigger dependabot PR for dependency released exactly 24h ago | release_age_hours >= 24, threshold passes | [ ] |

## US4: Robust Dependency Information Extraction

| # | Scenario | Steps | Expected Result | Pass? |
|---|----------|-------|-----------------|-------|
| 1 | Composite action file | Trigger dependabot PR updating an action in `.github/actions/` | Name, version, risk extracted from commit metadata; all downstream jobs succeed | [ ] |
| 2 | Diff parsing fails | Trigger dependabot PR where diff is unusual/unparseable | System produces valid outputs from commit metadata or title fallback | [ ] |
| 3 | Both sources succeed | Trigger dependabot PR with standard commit metadata and parseable diff | Commit metadata used for name/version/update-type; diff enriches with SHA refs | [ ] |
| 4 | All extraction fails | Trigger PR with malformed/missing metadata and unparseable diff | Risk defaults to high, PR not auto-approved, comment indicates extraction failure | [ ] |

## PR Comment Validation

| # | Check | Expected | Pass? |
|---|-------|----------|-------|
| 1 | Release age displayed | Shows hours if known, "unknown" if -1 | [ ] |
| 2 | Auto-approval rationale | Shows pass/fail status for each criterion | [ ] |
| 3 | Dependency usage | Shows count or "unavailable" | [ ] |
| 4 | Maintainer checklist | Present and complete | [ ] |
