# Implementation Plan: Centralize CRAP Load Analysis Workflow

**Branch**: `001-crapload-workflow` | **Date**: 2026-03-18 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `/specs/001-crapload-workflow/spec.md`

## Summary

Move the reusable CRAP Load Analysis workflow from complyctl to org-infra, provide a consumer workflow template, and add sync configuration to distribute it to Go repositories across the organization. This is a workflow migration — the existing implementation is proven and requires only path reference changes, not logic changes.

## Technical Context

**Language/Version**: YAML (GitHub Actions workflow syntax)
**Primary Dependencies**: Gaze (`github.com/unbound-force/gaze`), Go toolchain (detected from `go.mod`), `jq`, `bc`
**Storage**: N/A
**Testing**: Validated via yamllint (local), MegaLinter (CI), and dry-run sync verification
**Target Platform**: GitHub Actions (ubuntu-latest runners)
**Project Type**: CI/CD infrastructure (reusable workflow + consumer template + sync config)
**Performance Goals**: N/A (CI workflow — runtime bounded by repository test suite)
**Constraints**: Workflow MUST follow least-privilege permissions; MUST pass yamllint
**Scale/Scope**: Targets all Go repositories in the ComplyTime organization (~8 repos based on golangci exclusion list)

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Evidence |
|-----------|--------|----------|
| I. Single Source of Truth | PASS | Moving workflow to org-infra centralizes it as the single source; eliminates duplicate in complyctl |
| II. Simplicity & Isolation | PASS | Reusable workflow has single responsibility (CRAP analysis); consumer workflow is a thin caller |
| III. Incremental Improvement | PASS | This PR only moves the workflow and adds sync config — no unrelated changes |
| IV. Readability First | PASS | Workflow has descriptive step names, header comment, and clear input descriptions |
| V. Do Not Reinvent the Wheel | PASS | Uses existing Gaze tool; leverages established org-infra sync mechanism |
| VI. Composability | PASS | Reusable workflow outputs status/counts for downstream composition; consumer workflow is modular |
| VII. Convention Over Configuration | PASS | Sensible defaults for all inputs (go.mod path, packages, threshold, etc.) |
| YAML Naming Conventions | PASS | `reusable_crapload_analysis.yml` and `ci_crapload.yml` follow org conventions |
| YAML Security | PASS | Permissions scoped to `contents: read` + `pull-requests: write` (minimum required) |
| YAML Design | PASS | All inputs have descriptions, required flags, and defaults where appropriate |
| YAML Formatting | PASS | Header comment present; linted with yamllint |
| Lint Configuration Awareness | PASS | Must pass `.yamllint.yml` and MegaLinter CI checks |

**Gate result**: PASS — no violations detected.

## Project Structure

### Documentation (this feature)

```text
specs/001-crapload-workflow/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output (minimal — no data model)
├── quickstart.md        # Phase 1 output
└── tasks.md             # Phase 2 output (/speckit.tasks command)
```

### Source Code (repository root)

```text
.github/workflows/
├── reusable_crapload_analysis.yml   # NEW — reusable workflow (moved from complyctl)
└── ci_crapload.yml                  # NEW — consumer workflow template (synced to Go repos)

sync-config.yml                      # MODIFIED — add ci_crapload.yml sync entry
```

**Structure Decision**: This feature adds two workflow files to the existing `.github/workflows/` directory and modifies the sync configuration. No new directories or structural changes needed — follows the established org-infra pattern.

## Migration Details

### Consumer Workflow Reference Change

When the reusable workflow moves from complyctl to org-infra, consumer workflows in other repositories must reference it cross-repository:

- **Before** (local in complyctl): `uses: ./.github/workflows/reusable_crapload_analysis.yml`
- **After** (centralized in org-infra): `uses: complytime/org-infra/.github/workflows/reusable_crapload_analysis.yml@main`

### Sync Configuration

The consumer workflow (`ci_crapload.yml`) will be synced to Go repositories. Non-Go repositories must be excluded. The exclusion list mirrors the `ruff.toml` sync entry (which targets Python repos — inverse of Go repos):

**Exclude from ci_crapload.yml sync**:
- `complyscribe` — Python-only
- `complytime-demos` — demo/docs repository
- `complytime-policies` — policy definitions, no Go code
- `vagrant-boxes` — infrastructure, no Go code
- `community` — community docs, no Go code

### Indentation Normalization

The source workflow in complyctl uses 4-space indentation. Org-infra workflows use 2-space indentation. The workflow MUST be normalized to 2-space indentation to pass yamllint with the org-infra `.yamllint.yml` configuration (which enforces `spaces: consistent` and the repo standard is 2 spaces).

## Complexity Tracking

No constitution violations to justify. Feature is a straightforward migration with no architectural complexity.
