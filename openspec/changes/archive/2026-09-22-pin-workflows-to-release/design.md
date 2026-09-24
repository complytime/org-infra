## Context

Consumer workflows (`ci_*`) in org-infra call reusable workflows via
`uses: complytime/org-infra/.github/workflows/reusable_*.yml@main`. This mutable
reference means any push to `main` that modifies a reusable workflow immediately changes
behavior in all downstream repos -- with no review gate and no rollback path.

The org already enforces SHA-pinning for all third-party actions (e.g.,
`actions/checkout@<sha> # v6.0.2`). The v0.1.0 release
(`baf5b2e21e61581b4a3a129795286e8592e6afbb`) provides the first stable tag to pin against.

Nine `@main` references exist across 7 consumer workflows and 1 reusable workflow
(`reusable_scheduled.yml` calls `reusable_security.yml`).

## Goals / Non-Goals

**Goals:**

- Pin all 9 reusable-workflow `@main` references to the v0.1.0 release SHA.
- Use the same `@<sha> # v0.1.0` format already established for third-party action pins.
- Ensure downstream repos receive the pinned references on the next org sync.

**Non-Goals:**

- Adding automated sync triggers (remains `workflow_dispatch` only).
- Creating a major-version floating tag strategy (e.g., `@v1`).
- Modifying the sync script or `sync-config.yml`.
- Changing any third-party action pins.

## Decisions

### 1. Pin format: `@<full-sha> # v0.1.0`

Use the full 40-character commit SHA with an inline version comment, matching the
existing convention for third-party actions.

**Alternatives considered:**
- **Tag reference (`@v0.1.0`)**: Mutable -- tags can be moved or deleted. Rejected
  because the org constitution explicitly prohibits mutable tags in `uses:` references.
- **Short SHA (`@baf5b2e`)**: GitHub resolves short SHAs but they can become ambiguous
  as the commit history grows. Rejected for consistency with existing full-SHA pins.

### 2. Pin the reusable-to-reusable reference too

`reusable_scheduled.yml` calls `reusable_security.yml@main`. This is pinned to the same
SHA to maintain consistency -- all cross-workflow references within org-infra follow the
same pinning convention.

**Alternatives considered:**
- **Leave `@main` for internal calls**: Would create an inconsistency where consumer
  workflows are pinned but internal calls are not. Rejected for uniformity and because
  `reusable_scheduled.yml` is also synced to downstream repos.

### 3. Single atomic change across all files

All 9 references are updated in one change rather than per-file or per-workflow.

**Alternatives considered:**
- **Per-workflow PRs**: Would create 7 separate PRs for a uniform find-and-replace.
  Rejected as unnecessary overhead for a mechanical change.

## Risks / Trade-offs

- **[Risk] Future reusable workflow changes require a release cycle to propagate.**
  Previously, pushing to `main` was enough. Now a new release must be cut and the SHA
  updated in consumer workflows before syncing.
  -> Mitigation: This is the intended behavior. It adds a deliberate review gate.
  Document the release-then-sync workflow in the repo's contributing guide.

- **[Risk] Circular dependency for org-infra's own CI.** The consumer workflows in
  org-infra itself reference reusable workflows from the same repo. After pinning,
  changes to a reusable workflow won't be tested by org-infra's own CI until a new
  release is cut.
  -> Mitigation: org-infra can test reusable workflow changes on feature branches using
  `@<branch>` temporarily, then pin to the new release SHA before merging. Alternatively,
  accept that org-infra's `main` CI uses the last-released version of its own reusable
  workflows.

- **[Trade-off] Increased maintenance cost per release.** Each release requires updating
  9 SHA references. This is a small, mechanical cost offset by the supply-chain security
  benefit.
