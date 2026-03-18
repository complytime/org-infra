# Feature Specification: Centralize CRAP Load Analysis Workflow

**Feature Branch**: `001-crapload-workflow`
**Created**: 2026-03-18
**Status**: Draft
**Input**: User description: "Move reusable CRAP Load Analysis workflow from complyctl to org-infra so Go repositories across the organization can adopt it."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Adopt CRAP Load Analysis in a Go Repository (Priority: P1)

A maintainer of a Go repository within the ComplyTime organization wants to add CRAP (Change Risk Anti-Patterns) load analysis to their CI pipeline. They add a consumer workflow to their repository that references the reusable workflow from org-infra, and CRAP analysis runs automatically on pull requests.

**Why this priority**: This is the core value proposition — enabling any Go repository to adopt CRAP load analysis without duplicating workflow code.

**Independent Test**: Can be fully tested by creating a consumer workflow in a Go repository that calls the reusable workflow from org-infra and verifying that CRAP analysis results appear on a pull request.

**Acceptance Scenarios**:

1. **Given** a Go repository with a consumer workflow referencing the org-infra reusable workflow, **When** a pull request is opened that modifies Go files, **Then** the CRAP load analysis runs and posts a summary comment on the PR.
2. **Given** a Go repository with a consumer workflow, **When** a pull request is opened that does not modify any Go files, **Then** the workflow reports "No Go code changes detected" without running analysis.
3. **Given** a Go repository with a committed baseline file, **When** CRAP analysis runs on a PR, **Then** the results include regressions, improvements, and new function comparisons against the baseline.

---

### User Story 2 - Detect CRAP Score Regressions on Pull Requests (Priority: P1)

A maintainer wants to prevent code quality degradation. When a contributor submits a pull request that increases the CRAP score of existing functions or introduces new functions exceeding the threshold, the workflow blocks the PR and clearly reports which functions regressed.

**Why this priority**: Regression detection is the primary quality gate that makes the workflow actionable, not just informational.

**Independent Test**: Can be tested by submitting a PR that intentionally increases complexity without adding test coverage, and verifying the workflow fails with a clear regression report.

**Acceptance Scenarios**:

1. **Given** a baseline file exists and a PR increases the CRAP score of an existing function, **When** the analysis completes, **Then** the workflow status is "fail" and the PR comment lists the regressed functions with before/after scores.
2. **Given** a PR introduces a new function with a CRAP score above the configured threshold, **When** the analysis completes, **Then** the workflow status is "fail" and the new function is flagged as a violation.
3. **Given** a PR improves CRAP scores (adds tests or reduces complexity), **When** the analysis completes, **Then** the workflow status is "pass" and improvements are listed in the PR comment.

---

### User Story 3 - Sync Consumer Workflow to Go Repositories (Priority: P2)

The org-infra sync mechanism distributes a consumer workflow template to Go repositories across the organization, so new repositories automatically get CRAP load analysis without manual setup.

**Why this priority**: Automates adoption across the organization but depends on the reusable workflow (P1) being available first.

**Independent Test**: Can be tested by adding the consumer workflow to the sync configuration and running a dry-run sync to verify it targets the correct repositories.

**Acceptance Scenarios**:

1. **Given** the consumer workflow is added to the sync configuration, **When** the sync script runs, **Then** Go repositories receive the consumer workflow file.
2. **Given** the sync configuration excludes non-Go repositories, **When** the sync runs, **Then** Python-only repositories do not receive the consumer workflow.

---

### Edge Cases

- What happens when no baseline file exists in a repository? The workflow skips per-function comparison and passes, logging a warning.
- What happens when the Gaze tool fails to install or produce output? The workflow steps use failure guards and the analysis continues gracefully, uploading whatever data is available.
- What happens when a repository uses a non-standard Go module structure (e.g., multi-module monorepo)? The workflow accepts a configurable `packages` input to specify which packages to analyze.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The reusable workflow MUST be hosted in org-infra and callable via `workflow_call` by any repository in the organization.
- **FR-002**: A consumer workflow template MUST be provided for repositories to invoke the reusable workflow on pull requests targeting `main`.
- **FR-003**: The workflow MUST detect which Go packages were changed in a pull request and scope analysis to only those packages.
- **FR-004**: The workflow MUST generate a coverage profile, run CRAP analysis, and compare results against a committed baseline file when available.
- **FR-005**: The workflow MUST post or update a single PR comment (idempotent) with a summary table including metrics such as average complexity, coverage, CRAP scores, regressions, improvements, and new functions.
- **FR-006**: The workflow MUST fail the check when regressions or new-function threshold violations are detected.
- **FR-007**: The workflow MUST support configurable inputs for Go version detection, analysis tool version, baseline file path, target packages, coverage profile path, new-function threshold, and PR comment toggle.
- **FR-008**: The consumer workflow template MUST be added to the org-infra sync configuration to distribute it to Go repositories, excluding non-Go repositories.
- **FR-009**: The workflow MUST upload analysis artifacts for retention.
- **FR-010**: The workflow MUST follow the Principle of Least Privilege, requesting only the minimum permissions required for reading source code and writing PR comments.

### Key Entities

- **CRAP Score**: A metric combining cyclomatic complexity and code coverage to identify risky functions. Higher scores indicate higher risk.
- **Baseline File**: A committed JSON file containing per-function CRAP scores from a known-good state, used for regression detection.
- **Consumer Workflow**: A repository-level workflow file that invokes the reusable workflow with repository-specific configuration.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Any Go repository in the organization can adopt CRAP load analysis by adding a single consumer workflow file, with no other setup required beyond having Go tests.
- **SC-002**: CRAP score regressions are detected and reported within the standard CI pipeline run, without requiring a separate review step.
- **SC-003**: The workflow produces actionable PR comments that clearly identify which functions regressed, improved, or are new, with before/after scores.
- **SC-004**: The reusable workflow is adopted by at least the complyctl repository (migrating from its local copy) as validation of the centralization.

## Assumptions

- The CRAP analysis tool is publicly available and installable in CI environments.
- Go repositories in the organization have existing test suites that produce meaningful coverage data.
- The org-infra sync mechanism is the established method for distributing workflow files to organization repositories.
- The main-branch workflow for baseline updates and metrics publishing is repository-specific and will NOT be centralized — each repository manages its own baseline publishing strategy.
- Non-Go repositories are excluded from sync via the exclusion list in the sync configuration.

## Out of Scope

- Baseline file generation or initialization — repositories are responsible for committing their own baseline files.
- Main-branch metrics publishing workflows — these are repository-specific and stay in each repository.
- CRAP analysis tool development or bug fixes — the workflow consumes it as an external dependency.
- Customization of CRAP thresholds beyond the existing input parameters.
