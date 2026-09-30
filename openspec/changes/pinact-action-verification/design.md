## Context

The reusable CI workflow (`reusable_ci.yml`) currently runs MegaLinter as its
sole job, which includes zizmor (offline, no GitHub token), actionlint, KICS,
and other linters. None of these tools validate that SHA-pinned action
references resolve to real commits, verify version comment accuracy, or detect
outdated action versions.

pinact is an established CLI tool (Go binary, 1.2k GitHub stars, SLSA
provenance) that provides SHA verification, version comment validation, and
version freshness detection for GitHub Actions workflow files.

The integration must accommodate a key constraint: pinact's `--check` flag
(alias for `--fix=false`) and `--update` flag are mutually exclusive in effect.
`--check` disables file writes, while `--update` requires write access to
resolve and record latest versions. There is no single dry-run mode that
reports both integrity issues and version staleness.

## Goals / Non-Goals

### Goals

- Validate SHA-pinned action references resolve to real upstream commits
- Verify version comments match their pinned SHAs
- Detect unpinned action references (mutable tags like `@v4`)
- Warn (not block) when action versions are behind latest
- Enforce a 3-day minimum release age for supply chain protection
- Provide consistent configuration across all org repositories

### Non-Goals

- Auto-committing fixes to PR branches
- Replacing zizmor (complementary tools, different audit domains)
- Blocking CI on outdated versions (warning only)
- Solving the `reusable_ci.yml` downstream propagation mechanism

## Decisions

### 1. Use `suzuki-shunsuke/pinact-action` composite action (two invocations)

The pinact job uses the official `suzuki-shunsuke/pinact-action` composite
action, SHA-pinned to a specific release. Two invocations handle the two
verification modes:

1. **Verify invocation** (hard gate): `fix: "false"`, `verify: "true"`,
   `min_age: "3"`, `verify_min_age: "true"`
2. **Freshness invocation** (warning): `update: "true"`, `skip_push: "true"`,
   followed by a `git diff` step to detect and annotate outdated actions.

**Alternative considered: Install pinact binary via `go install` and run CLI
commands directly.** Rejected because it duplicates installation, token
management, and flag-mapping logic that the maintained action already handles.
Direct CLI invocation offers no additional control needed for this use case
and adds unnecessary maintenance surface. This violates principle V (Do Not
Reinvent the Wheel).

### 2. Two-step verification in a single job

The pinact job runs two sequential steps within a single job:

1. **Verify step** (hard gate): Runs `pinact-action` with `fix: "false"`,
   `verify: "true"`, `min_age: "3"`, `verify_min_age: "true"`.
   Exits non-zero if any action is unpinned, has a mismatched comment, or
   has an unresolvable SHA. Fails the job on exit codes 1 (needs pinning),
   2 (unfixable issue), or 3 (API error).

2. **Freshness step** (warning only): Runs `pinact-action` with
   `update: "true"`, `skip_push: "true"`. This updates files locally without
   pushing. A follow-up step runs `git diff` to detect outdated actions and
   emits `::warning` annotations. The workspace is restored with
   `git checkout -- .`. This step never fails the job regardless of outcome.

**Alternative considered: Single step combining both checks.** Rejected because
`--check` and `--update` are mutually exclusive (see Context). A single
invocation cannot both validate integrity (read-only) and detect staleness
(requires write).

**Alternative considered: Separate jobs for verify and freshness.** Rejected
because both steps need the same checkout and pinact installation. Running them
in one job avoids duplicating setup and checkout time.

### 3. Minimum release age of 3 days

The `.pinact.yaml` configuration sets `min_age.value: 3` (days). This prevents
pinning to versions released within the last 3 days, providing a cooldown
window against compromised newly-published releases.

**Alternative considered: 7 days.** Rejected as too conservative for the org's
iteration speed. A 7-day window would frequently block legitimate updates and
create friction.

**Alternative considered: 1 day (24 hours).** Rejected as insufficient to
cover weekend publication windows. A release published Friday evening would
clear a 1-day gate by Saturday evening, before most maintainers are available
to notice issues.

### 4. `.pinact.yaml` synced to all downstream repositories

The `.pinact.yaml` configuration file is added to `sync-config.yml` so all
org repositories receive consistent defaults. Individual repos may override
with a local `.pinact.yaml` for legitimate exceptions.

**Alternative considered: No sync, each repo configures independently.**
Rejected because it violates the Single Source of Truth principle and would
lead to inconsistent min-age and exclusion policies across the org.

### 5. Freshness check uses `continue-on-error: true`

The freshness step uses `continue-on-error: true` to ensure it never blocks
CI, even if pinact or git commands fail unexpectedly. The verify step (hard
gate) does NOT use `continue-on-error`.

**Alternative considered: Custom exit code handling with `if: always()`.**
Rejected as more complex and harder to reason about. `continue-on-error: true`
is the idiomatic GitHub Actions pattern for advisory checks.

### 6. Pass `GITHUB_TOKEN` explicitly to pinact

The pinact job passes `GITHUB_TOKEN` via the action's `github_token` input so
pinact can make authenticated GitHub API calls for SHA resolution and version
lookups. Without it, pinact would be rate-limited to 60 requests/hour
(unauthenticated), which is insufficient for repos with many workflow files.

**Alternative considered: `--no-api` (offline) mode.** Rejected because offline
mode cannot verify SHAs against upstream repositories, which is the core
requirement from issue #337.

## Risks / Trade-offs

**[Risk] Existing workflows have mismatched version comments.**
The hard gate (`--verify-comment`) will fail if any current action has a
version comment that doesn't match its SHA. This requires a one-time fix pass
on existing workflows before the check can be enabled.
-> Mitigation: Run `pinact run --verify-comment` locally before merging to
identify and fix mismatches. The first PR can include these fixes.

**[Risk] GitHub API rate limiting.**
pinact makes API calls for each action reference to resolve SHAs and verify
comments. Repos with many workflow files could hit rate limits.
-> Mitigation: The `GITHUB_TOKEN` provides 1,000 requests/hour for
authenticated calls, sufficient for typical org repos. pinact caches
resolutions within a single run.

**[Risk] False positives from the freshness check on intentionally-pinned
older versions.**
-> Mitigated by design: the freshness check is a warning, not a gate.
Maintainers can acknowledge and ignore warnings for intentional version
ceilings.

**[Trade-off] Two-step pattern adds complexity vs. a single check.**
-> Accepted because the single-check alternative (only `--check
--verify-comment`) would miss the outdated version problem entirely, which is
the more common issue with AI-authored workflows.
