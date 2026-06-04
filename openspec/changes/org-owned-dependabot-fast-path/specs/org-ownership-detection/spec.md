## ADDED Requirements

### Requirement: Detect org-owned dependencies

The Dependabot reviewer workflow SHALL determine whether a dependency
originates from the same GitHub organization as the repository consuming it.
The check SHALL compare the first path segment of the dependency name against
the consuming repository's owner. The result SHALL be exposed as a workflow
output for downstream decision logic.

#### Scenario: Reusable workflow dependency from the same org

- **WHEN** the dependency name is
  `complytime/org-infra/.github/workflows/reusable_security.yml` and the
  consuming repository owner is `complytime`
- **THEN** the dependency SHALL be classified as org-owned

#### Scenario: Standard action from the same org

- **WHEN** the dependency name is `complytime/some-action` and the consuming
  repository owner is `complytime`
- **THEN** the dependency SHALL be classified as org-owned

#### Scenario: Third-party dependency

- **WHEN** the dependency name is `actions/checkout` and the consuming
  repository owner is `complytime`
- **THEN** the dependency SHALL NOT be classified as org-owned

#### Scenario: Dependency with no recognizable owner segment

- **WHEN** the dependency name cannot be split into an owner segment (e.g.,
  a bare package name from a non-GitHub ecosystem)
- **THEN** the dependency SHALL NOT be classified as org-owned

### Requirement: No configuration for ownership detection

The ownership detection mechanism SHALL NOT require any workflow inputs,
environment variables, or allowlists to function. It SHALL rely solely on
runtime context available in every workflow run.

#### Scenario: Reusable workflow called without extra inputs

- **WHEN** the Dependabot reviewer workflow is called by a consumer workflow
  that provides no ownership-related inputs
- **THEN** ownership detection SHALL still produce a correct result based on
  the runtime context

### Requirement: Ownership output available to callers

The Dependabot reviewer workflow SHALL expose the ownership classification as
a named output that can be consumed by downstream jobs in the calling workflow.

#### Scenario: Consumer workflow reads ownership output

- **WHEN** the Dependabot reviewer workflow completes
- **THEN** the calling workflow SHALL be able to read the ownership
  classification output and use it in conditional logic
