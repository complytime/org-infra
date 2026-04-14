# Feature Specification: Release Workflow for org-infra

## Document Overview

This specification details a lightweight release process for `complytime/org-infra` that enables
downstream repositories to pin reusable workflows to semver tags or release commit SHAs. Since
org-infra ships no binaries, the process is intentionally minimal: tag creation, automated changelog
generation from merged PRs, and a published GitHub Release.

**Key Metadata:**
- Workflow Files: `.github/workflows/release.yml`, `.github/workflows/release_notes_preview.yml`
- Configuration: `.github/release-drafter.yml`
- Date: 2026-04-13
- Current Status: **In Progress** — workflow files drafted, spec under review
- First Consumer: All complytime org repositories that reference `complytime/org-infra` reusable workflows

## Background and Motivation

The complytime org-infra repository provides 13 reusable GitHub Actions workflows consumed by
downstream repositories across the organization. Today, consumers reference these workflows by
branch name (e.g., `@main`) or commit SHA. This creates two problems:

1. **No stability guarantee** — `@main` is a moving target. A breaking workflow change lands on main
   and immediately affects all consumers without notice.
2. **No versioning signal** — consumers cannot distinguish a patch fix from a breaking change without
   reading every commit.

A semver-tagged release process solves both problems. Consumers can pin to a release tag
(e.g., `@v1.2.0`) for stability, and the version number communicates the nature of changes.

## Core User Scenarios

### Priority 1: Create a Versioned Release

A repository maintainer triggers the release workflow via `workflow_dispatch`, providing a semver tag
(e.g., `v1.0.0`). The workflow validates the tag format, creates the tag if it does not exist, and
publishes a GitHub Release with auto-generated changelog from merged PRs since the last release.

**Test Coverage:** Validates that the tag is created, the GitHub Release is published, and the
changelog is correctly categorized by PR labels.

### Priority 2: Pin Reusable Workflows to a Release

A downstream repository maintainer updates their caller workflow to reference a specific release tag
instead of `@main`. The pinned version continues to work until the consumer explicitly upgrades.

**Test Coverage:** Validates that `uses: complytime/org-infra/.github/workflows/reusable_ci.yml@v1.0.0`
resolves correctly and the workflow executes as expected.

### Priority 3: Preview Release Notes Before Publishing

A maintainer runs the release notes preview workflow to see what the next release changelog will
contain, without creating a release. This enables review of PR categorization and version resolution
before committing to a release.

**Test Coverage:** Validates that the dry-run output matches expected PR groupings and the resolved
version is correct.

## Edge Cases Addressed

- **Tag already exists**: If the tag already exists when the release workflow runs, the tag creation
  step is skipped and the existing tag is used for the release.
- **Tag format validation**: The workflow rejects tags that do not match semver format
  (`v<major>.<minor>.<patch>`).
- **No PRs since last release**: Release drafter produces a "no changes" message rather than an
  empty changelog.
- **Unlabeled PRs**: PRs without labels are categorized by the autolabeler based on conventional
  commit prefixes and file paths. PRs that match no rule are excluded from the changelog.
- **Dependabot PRs**: Excluded from changelog via `exclude-contributors` to reduce noise.
- **First release**: When no previous tag exists, the changelog includes all merged PRs.

## Functional Requirements Summary

The release process must:

1. **Provide a manual release trigger**: Via `workflow_dispatch` with a required semver tag input.
2. **Validate tag format**: Reject tags not matching `v<major>.<minor>.<patch>`.
3. **Enforce release from default branch**: Reject triggers from any ref other than `refs/heads/main`.
4. **Create the tag if absent**: Tag the current branch HEAD and push to origin.
5. **Publish a GitHub Release**: With auto-generated changelog categorized by PR labels.
6. **Auto-label PRs**: Map conventional commit prefixes and file paths to changelog categories.
7. **Resolve version from labels**: Major/minor/patch version bumps determined by PR labels, defaulting
   to patch.
8. **Provide changelog categories**: Breaking changes, Workflows, Compliance, Sync, Features, Fixes,
   Performance, Maintenance.
9. **Exclude bot contributions**: Dependabot and github-actions bot PRs excluded from changelog.
10. **Support dry-run preview**: A separate workflow previews release notes without creating a release.
11. **Use pinned action SHAs**: All `uses:` references pinned to full commit SHA with version comment.
12. **Follow least-privilege permissions**: `contents: write` only on the release job; preview is
    read-only.

## Success Metrics

- Maintainers can create a release by triggering a single workflow with a version tag.
- Downstream repositories can pin to `@v<major>.<minor>.<patch>` and receive no changes until
  they explicitly upgrade.
- Release notes accurately categorize PRs by type (workflows, compliance, features, fixes, etc.).
- The release process requires no local tooling — everything runs via GitHub Actions and `gh` CLI.
- `yamllint` passes on all workflow files.

## Scope Boundaries

**Included:**
- `.github/workflows/release.yml` — manual release workflow
- `.github/workflows/release_notes_preview.yml` — dry-run preview workflow
- `.github/release-drafter.yml` — changelog and version configuration
- Consumer pinning documentation

**Excluded:**
- Automated release triggers (e.g., on merge to main) — releases are intentionally manual
- Binary artifact building or signing — org-infra has no binaries
- Release branch strategy — releases are cut from `main`
- Migration tooling for existing consumers — consumers upgrade at their own pace
- Webhook or notification integration (Slack, email, etc.)
