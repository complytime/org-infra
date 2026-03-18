# Research: Centralize CRAP Load Analysis Workflow

**Date**: 2026-03-18

## R1: Cross-Repository Workflow Reference Syntax

**Decision**: Use `complytime/org-infra/.github/workflows/reusable_crapload_analysis.yml@main` as the workflow reference in consumer workflows.

**Rationale**: This is the standard GitHub Actions syntax for cross-repository reusable workflow calls. Using `@main` ensures consumers always get the latest version. This matches how other org-infra reusable workflows are consumed.

**Alternatives considered**:
- `@<sha>` pinning — more secure but creates maintenance burden for every update. Not used by other org-infra workflows.
- `@<tag>` pinning — requires a release tagging workflow. Org-infra does not currently use release tags for workflows.

## R2: Sync Exclusion List for Go-Only Workflow

**Decision**: Exclude non-Go repositories from `ci_crapload.yml` sync using per-file `exclude_repos` in `sync-config.yml`.

**Rationale**: The existing `.golangci.yml` sync entry already excludes non-Go repos (`complyscribe`, `complytime-demos`, `complytime-policies`, `vagrant-boxes`). The CRAP analysis consumer workflow should use the same exclusion list plus `community` (which was added to the org after the golangci entry). This pattern is already established in the sync config.

**Alternatives considered**:
- Syncing to all repos and relying on the workflow to skip (no Go files detected) — wasteful, creates noise in non-Go repos.
- Creating a separate "go-repos" list in sync config — over-engineering for current needs; can be introduced later if more Go-specific workflows are added.

## R3: Indentation Standard

**Decision**: Normalize the workflow from 4-space to 2-space indentation.

**Rationale**: The source workflow in complyctl uses 4-space YAML indentation. Org-infra's `.yamllint.yml` enforces `spaces: consistent`, and all existing org-infra workflows use 2 spaces. The migrated workflow MUST be normalized to 2-space indentation for consistency and to pass linting.

**Alternatives considered**:
- Keeping 4-space — would pass yamllint (consistent within file) but would be inconsistent with every other workflow in org-infra. Violates Constitution Principle IV (Readability First) due to inconsistency.

## R4: Gaze Tool Dependency

**Decision**: Accept Gaze as an external dependency installed via `go install` at runtime.

**Rationale**: Gaze is the established tool for CRAP/GazeCRAP analysis in the ComplyTime ecosystem. It's actively maintained, publicly available on GitHub, and already validated in complyctl's CI. Installing via `go install` is the standard Go tool distribution pattern.

**Alternatives considered**:
- Pre-built binary download — Gaze distributes via `go install`, not binary releases. Would require maintaining a fork or custom build.
- Container-based Gaze — over-engineering; `go install` is simpler and aligns with Constitution Principle II (Simplicity).
