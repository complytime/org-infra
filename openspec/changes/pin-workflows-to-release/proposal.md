## Why

Consumer workflows (`ci_*`) and one reusable workflow (`reusable_scheduled.yml`) reference
org-infra reusable workflows at `@main`, creating a mutable, unpinned dependency. With the
v0.1.0 release now cut, these references should be pinned to the release commit SHA
(`baf5b2e21e61581b4a3a129795286e8592e6afbb`) to align with the org's existing security
convention of pinning all `uses:` references to full 40-character SHAs.

## What Changes

- Replace all 9 `@main` reusable-workflow references with
  `@baf5b2e21e61581b4a3a129795286e8592e6afbb # v0.1.0` across 7 workflow files.
- Affected files:
  - `ci_checks.yml` (1 reference)
  - `ci_compliance.yml` (1 reference)
  - `ci_crapload.yml` (1 reference)
  - `ci_dependencies.yml` (2 references)
  - `ci_scheduled.yml` (1 reference)
  - `ci_security.yml` (2 references)
  - `reusable_scheduled.yml` (1 reference)

## Non-goals

- Changing the sync mechanism or adding automated sync triggers.
- Implementing a major-version floating tag strategy (e.g., `@v1`).
- Modifying any third-party action pins (already SHA-pinned).

## Capabilities

### New Capabilities

- `workflow-sha-pinning`: Pin org-infra reusable workflow references to release commit
  SHAs with version comments, matching the existing third-party action pinning convention.

### Modified Capabilities

(none)

## Impact

- **Workflows**: All 7 consumer workflow files and 1 reusable workflow file in
  `.github/workflows/` are modified.
- **Downstream repos**: After the next org sync, downstream repos will receive updated
  `ci_*` files pinned to the v0.1.0 SHA instead of `@main`. This means downstream repos
  will use a fixed snapshot of reusable workflows until the next release and sync cycle.
- **Development workflow**: Future changes to reusable workflows will no longer take
  effect immediately in downstream repos. A new release + sync cycle will be required to
  propagate reusable workflow changes.
