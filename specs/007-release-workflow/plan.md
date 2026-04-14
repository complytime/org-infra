# Implementation Plan: Release Workflow for org-infra

**Branch**: `feat/adds-release-workflow` | **Date**: 2026-04-13 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `/specs/007-release-workflow/spec.md`

## Summary

Add a lightweight release process for org-infra consisting of three files: a manual release workflow
that creates tags and publishes GitHub Releases with auto-generated changelogs, a dry-run preview
workflow, and a release-drafter configuration that maps PR labels and conventional commit prefixes
to semver categories.

## Technical Context

**Language/Version**: YAML (GitHub Actions workflow syntax)
**Primary Dependencies**:
- `release-drafter/release-drafter` — changelog generation and version resolution from PR labels
- `actions/checkout` — code checkout (already pinned in org-infra codebase)
- `actions/upload-artifact` — preview artifact upload (already pinned in org-infra codebase)

**Testing**: Validated via `yamllint` (local) and manual `workflow_dispatch` trigger.
**Target Platform**: GitHub Actions (`ubuntu-latest`)
**Project Type**: CI/CD infrastructure (release tooling)
**Constraints**: Must pass `.yamllint.yml`; all `uses:` pinned to full SHA; least-privilege permissions.

## Constitution Check

| Principle | Status | Evidence |
|-----------|--------|----------|
| I. Single Source of Truth | PASS | Version resolved from PR labels via release-drafter config; no separate VERSION file |
| II. Simplicity & Isolation | PASS | Three focused files with clear responsibilities; no build steps or artifacts |
| III. Incremental Improvement | PASS | New files only; no changes to existing workflows |
| IV. Readability First | PASS | Header comments, descriptive step names, consumer guidance in workflow comments |
| V. Do Not Reinvent the Wheel | PASS | Uses release-drafter for changelog generation rather than custom scripting |
| VI. Composability | PASS | Release workflow is independent; does not couple to other workflows |
| VII. Convention Over Configuration | PASS | Semver convention; conventional commit mapping via autolabeler |
| YAML Naming Conventions | NOTE | `release.yml` does not follow `reusable_*` or `ci_*` prefix — intentional, as it is neither reusable nor a CI workflow |
| YAML Security | PASS | Workflow-level permissions none; job-level minimal grant; all user inputs routed through `env:` blocks; release restricted to `main` branch |
| YAML Formatting | PASS | Header comment; 2-space indent; yamllint clean |

**Gate result**: PASS — no violations detected.

## Project Structure

```text
specs/007-release-workflow/
├── spec.md                    # Feature specification
├── plan.md                    # This file
├── tasks.md                   # Actionable task list
├── quickstart.md              # Quick reference
└── checklists/
    └── requirements.md        # Quality gate checklist

.github/
├── release-drafter.yml        # Release drafter configuration
└── workflows/
    ├── release.yml            # Manual release workflow
    └── release_notes_preview.yml  # Dry-run preview workflow
```

## Action Version Pinning

| Action | SHA (pinned) | Version |
|--------|-------------|---------|
| `actions/checkout` | `de0fac2e4500dabe0009e67214ff5f5447ce83dd` | v6.0.2 |
| `release-drafter/release-drafter` | `139054aeaa9adc52ab36ddf67437541f039b88e2` | v7.1.1 |
| `actions/upload-artifact` | `bbbca2ddaa5d8feaa63e36b76fdaad77386f024f` | v7.0.0 |

## Release Drafter Configuration Design

### Version Resolution

PR labels drive semver bumps. The `version-resolver` in `.github/release-drafter.yml`:

| Bump | Labels |
|------|--------|
| Major | `breaking`, `major` |
| Minor | `feature`, `enhancement`, `minor` |
| Patch | `fix`, `documentation`, `maintenance`, `patch`, `performance`, `workflows`, `compliance`, `sync-config` |
| Default | patch (when no matching labels) |

### Autolabeler

Maps conventional commit prefixes and file paths to labels automatically:

| Pattern | Label |
|---------|-------|
| `feat:` title | `feature` |
| `fix:` title | `fix` |
| `chore:` / `maintenance:` title | `maintenance` |
| `docs:` title | `documentation` |
| `ci:` / `build:` / `refactor:` / `test:` title | `automation` |
| Files in `.github/workflows/` or `.github/actions/` | `workflows` |
| Files in `compliance/` | `compliance` |
| Files matching `sync-config.yml`, `complytime.yaml`, `scripts/**` | `sync-config` |

### Changelog Categories

PRs are grouped into sections in this order:
1. Breaking changes
2. Workflows & GitHub Actions
3. Compliance & policy assets
4. Sync & repository configuration
5. Features
6. Bug fixes
7. Performance
8. Maintenance

### Exclusions

- PRs labeled `skip-changelog` are excluded
- Contributions by `dependabot[bot]` and `github-actions[bot]` are excluded

## Consumer Pinning Strategy

After the first release, downstream repos can reference workflows three ways:

```yaml
# Recommended: pin to semver tag for stability + readability
uses: complytime/org-infra/.github/workflows/reusable_ci.yml@v1.0.0

# Maximum reproducibility: pin to the release commit SHA
uses: complytime/org-infra/.github/workflows/reusable_ci.yml@<sha>

# Living edge (current behavior, not recommended for production):
uses: complytime/org-infra/.github/workflows/reusable_ci.yml@main
```

## Initial Release Baseline

The first release should be tagged `v0.1.0` to signal that the project is pre-1.0 and the
reusable workflow interfaces may still evolve. The `v1.0.0` tag should be reserved for when the
workflow interfaces are considered stable.

## Complexity Tracking

No constitution violations to justify. The release process is intentionally minimal: three config/
workflow files, no custom scripting beyond tag format validation and conditional tag creation.
