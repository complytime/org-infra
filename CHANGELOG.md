# Changelog

## Unreleased

### Added

- **Sprint velocity report**: Manual workflow that counts Done issues per
  completed Iteration on the Compliance Automation planning board, then
  averages those counts (including by Size, Organization, and Milestone).
  The open sprint is listed separately and is not in the mean. See
  `docs/SPRINT_VELOCITY.md`.

- **Stale review alerts**: Added `reusable_stale_reviews.yml` and
  `ci_stale_reviews.yml` to detect and flag PRs with review requests
  pending beyond a configurable business-day threshold. Applies a
  `stale-review` label and posts a reminder comment @-mentioning
  assigned reviewers. Synced to org repos via `sync-config.yml` with
  staged rollout (org-infra first). (#478)

- **SECURITY.md sync**: Added `SECURITY.md` to `sync-config.yml` for
  org-wide security policy distribution. Each synced repository receives a
  stub with the security contact email (`complytime-security@redhat.com`),
  GitHub Private Vulnerability Reporting instructions, and a link to the
  canonical policy in `community/SECURITY.md`. The `community` repository
  is excluded from sync (it holds the canonical policy). This ensures OSPS
  Baseline Level 1 compliance (OSPS-VM-02.01) across all org repositories.

### Changed

- **Project board sync**: Run the Compliance Automation planning board
  sync every 5 minutes instead of once daily. GitHub Actions does not
  honor a 1-minute cron; 5 minutes is the documented minimum. Concurrent
  runs are serialized so ticks do not pile up.

- **crapload workflow**: Replaced custom `scripts/compare-crapload.sh`
  (315 lines) with gaze's native `gaze crap --baseline` comparison.
  The workflow now writes a temporary `.gaze.yaml` from workflow inputs
  when the consumer repo has no config file, preserving backward
  compatibility. PR comment generation is inline via jq. (#328)

### Removed

- `scripts/compare-crapload.sh` — comparison logic is now native to gaze
- `TestCompareCrapload` test class (5 tests, 203 lines) — covered by
  34 upstream tests in gaze
