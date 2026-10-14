# Proposal

## Why

When Dependabot proposes the same dependency version bump across multiple org
repositories, maintainers must review and merge each PR individually -- even
though the update is identical. For GitHub Actions dependencies (the most common
cross-repo ecosystem), this means N redundant reviews for N repos. If a
maintainer already reviewed, approved, and merged a dependency update in one
repo, that review effort should propagate as trust to the remaining repos.

## What Changes

- Add a cross-repo precedent lookup step to the Dependabot reviewer pipeline.
  When a dependabot PR arrives, the pipeline queries the GitHub Search API for
  merged PRs in the same org that update the same dependency to the same
  version, then verifies that at least one of those merges had a human approval
  review (excluding bot approvals from the existing auto-approve logic).
- Extend the auto-approval decision matrix with a third path ("org precedent"):
  when precedent is found AND the local dependency review passes AND risk is not
  high AND release age is at least 24 hours, the PR is auto-approved and
  auto-merge is enabled.
- Extend the PR comment to include the org precedent signal with a link to the
  seed PR and the reviewer who approved it, giving maintainers full transparency
  into the automated decision.

## Non-goals

- Overriding the 24-hour release age gate. Even with precedent, the release
  must be at least 24 hours old.
- Overriding the dependency-review-action. The vulnerability scan still runs in
  every repo regardless of precedent.
- Overriding the risk gate. Major version bumps still require manual review
  even with precedent.
- Cross-repo dispatch or event-driven propagation. This change uses a pull-based
  API lookup, not push-based notifications.
- Handling private repositories. All ComplyTime repos are public;
  `GITHUB_TOKEN` is sufficient for cross-repo search.
- Scheduled re-evaluation of open PRs. Follower PRs pick up precedent on their
  next CI run (manual re-run or dependabot rebase). A sweep mechanism can be
  added later if needed.

## Capabilities

### New Capabilities

- `org-precedent-detection`: Cross-repo search for merged dependabot PRs with
  human approval, verifying that the same dependency at the same version was
  already reviewed and merged in another org repository.

### Modified Capabilities

- `org-owned-auto-merge`: The approval decision matrix gains a third path
  (org precedent) that enables auto-merge for third-party dependencies when
  cross-repo human review precedent exists. The PR comment format is extended
  to surface the precedent signal.

## Impact

- **Workflows**: `reusable_dependabot_reviewer.yml` (new step + outputs),
  `ci_dependencies.yml` (extended approval logic + comment + auto-merge
  condition).
- **Sync**: Both files are synced to all org repos via `sync-config.yml`.
  The change rolls out automatically to all downstream repos on next sync.
- **API usage**: Adds 1 search API call + 1-5 REST API calls per dependabot PR
  evaluation. Well within GitHub rate limits (30 search/min, 5000 REST/hr).
- **Token**: No new secrets. Uses existing `GITHUB_TOKEN` (sufficient for
  public repos).
- **Security**: The dependency-review-action, risk gate, and release age gate
  all remain as independent safety checks. Precedent is an additive signal,
  never a bypass.
