## Why

The `reusable_dependabot_reviewer.yml` workflow fails to detect version
information for **grouped Dependabot PRs**, causing all grouped updates to be
classified as "high risk" regardless of the actual semver change. This happens
because grouped Dependabot commits (1) omit `update-type` from the
`updated-dependencies` metadata block, and (2) omit version numbers from the
commit subject line. The version data exists in the commit body text and PR title
but the workflow never consults either source, leaving `from_version` and
`update_type` empty and triggering the default high-risk fallback.

This directly violates FR-015 (fallback chain) and Assumption 12 (graceful
handling of missing metadata) from spec 006-robust-dependabot-approval, and
prevents safe grouped patch/minor updates from being auto-approved.

## What Changes

- Add a **commit body fallback** to the version extraction pipeline: when the
  commit subject yields fewer than two semver matches, scan `COMMIT_BODY` for
  the pattern `from <version> to <version>` to populate `from_version`.
- Add a **PR title fallback** as a final extraction source: use
  `github.event.pull_request.title` when neither the commit subject nor body
  yield version numbers.
- Compute `update_type` from extracted `from_version` and `to_version` when the
  commit metadata lacks `update-type`, so the primary classification path can
  still function.

## Non-goals

- Changing the auto-approval criteria or risk thresholds (those are correct as
  designed in 006).
- Supporting multi-dependency grouped PRs where each dependency has a different
  update type (the existing "first dependency" heuristic is retained).
- Refactoring the entire extraction pipeline (this is a targeted fix to the
  existing fallback chain).

## Capabilities

### New Capabilities

_None._

### Modified Capabilities

- `dependabot-review`: The version extraction fallback chain in the reusable
  dependabot reviewer workflow is extended to handle grouped Dependabot commit
  formats that omit `update-type` and version numbers from the subject line.

## Impact

- **Workflow**: `reusable_dependabot_reviewer.yml` -- the "Get Dependency
  Information" and "Classify Risk Based on Semantic Version" steps are modified.
- **Downstream**: All org repositories consuming this reusable workflow via
  `sync-config.yml` will receive the fix automatically on next sync.
- **Risk**: Low. Changes are additive fallbacks that only activate when existing
  extraction sources yield incomplete data. The existing primary extraction paths
  (commit metadata, subject regex) are unchanged.
