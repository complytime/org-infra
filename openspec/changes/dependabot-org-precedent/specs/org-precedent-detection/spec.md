# Spec Delta

## Purpose

Detects whether a Dependabot dependency update was already merged with human
approval in another repository within the same GitHub organization, providing
a cross-repo trust signal for the approval pipeline.

## ADDED Requirements

### Requirement: Cross-repo precedent search

The Dependabot reviewer pipeline SHALL search for merged Dependabot PRs across
the same GitHub organization that update the same dependency to the same
version as the current PR. The search SHALL exclude the current repository
from results.

#### Scenario: Matching merged PR exists in another org repo

- **WHEN** a Dependabot PR proposes updating dependency `actions/checkout` to
  version `7.0.1` in repository `complytime/complyctl` and repository
  `complytime/org-infra` has a merged Dependabot PR for `actions/checkout`
  version `7.0.1`
- **THEN** the search SHALL return the merged PR from `complytime/org-infra`
  as a candidate

#### Scenario: No matching merged PR in the org

- **WHEN** a Dependabot PR proposes updating dependency `actions/checkout` to
  version `7.0.1` and no other org repository has a merged Dependabot PR for
  that dependency at that version
- **THEN** the search SHALL return no candidates and `org_precedent` SHALL be
  `"false"`

#### Scenario: Matching PR exists only in the current repo

- **WHEN** the only merged PR for the dependency at the target version is in
  the same repository as the current PR
- **THEN** the search SHALL exclude that result and `org_precedent` SHALL be
  `"false"`

#### Scenario: Multiple matching PRs across org repos

- **WHEN** multiple org repositories have merged Dependabot PRs for the same
  dependency at the same version
- **THEN** the search SHALL use the first candidate with a verified human
  approval and stop

### Requirement: Human approval verification

The pipeline SHALL verify that at least one candidate merged PR received an
approval review from a human reviewer. Approvals from automated accounts
(bot users) SHALL NOT satisfy the human approval requirement.

#### Scenario: Merged PR with human approval

- **WHEN** a candidate merged PR has an approval review from a user whose
  account type is not "Bot"
- **THEN** the precedent check SHALL classify this as a valid precedent and
  output the reviewer identity

#### Scenario: Merged PR with only bot approval

- **WHEN** a candidate merged PR has approval reviews exclusively from bot
  accounts (e.g., the workflow's own auto-approve step)
- **THEN** the precedent check SHALL NOT classify this as a valid precedent

#### Scenario: Merged PR with no approval reviews

- **WHEN** a candidate merged PR was merged without any approval reviews
  (e.g., admin merge bypass)
- **THEN** the precedent check SHALL NOT classify this as a valid precedent

### Requirement: Precedent output

The Dependabot reviewer pipeline SHALL expose the precedent result as
workflow outputs consumable by downstream jobs in the calling workflow.

#### Scenario: Precedent found

- **WHEN** a valid precedent is detected (merged PR with human approval in
  another org repo)
- **THEN** the pipeline SHALL output `org_precedent` as `"true"` and
  `precedent_detail` as a human-readable string identifying the repository,
  PR number, and reviewer (e.g., `"Reviewed by @username in org/repo#123"`)

#### Scenario: No precedent found

- **WHEN** no valid precedent is detected
- **THEN** the pipeline SHALL output `org_precedent` as `"false"` and
  `precedent_detail` as an empty string

### Requirement: Graceful degradation on search failure

The precedent search SHALL fail gracefully when the search API is
unavailable, rate-limited, or returns an error. A search failure SHALL
never block or degrade the existing approval pipeline.

#### Scenario: Search API rate limit exceeded

- **WHEN** the search API returns a rate limit error during the precedent
  lookup
- **THEN** the pipeline SHALL set `org_precedent` to `"false"` and continue
  with the existing approval logic

#### Scenario: Search API timeout

- **WHEN** the search API call exceeds the configured timeout
- **THEN** the pipeline SHALL set `org_precedent` to `"false"` and continue
  without error

#### Scenario: Empty dependency name or version

- **WHEN** the dependency name or version is empty or could not be extracted
  from the PR
- **THEN** the pipeline SHALL skip the precedent search and set
  `org_precedent` to `"false"`

#### Scenario: Reviews API failure for a candidate PR

- **WHEN** the search returns candidate PRs but the Reviews API call for a
  candidate returns an error or timeout
- **THEN** the pipeline SHALL skip that candidate and evaluate the next
  candidate. If all candidates fail verification, the pipeline SHALL set
  `org_precedent` to `"false"` and continue without error

### Requirement: No additional secrets or configuration

The precedent search SHALL operate using the workflow token already available
in the runner environment. It SHALL NOT require additional secrets, workflow
inputs, or configuration files.

#### Scenario: Workflow called without extra inputs

- **WHEN** the Dependabot reviewer workflow is called by a consumer workflow
  that provides no precedent-related inputs
- **THEN** the precedent search SHALL function correctly using the existing
  runner context and token
