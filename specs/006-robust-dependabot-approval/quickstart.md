# Quickstart: Robust Dependabot Auto-Approval

**Branch**: `006-robust-dependabot-approval` | **Date**: 2026-04-08

## Files to Modify

| File | Action | Description |
|------|--------|-------------|
| `.github/workflows/reusable_dependabot_reviewer.yml` | Modify | Simplify extraction, add release age, add new outputs |
| `.github/workflows/ci_dependencies.yml` | Modify | Update auto-approval criteria, update PR comment |

No new files are created. No files are deleted.

## Implementation Order

### Step 1: Simplify Dependency Extraction (reusable_dependabot_reviewer.yml)

Replace the "Get Dependency Information" step (lines 41-157, 112 lines of bash):

1. Remove `set -e` -- replace with per-command error handling
2. Add commit metadata parsing as primary source (parse `updated-dependencies` block from commit body using `grep`/`sed`)
3. Simplify diff parsing to supplementary enrichment only (extract SHA-pinned refs for usage queries)
4. Keep title/body fallback for cases where metadata is absent
5. Export new outputs: `dep_name`, `dep_version`

### Step 2: Simplify Risk Classification (reusable_dependabot_reviewer.yml)

Modify the "Classify Risk" step (lines 159-188):

1. If `UPDATE_TYPE` was extracted from commit metadata, use it directly (`semver-major` → `high`, `semver-minor` → `medium`, `semver-patch` → `low`)
2. Fall back to semver comparison only when `UPDATE_TYPE` is unavailable
3. Default to `high` when neither method yields a result

### Step 3: Add Release Age Check (reusable_dependabot_reviewer.yml)

Add a new step after ecosystem detection:

1. Based on detected ecosystem, look up release date via the appropriate API
2. GitHub Actions: `gh api repos/{dep_name}/releases/tags/v{version}` → `.published_at`
3. Go modules: `curl https://proxy.golang.org/{module}/@v/v{version}.info` → `.Time`
4. Python/pip: `curl https://pypi.org/pypi/{package}/{version}/json` → `.urls[0].upload_time_iso_8601`
5. Unknown/failure: set `release_age_hours=-1`
6. Compute hours since release, output `release_age_hours`

### Step 4: Update Auto-Approval (ci_dependencies.yml)

Modify the `approve_dependabot_prs` job:

1. Change `if:` condition to use `needs.*` outputs directly (not step-level `env:`)
2. New criteria: `risk_level != 'high' && review_conclusion == 'success' && release_age_hours >= 24`
3. Remove `UPDATES_COUNT > 10` from the condition

### Step 5: Update PR Comment (ci_dependencies.yml)

Modify the `comment_on_dependabot_prs` job:

1. Add release age information to the comment body
2. Add auto-approval rationale (which criteria passed/failed)
3. Keep dependency usage as informational context

## Validation

1. `make lint` -- YAML linting must pass
2. Manual test: trigger workflow on a dependabot PR in a test repo
3. Verify PR comment includes release age and approval rationale
4. Verify auto-approval fires only when all criteria are met
5. Verify extraction works for composite action files (the PR #806 scenario)

## Sync Impact

Both modified files are listed in `sync-config.yml` and will propagate to all org repos:
- `ci_dependencies.yml` → all non-excluded repos
- `reusable_dependabot_reviewer.yml` → consumed via `@main` reference (auto-propagates)
