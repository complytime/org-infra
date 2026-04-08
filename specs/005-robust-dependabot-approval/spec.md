# Feature Specification: Robust Dependabot Auto-Approval

**Feature Branch**: `005-robust-dependabot-approval`
**Created**: 2026-04-08
**Status**: Draft
**Input**: User description: "Lets review and update the reusable workflows for dependabot reviews to make them more robust. First, it is not automatically approving PR if the dependency usage is not determined. This is frigile since not always the dependency usage can be queried due to the dependency nature or API limits. Lets treat the dependency usage as a supporting information for maintainers and not to decide about automatically approving a PR. The automatic approval should be made if the dependency is at least 24 hours released, there are no vulnerabilities and CI tests are passing."

## Clarifications

### Session 2026-04-08

- Q: How should dependency information extraction sources be prioritized — commit metadata vs diff parsing? → A: Commit metadata as primary source, diff parsing as supplementary enrichment (e.g., for SHA refs).

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Reliable Auto-Approval for Safe Dependency Updates (Priority: P1)

As a repository maintainer, I want dependabot pull requests that meet safety criteria (non-major version bump, at least 24 hours since release, no known vulnerabilities, CI tests passing) to be automatically approved regardless of whether dependency usage data could be retrieved, so that safe updates are not unnecessarily blocked by external API limitations.

**Why this priority**: This is the core problem being solved. The current auto-approval gate requires more than 10 repositories to already use the updated version, which fails silently for Python dependencies, unknown ecosystems, and when GitHub's code search API is rate-limited. This causes safe updates to stall, increasing maintenance burden and security exposure across all org repositories.

**Independent Test**: Can be fully tested by submitting a dependabot PR with a patch-level update for a dependency that was released more than 24 hours ago, has no vulnerabilities, and passes CI -- the PR should be auto-approved even if dependency usage data is unavailable.

**Acceptance Scenarios**:

1. **Given** a dependabot PR with a patch update where the new version was released more than 24 hours ago and has no known vulnerabilities, **When** CI tests pass and dependency usage data is unavailable, **Then** the PR is automatically approved.
2. **Given** a dependabot PR with a minor update where the new version was released more than 24 hours ago and has no known vulnerabilities, **When** CI tests pass and dependency usage shows 0 repositories, **Then** the PR is automatically approved.
3. **Given** a dependabot PR with a patch update where the new version was released only 2 hours ago and has no known vulnerabilities, **When** CI tests pass, **Then** the PR is NOT automatically approved (release too recent).
4. **Given** a dependabot PR with a minor update that has a known vulnerability flagged by the dependency review, **When** CI tests pass, **Then** the PR is NOT automatically approved.
5. **Given** a dependabot PR with a major version bump where the new version was released more than 24 hours ago with no vulnerabilities, **When** CI tests pass, **Then** the PR is NOT automatically approved (major updates require manual review).

---

### User Story 2 - Dependency Usage as Informational Context for Maintainers (Priority: P2)

As a repository maintainer reviewing a dependabot PR, I want to see dependency usage information (how many repositories already use the updated version) presented as supplementary context in the PR comment, so that I can make informed decisions during manual review without this data blocking automated processes.

**Why this priority**: Dependency usage data is valuable for manual decision-making but unreliable as an automated gate. Keeping it visible in PR comments retains its informational value while removing it from the approval decision path.

**Independent Test**: Can be tested by triggering a dependabot PR and verifying the PR comment includes dependency usage information when available, and shows a clear "unavailable" status when the data could not be retrieved, without either state affecting the auto-approval outcome.

**Acceptance Scenarios**:

1. **Given** a dependabot PR where dependency usage data was successfully retrieved, **When** the PR comment is posted, **Then** the comment displays the usage count as informational context (not as an approval criterion).
2. **Given** a dependabot PR where dependency usage data could not be retrieved (API failure, unsupported ecosystem), **When** the PR comment is posted, **Then** the comment clearly indicates that usage data is unavailable and does not present this as a blocker.
3. **Given** a dependabot PR where dependency usage data shows 0 repositories, **When** a maintainer views the PR comment, **Then** the comment presents this as informational context alongside other review data (risk level, vulnerabilities, release age).

---

### User Story 3 - Release Age Verification Before Auto-Approval (Priority: P3)

As a security-conscious organization, I want the auto-approval process to verify that a dependency release is at least 24 hours old before approving it, so that newly published (and potentially compromised or buggy) releases are not automatically merged into our repositories.

**Why this priority**: This is a new safety gate that does not exist in the current workflow. It provides a cooling-off period that allows the community to identify issues with new releases before they are automatically merged. While important, it builds on top of the core approval logic change (P1).

**Independent Test**: Can be tested by creating or simulating a dependabot PR for a dependency version released less than 24 hours ago and verifying that auto-approval does not trigger, then waiting (or simulating) past the 24-hour threshold and verifying it would then qualify.

**Acceptance Scenarios**:

1. **Given** a dependabot PR for a dependency version released 25 hours ago, **When** all other approval criteria are met, **Then** the release age check passes and does not block auto-approval.
2. **Given** a dependabot PR for a dependency version released 12 hours ago, **When** all other approval criteria are met, **Then** the release age check fails and the PR is not auto-approved.
3. **Given** a dependabot PR where the release date cannot be determined, **When** all other approval criteria are met, **Then** the system treats the release age as unknown and does NOT auto-approve the PR.
4. **Given** a dependabot PR for a dependency version released exactly 24 hours ago, **When** all other approval criteria are met, **Then** the release age check passes (the threshold is "at least 24 hours").

---

### User Story 4 - Robust Dependency Information Extraction (Priority: P1)

As a repository maintainer, I want the dependency information extraction step to reliably identify the dependency name, version, and update type from every dependabot PR — even when diff parsing fails — so that downstream processing (PR comment, auto-approval decision) is never blocked by extraction errors.

**Why this priority**: Equal to P1 because it is a prerequisite for reliable auto-approval. The current extraction mechanism uses fragile diff parsing that crashes on real-world PRs (e.g., composite action files in `.github/actions/`), producing no outputs and blocking all downstream jobs. Dependabot commit messages typically contain structured metadata (`dependency-name`, `dependency-version`, `update-type`) that is machine-generated, making it a reliable primary source when present.

**Independent Test**: Can be tested by triggering the workflow on a dependabot PR that changes a composite action file (e.g., in `.github/actions/`) and verifying that dependency name, version, and risk level are correctly extracted from the commit message metadata, and that the PR comment and auto-approval decision proceed normally.

**Acceptance Scenarios**:

1. **Given** a dependabot PR that updates an action in a composite action file (`.github/actions/`), **When** the extraction step runs, **Then** the dependency name, version, and update type are correctly extracted from the commit message metadata and all downstream jobs execute successfully.
2. **Given** a dependabot PR where diff parsing (supplementary enrichment) fails for any reason, **When** the extraction step runs, **Then** the system still produces valid outputs from commit metadata or title fallback (dependency name, version, risk level) without crashing.
3. **Given** a dependabot PR where both diff parsing and commit metadata extraction succeed, **When** the extraction step runs, **Then** commit metadata is used for name/version/update-type and diff parsing enriches with supplementary data (e.g., SHA-pinned action refs for usage search queries).
4. **Given** a dependabot PR where commit metadata is malformed or missing, **When** the extraction step runs, **Then** the system falls back to diff parsing and then to commit title parsing, producing the best available data without crashing.

---

### Edge Cases

- What happens when the release date of a dependency version cannot be determined (e.g., private registry, missing metadata)? The system should not auto-approve and should indicate this in the PR comment.
- What happens when CI tests are still running or have not yet completed? The auto-approval step should depend on CI completion and only proceed when tests have concluded successfully.
- What happens when the dependency review action itself fails (not "failure" result, but an actual execution error)? The system should treat this as a non-passing review and not auto-approve.
- What happens when the dependabot PR updates multiple dependencies in a single PR? The extraction processes the first dependency found; the risk level defaults to the highest-risk dependency classification and the release age check applies to the extracted dependency. Grouped updates with mixed risk levels require manual review.
- What happens when GitHub's API rate limit is hit during the release age lookup? The system should fail safely by not auto-approving and logging the issue in the PR comment.
- What happens when the GitHub code search API times out during the dependency usage lookup? The system should produce `updates_count=0` after retries and display "unavailable" in the PR comment. Since usage is informational only (FR-001), this does not affect the auto-approval decision.
- What happens when the dependency information extraction step encounters an error (e.g., malformed diff, unexpected file format)? The step must never crash; it should produce degraded outputs and allow downstream jobs to proceed with available data.
- What happens when all extraction methods fail (no commit metadata, no diff, no title match)? The system should post a PR comment indicating extraction failure, default risk to high, and not auto-approve.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The auto-approval decision MUST NOT use dependency usage count (number of repositories using the updated version) as a gating criterion.
- **FR-002**: The auto-approval decision MUST require that the dependency's new version was released at least 24 hours before the approval check runs.
- **FR-003**: The auto-approval decision MUST require that the dependency review (vulnerability and security assessment) has passed successfully.
- **FR-004**: The auto-approval decision MUST require that CI tests have completed and passed. This is enforced by GitHub's required status checks on the `main` branch -- auto-approval grants a review approval but does not merge; merging is blocked until all required checks pass.
- **FR-005**: The auto-approval decision MUST NOT approve major version bumps (these always require manual review).
- **FR-006**: The workflow MUST continue to collect and report dependency usage data in the PR comment as informational context for maintainers.
- **FR-007**: When dependency usage data cannot be retrieved, the PR comment MUST clearly indicate this status without presenting it as an approval blocker.
- **FR-008**: The workflow MUST determine the release date of the updated dependency version and include it in the PR comment.
- **FR-009**: When the release date of the updated dependency version cannot be determined, the system MUST NOT auto-approve the PR and MUST indicate this in the PR comment.
- **FR-010**: The PR comment MUST include the release age information alongside existing data (risk level, dependency review result, dependency usage).
- **FR-011**: The auto-approval criteria MUST be clearly documented in the PR comment so maintainers understand why a PR was or was not auto-approved.
- **FR-012**: The dependency information extraction step MUST use dependabot's structured commit message metadata (dependency-name, dependency-version, update-type) as the primary source for identifying the dependency name, version, and update type.
- **FR-013**: Diff parsing MUST be used as supplementary enrichment (e.g., extracting SHA-pinned action references for usage search queries) but MUST NOT be the primary source for dependency name or version.
- **FR-014**: The dependency information extraction step MUST NOT crash or produce a non-zero exit code under any circumstances. If all extraction methods fail, it MUST output safe defaults (empty name, unknown version, high risk) and allow downstream jobs to proceed.
- **FR-015**: The extraction step MUST implement a fallback chain: (1) commit message metadata, (2) diff parsing, (3) commit title/body parsing — each method attempted in order, with later methods used only to fill gaps not covered by earlier methods.

### Key Entities

- **Dependency Update**: Represents a single dependency version change in a dependabot PR. Key attributes: dependency name, ecosystem (Go including submodules, Python, GitHub Actions), old version, new version, risk level (low/medium/high), update type (patch/minor/major), release date of new version, extraction source (commit metadata, diff, title).
- **Approval Decision**: The outcome of evaluating all auto-approval criteria. Key attributes: risk level assessment, release age (hours since release), vulnerability review result, CI test result, final decision (approve/manual review), reason for decision.
- **PR Comment**: The structured summary posted on each dependabot PR. Contains: dependency review conclusion, risk level, dependency usage count (informational), release age, approval decision rationale, maintainer checklist.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Dependabot PRs with patch or minor updates that meet all safety criteria (24h+ release age, no vulnerabilities, CI passing) are auto-approved within the workflow run time, regardless of dependency usage data availability.
- **SC-002**: Zero dependabot PRs are incorrectly blocked solely because dependency usage data could not be retrieved.
- **SC-003**: All dependabot PRs for versions released less than 24 hours ago require manual maintainer review, adding a safety buffer against compromised or unstable releases.
- **SC-004**: Maintainers can see dependency usage information (when available) in every dependabot PR comment to support their manual review decisions.
- **SC-005**: The auto-approval rationale (which criteria passed, which failed) is visible in the PR comment for every dependabot PR, enabling maintainers to understand the decision.
- **SC-006**: Major version bumps are never auto-approved, maintaining the existing safety gate for breaking changes.
- **SC-007**: The dependency information extraction step completes successfully (zero exit code) on every dependabot PR, including PRs that change composite action files, Go modules, Python packages, and other ecosystems.
- **SC-008**: Downstream jobs (PR comment, auto-approval decision) execute on every dependabot PR, even when individual extraction methods fail.

## Assumptions

- The existing dependency review mechanism continues to provide reliable vulnerability and security assessments and its pass/fail output is trusted for auto-approval gating.
- Release date information is available via package registry APIs for the majority of dependency ecosystems encountered in org repositories.
- CI test workflows are configured and run on dependabot PRs in all org repositories where this workflow is synced.
- The 24-hour release age threshold is sufficient as a cooling-off period; this value may be adjusted in the future based on operational experience.
- The existing semantic version risk classification (patch/minor/major) remains unchanged and continues to be used for the auto-approval gate.
- This workflow change will be synced to all org repositories via the existing `sync-config.yml` mechanism, so changes to the reusable workflows automatically propagate downstream.
- Dependabot commit messages typically contain structured metadata (`updated-dependencies` block with `dependency-name`, `dependency-version`, `update-type`) in the commit body, but this is not guaranteed for all dependency ecosystems or configurations. The extraction step must handle its absence gracefully.
- For PRs that update multiple dependencies (grouped updates), the extraction processes the first dependency found; the risk level and release age checks apply to the highest-risk dependency in the group.
- GitHub Actions workflow logic lacks a standard unit test framework. Validation relies on YAML linting (`make lint`) and manual workflow runs on dependabot PRs. This is pre-existing across all org-infra workflows and is not introduced by this feature.
