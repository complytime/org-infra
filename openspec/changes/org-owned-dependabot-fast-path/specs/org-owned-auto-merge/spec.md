## ADDED Requirements

### Requirement: Auto-approve org-owned patch/minor without release age gate

The approval pipeline SHALL auto-approve Dependabot PRs for org-owned
dependencies when the update is a patch or minor version bump and the
dependency review passes, without requiring a minimum release age.

#### Scenario: Org-owned minor bump with passing review

- **WHEN** a Dependabot PR bumps an org-owned dependency with a minor version
  update and the dependency review concludes with success
- **THEN** the PR SHALL be auto-approved regardless of the release age

#### Scenario: Org-owned patch bump with passing review

- **WHEN** a Dependabot PR bumps an org-owned dependency with a patch version
  update and the dependency review concludes with success
- **THEN** the PR SHALL be auto-approved regardless of the release age

#### Scenario: Org-owned major bump

- **WHEN** a Dependabot PR bumps an org-owned dependency with a major version
  update
- **THEN** the PR SHALL NOT be auto-approved, regardless of review outcome

#### Scenario: Org-owned bump with failing review

- **WHEN** a Dependabot PR bumps an org-owned dependency but the dependency
  review concludes with failure
- **THEN** the PR SHALL NOT be auto-approved

### Requirement: Third-party approval unchanged

The approval pipeline SHALL continue to apply the existing approval conditions
for third-party (non-org-owned) dependencies: risk not high, dependency review
passes, release age known, and release age at least 24 hours.

#### Scenario: Third-party patch bump with sufficient age

- **WHEN** a Dependabot PR bumps a third-party dependency with a patch update,
  the dependency review passes, and the release is at least 24 hours old
- **THEN** the PR SHALL be auto-approved (existing behavior preserved)

#### Scenario: Third-party bump with unknown release age

- **WHEN** a Dependabot PR bumps a third-party dependency and the release age
  cannot be determined
- **THEN** the PR SHALL NOT be auto-approved (existing behavior preserved)

### Requirement: Enable auto-merge for org-owned approvals

After auto-approving an org-owned Dependabot PR, the pipeline SHALL enable
GitHub auto-merge on the PR. Auto-merge SHALL respect all branch protection
rules configured on the target repository.

#### Scenario: Auto-merge enabled after org-owned approval

- **WHEN** an org-owned Dependabot PR is auto-approved
- **THEN** GitHub auto-merge SHALL be enabled on the PR

#### Scenario: Repo with single required approval

- **WHEN** auto-merge is enabled on an org-owned Dependabot PR and the
  repository requires one approval and all status checks pass
- **THEN** the PR SHALL merge automatically without further human intervention

#### Scenario: Repo with two required approvals

- **WHEN** auto-merge is enabled on an org-owned Dependabot PR and the
  repository requires two approvals
- **THEN** the PR SHALL merge automatically after one human provides the
  second approval and all status checks pass

#### Scenario: Auto-merge unavailable in repo settings

- **WHEN** auto-merge is enabled but the repository does not have "Allow
  auto-merge" turned on in its settings
- **THEN** the auto-merge step SHALL fail gracefully without affecting the
  approval, and the PR comment SHALL indicate that auto-merge is unavailable

### Requirement: PR comment reflects ownership and auto-merge status

The PR comment posted by the pipeline SHALL include the ownership
classification and the auto-merge status to give maintainers full visibility
into the automated decision.

#### Scenario: Org-owned dependency auto-approved with auto-merge

- **WHEN** an org-owned Dependabot PR is auto-approved and auto-merge is
  enabled
- **THEN** the PR comment SHALL indicate the dependency is org-owned, the PR
  was auto-approved, and auto-merge is enabled

#### Scenario: Third-party dependency auto-approved without auto-merge

- **WHEN** a third-party Dependabot PR is auto-approved
- **THEN** the PR comment SHALL indicate the dependency is third-party, the PR
  was auto-approved, and auto-merge is not applicable

#### Scenario: Dependency requiring manual review

- **WHEN** a Dependabot PR is not auto-approved (any reason)
- **THEN** the PR comment SHALL indicate manual review is required and display
  the reason (e.g., major update, failed review, unknown release age for
  third-party)
