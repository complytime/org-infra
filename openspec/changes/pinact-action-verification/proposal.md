# Proposal: Integrate pinact for Action Version Verification

Resolves: [complytime/org-infra#337](https://github.com/complytime/org-infra/issues/337)

## Why

GitHub Actions workflows in the ComplyTime organization are vulnerable to two
classes of defects that pass all current CI checks:

1. **Invalid SHAs**: AI-generated or manually crafted action references can
   contain fabricated commit hashes that don't exist in the upstream repository.
   These pass yamllint, actionlint, and zizmor (in offline mode) but fail at
   runtime. The motivating example is `complytime/.github#114`, where
   `actions/setup-node` was pinned to a non-existent SHA.

2. **Outdated versions**: AI agents frequently write workflows using action
   versions from their training data. A workflow may reference
   `actions/checkout@v3` when `v7` is the current version. These are valid and
   functional but accumulate technical debt and miss security fixes, bug fixes,
   and performance improvements.

Neither zizmor (already integrated via MegaLinter) nor actionlint, KICS, or
Dependabot catch these problems pre-merge. Dependabot updates *existing*
references after merge but cannot prevent *new* stale references from being
introduced.

[pinact](https://github.com/suzuki-shunsuke/pinact) (1.2k GitHub stars,
actively maintained, Go binary with SLSA provenance) provides all needed
verification functionality with no custom scripting required.

## What Changes

The reusable CI workflow gains a new `pinact` job that validates action
references in two modes:

- **Hard gate**: Verifies all actions are SHA-pinned with correct version
  comments. Fails CI if any SHA is invalid, any version comment is mismatched,
  or any action is unpinned.
- **Warning**: Detects outdated action versions by comparing against the latest
  available release. Annotates the PR with warnings but does not block merging,
  since using an older version may be intentional.

A new `.pinact.yaml` configuration file is added to define org-wide defaults
(minimum release age, exclusion rules) and is synced to all downstream
repositories.

### Key design constraint

pinact's `--check` flag (alias for `--fix=false`) and `--update` flag are
mutually exclusive in effect. `--check` puts pinact in read-only mode, while
`--update` requires write access to resolve and write latest versions. There is
no dry-run mode that reports outdated versions without modifying files.

This requires a two-step verification approach:

1. **Verify step** (hard gate): `pinact run --check --verify-comment` --
   read-only, exits non-zero on invalid SHAs, mismatched comments, or unpinned
   actions.
2. **Freshness step** (warning): `pinact run --update` followed by
   `git diff` to detect whether any actions were updated. If changes are
   detected, emit `::warning` annotations listing the outdated actions, then
   restore the workspace with `git checkout -- .`

## Capabilities

### New Capabilities

- **Action SHA verification**: Every `uses:` clause with a SHA pin has its
  version comment validated against the actual tag the SHA resolves to,
  catching hallucinated SHAs and forged comments.
- **Unpinned action detection**: Actions using mutable tags (`@v4`, `@main`)
  are flagged as needing SHA pinning.
- **Outdated version warnings**: Actions not at their latest version are
  reported as PR annotations (warnings, not failures).
- **Supply chain cooldown**: A minimum release age of 3 days prevents pinning
  to versions released too recently, reducing risk from compromised
  newly-published releases. This covers weekend publication windows while
  remaining practical for rapid iteration.
- **Org-wide pinact configuration**: A `.pinact.yaml` file synced to all
  repositories provides consistent defaults.

### Modified Capabilities

- **`reusable_ci.yml`**: Extended with a new `pinact` job alongside the
  existing `megalinter` job.
- **`sync-config.yml`**: Extended with a `.pinact.yaml` sync entry.
- **`.mega-linter.yml`**: No changes. zizmor remains enabled and continues to
  provide complementary security audits.

## Impact

- **org-infra**: Gains immediate CI protection against invalid SHAs and
  outdated versions.
- **Downstream repositories**: Gain the `.pinact.yaml` config via sync. The
  pinact job itself reaches downstream repos through the existing
  `reusable_ci.yml` propagation mechanism (same as the MegaLinter job today).
- **Existing workflows**: The hard gate (`--check --verify-comment`) will fail
  if any existing action has a mismatched version comment. This may require a
  one-time fix pass on current workflows before enabling.
- **Dependabot**: Continues to operate as before. pinact complements Dependabot
  by catching stale introductions pre-merge, while Dependabot keeps existing
  references fresh post-merge.
- **Token requirements**: The default `github.token` is sufficient for
  check-only and update modes (read API access only). No GitHub App or
  additional secrets are required.

## Non-goals

- **Auto-committing fixes**: This change does not auto-update or auto-pin
  actions on the PR branch. It is a check-only integration. Auto-fix mode
  (which requires a GitHub App token and `workflows:write` permission) may be
  explored separately.
- **Replacing zizmor**: pinact and zizmor serve complementary roles. zizmor
  audits for security misconfigurations (permissions, template injection,
  dangerous triggers). pinact audits for version integrity (SHA validity,
  comment accuracy, version freshness). Both remain enabled.
- **Blocking on outdated versions**: The outdated version check is
  intentionally a warning, not a hard gate. There are legitimate reasons to
  pin to an older version (compatibility, feature regression, deliberate
  version ceiling).
- **Solving the `reusable_ci.yml` sync question**: Whether and how
  `reusable_ci.yml` propagates to downstream repos is a pre-existing
  infrastructure concern. This proposal adds the pinact job to
  `reusable_ci.yml` following the same pattern as the existing MegaLinter job.
- **Replacing Dependabot for version updates**: Dependabot remains the
  mechanism for ongoing version maintenance. pinact prevents stale
  introductions; Dependabot prevents stale drift.

## Constitution Alignment

### I. Single Source of Truth

**Assessment**: PASS

The `.pinact.yaml` configuration file serves as the single source of truth for
action version policy (minimum release age, exclusion rules) and is synced
org-wide via `sync-config.yml`. No duplicate configuration in individual repos.

### II. Simplicity & Isolation

**Assessment**: PASS

pinact runs as an isolated job in `reusable_ci.yml`, independent of the
MegaLinter job. It uses the default `github.token` (no additional secrets or
GitHub Apps required for check-only mode). The tool is a single Go binary with
no runtime dependencies.

### III. Incremental Improvement

**Assessment**: PASS

Focused on a single concern: action version integrity. Does not bundle
unrelated changes. The warning-only mode for outdated versions allows gradual
adoption without disrupting existing workflows.

### IV. Readability First

**Assessment**: PASS

pinact produces clear, actionable output: file path, line number, current
version, expected version. SARIF output is available for GitHub code scanning
integration if needed later.

### V. Do Not Reinvent the Wheel

**Assessment**: PASS

pinact is an established, actively maintained tool (1.2k GitHub stars, SLSA
provenance, Cosign attestations) that provides all needed functionality. No
custom scripts required. The tool is already recommended by zizmor's own
documentation for version comment management.

### VI. Composability

**Assessment**: PASS

pinact integrates cleanly as an additional job in the existing
`reusable_ci.yml` workflow. Its SARIF output is consumable by GitHub code
scanning, reviewdog, and other tools. It does not interfere with existing
linters.

### VII. Convention Over Configuration

**Assessment**: PASS

Sensible defaults (SHA pinning required, version comments required, 3-day
minimum release age) are defined in `.pinact.yaml` and apply org-wide without
per-repo configuration. Repos may override with a local `.pinact.yaml` only
when deviating from the org standard.
