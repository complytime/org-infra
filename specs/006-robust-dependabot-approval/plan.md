# Implementation Plan: Robust Dependabot Auto-Approval

**Branch**: `006-robust-dependabot-approval` | **Date**: 2026-04-08 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `/specs/006-robust-dependabot-approval/spec.md`

## Summary

Replace the fragile dependency-usage-based auto-approval gate with a robust criteria set: non-major version bump + 24h release age + no vulnerabilities + CI passing. Simplify the dependency information extraction by using dependabot commit metadata as the primary source with diff parsing as supplementary enrichment. Keep dependency usage as informational data in PR comments. Structural simplification: elimination of `set -e`, nested while loops, and temp file I/O. Net reduction of ~51 lines across both files, with significantly reduced logical complexity.

## Technical Context

**Language/Version**: Bash (shell scripts in GitHub Actions `run:` blocks), YAML (GitHub Actions workflow syntax)
**Primary Dependencies**: GitHub Actions platform, `gh` CLI (pre-installed on runners), `jq` (pre-installed on runners), `curl` (pre-installed on runners), `actions/dependency-review-action@v4.9.0`, `peter-evans/create-or-update-comment@v5.0.0`, `actions/github-script@v8.0.0`, `actions/checkout@v6.0.2`, `tj-actions/changed-files@v47.0.5`
**Storage**: N/A (no persistent storage; data flows via GitHub Actions outputs and environment variables)
**Testing**: Manual validation via workflow runs on dependabot PRs; `make lint` for YAML linting
**Target Platform**: GitHub Actions runners (ubuntu-latest)
**Project Type**: CI/CD infrastructure (reusable workflows synced to all org repos)
**Performance Goals**: N/A (CI workflow, completes within minutes)
**Constraints**: Must work within GitHub Actions limitations (step outputs, job dependencies, permissions). Must simplify or at least not increase complexity per user requirement.
**Scale/Scope**: Synced to all org repositories via `sync-config.yml`. Changes to `reusable_dependabot_reviewer.yml` propagate automatically (consumed via `@main` ref). Changes to `ci_dependencies.yml` sync as file copies.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Notes |
|-----------|--------|-------|
| I. Single Source of Truth | PASS | Auto-approval criteria centralized in `ci_dependencies.yml` `if:` condition. Release age threshold extracted to workflow-level `env: MIN_RELEASE_AGE_HOURS: 24` and referenced in both the approval condition and PR comment template. |
| II. Simplicity & Isolation | PASS | Net reduction of ~51 lines. Extraction step replaces 112 lines of nested loops with ~30 lines of sequential metadata/diff/title parsing. Each step has a single responsibility. |
| III. Incremental Improvement | PASS | Changes are focused on the approval criteria and extraction robustness. No unrelated changes included. |
| IV. Readability First | PASS | Commit metadata parsing is explicit (`grep 'dependency-name:'`). Risk classification uses a clear `case` statement. Error handling uses `|| true` instead of `set -e`. |
| V. Do Not Reinvent the Wheel | PASS | Uses built-in dependabot metadata, existing `gh` CLI, standard package registry APIs. No new external dependencies added. |
| VI. Composability | PASS | Workflow steps remain modular. New `release_age_hours` output integrates cleanly with existing output pattern. |
| VII. Convention Over Configuration | PASS | 24h threshold is a sensible default. Auto-approval defaults to not approving when data is unavailable (safe default). |
| YAML/Actions naming | PASS | Files retain `reusable_` and `ci_` prefixes. |
| YAML/Actions security | PASS | No new permissions required. Existing `contents: read` sufficient for release date API calls via `gh`. |
| Workflow formatting | PASS | Must pass `yamllint` (`make lint`). |
| Commit standards | PASS | Conventional Commits with `-s` and `Assisted-by` trailer. |

**Post-Phase 1 re-check**: No violations introduced. All principles upheld.

## Project Structure

### Documentation (this feature)

```text
specs/006-robust-dependabot-approval/
├── plan.md              # This file
├── spec.md              # Feature specification
├── research.md          # Phase 0 research output
├── data-model.md        # Phase 1 data model (workflow I/O)
├── quickstart.md        # Phase 1 implementation quickstart
├── checklists/
│   └── requirements.md  # Specification quality checklist
└── tasks.md             # Phase 2 output (created by /speckit.tasks)
```

### Source Code (repository root)

```text
.github/workflows/
├── reusable_dependabot_reviewer.yml   # MODIFY: simplify extraction, add release age, add outputs
├── reusable_deps_reviewer.yml         # UNCHANGED
└── ci_dependencies.yml                # MODIFY: update approval criteria, update PR comment
```

**Structure Decision**: No new files. Modifications to two existing workflow files. This aligns with the simplification constraint -- the feature is implemented entirely within the existing workflow architecture.

## Complexity Tracking

No constitution violations to justify. All changes align with principles, particularly Principle II (Simplicity & Isolation).

## Implementation Tasks

### Task 1: Simplify Dependency Information Extraction

**File**: `.github/workflows/reusable_dependabot_reviewer.yml`
**Step**: "Get Dependency Information" (current lines 41-157)
**Spec refs**: FR-012, FR-013, FR-014, FR-015, SC-007, SC-008

**Changes**:

1. **Remove `set -e`** (line 46). Replace with per-command error handling using `|| true` and explicit checks.

2. **Add commit metadata parsing** as primary source (~10 lines):
   - Parse `dependency-name`, `dependency-version`, `update-type` from commit body using `grep`/`sed`
   - These fields appear in the `updated-dependencies:` YAML block in dependabot commit messages
   - When not present, variables remain empty and fallback methods fill them

3. **Simplify diff parsing** to supplementary enrichment only (~10 lines):
   - Remove nested while loops and temp file I/O (`/tmp/uses_old.txt`, `/tmp/uses_new.txt`, `/tmp/gomod_removed.txt`, `/tmp/gomod_added.txt`)
   - For GitHub Actions: single `grep` on diff to extract SHA-pinned `uses:` ref for usage query
   - For Go modules: single `grep` on diff to enrich version info if needed
   - All diff operations wrapped with `|| true` to prevent crashes

4. **Keep title/body fallback** (~10 lines):
   - Existing title parsing logic for `dep_name` when metadata and diff both miss
   - Version extraction from "from X to Y" patterns in commit text

5. **Add new outputs**: `dep_name`, `dep_version` to the job outputs section

**Estimated change**: 112 lines → ~30 lines (-82 lines)

### Task 2: Simplify Risk Classification

**File**: `.github/workflows/reusable_dependabot_reviewer.yml`
**Step**: "Classify Risk Based on Semantic Version" (current lines 159-188)
**Spec refs**: FR-005

**Changes**:

1. **Use `update-type` from commit metadata** when available:
   ```
   case "$UPDATE_TYPE" in
     *semver-major*) risk="high" ;;
     *semver-minor*) risk="medium" ;;
     *semver-patch*) risk="low" ;;
     *) # fall through to semver comparison
   esac
   ```

2. **Fall back to semver comparison** only when `UPDATE_TYPE` is empty (current logic, unchanged)

3. **Default to `high`** when neither method yields a result (current behavior, unchanged)

**Estimated change**: 30 lines → ~15 lines (-15 lines)

### Task 3: Add Release Age Check

**File**: `.github/workflows/reusable_dependabot_reviewer.yml`
**New step**: "Check Release Age" (after ecosystem detection)
**Spec refs**: FR-002, FR-008, FR-009, SC-003

**Changes**:

1. **New step** with ecosystem-specific release date lookups:
   - GitHub Actions: `gh api repos/{dep_name}/releases/tags/v{version}` for `.published_at`, falling back to tag date
   - Go modules: `curl` to Go proxy `@v/v{version}.info` for `.Time`
   - Python/pip: `curl` to PyPI JSON API for `.urls[0].upload_time_iso_8601`
   - Unknown/failure: `release_age_hours=-1`

2. **Compute age**: `(now_epoch - release_epoch) / 3600`

3. **Output**: `release_age_hours` added to job outputs

**Estimated change**: 0 lines → ~35 lines (+35 lines)

### Task 4: Update Auto-Approval Criteria

**File**: `.github/workflows/ci_dependencies.yml`
**Job**: `approve_dependabot_prs` (current lines 62-86)
**Spec refs**: FR-001, FR-002, FR-003, FR-004, FR-005, SC-001, SC-002

**Changes**:

1. **Replace step-level `if:` condition** (line 71):
   - Remove: `env.RISK_LEVEL != 'high' && env.REVIEW_CONCLUSION == 'success' && env.UPDATES_COUNT > 10`
   - Replace with `needs.*` output references:
     `needs.call_dependabot_reviewer.outputs.risk_level != 'high' && needs.call_deps_reviewer.outputs.review_conclusion == 'success' && needs.call_dependabot_reviewer.outputs.release_age_hours != '-1' && needs.call_dependabot_reviewer.outputs.release_age_hours >= env.MIN_RELEASE_AGE_HOURS`

2. **Remove step-level `env:` block** (lines 72-75) -- no longer needed since `needs.*` is used directly

3. **Update approval message** to include rationale

**Estimated change**: 5 lines → ~10 lines (+5 lines)

### Task 5: Update PR Comment

**File**: `.github/workflows/ci_dependencies.yml`
**Job**: `comment_on_dependabot_prs` (current lines 25-61)
**Spec refs**: FR-006, FR-007, FR-010, FR-011, SC-004, SC-005

**Changes**:

1. **Add `release_age_hours`** from `needs.call_dependabot_reviewer.outputs.release_age_hours` to env block

2. **Update comment body** to include:
   - Release age information (hours since release, or "unknown")
   - Auto-approval rationale (which criteria passed/failed)
   - Keep dependency usage as informational (existing)
   - Keep maintainer checklist (existing)

3. **Handle edge cases in display**:
   - Usage count of 0 or unavailable: display as "unavailable" not "0 repositories"
   - Release age of -1: display as "unknown (manual review required)"

**Estimated change**: 18 lines → ~30 lines (+12 lines)

## Validation Plan

1. **Lint**: `make lint` must pass (yamllint on all YAML files)
2. **Manual test scenarios** (on a test repository with the updated workflows):
   - Trigger dependabot PR with patch update → verify auto-approval fires
   - Trigger dependabot PR with major update → verify no auto-approval
   - Trigger dependabot PR for composite action file → verify extraction succeeds (the PR #806 scenario)
   - Trigger dependabot PR for very recent release → verify release age blocks approval
   - Trigger dependabot PR where usage search fails → verify approval still proceeds
3. **Sync verification**: Run `make sync-dry-run` to confirm `ci_dependencies.yml` is in the sync list
