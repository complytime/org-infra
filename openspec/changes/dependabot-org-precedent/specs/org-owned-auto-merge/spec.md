# Spec Delta

## ADDED Requirements

### Requirement: Auto-approve and auto-merge with org precedent

The approval pipeline SHALL auto-approve and enable auto-merge for Dependabot
PRs when all of the following conditions are met: org precedent exists, the
dependency review passes, the risk level is not high, and the release age is
at least 24 hours.

#### Scenario: Third-party patch bump with org precedent

- **WHEN** a Dependabot PR bumps a third-party dependency with a patch update,
  the dependency review passes, the release is at least 24 hours old, and the
  same dependency at the same version was merged with human approval in another
  org repo
- **THEN** the PR SHALL be auto-approved and auto-merge SHALL be enabled

#### Scenario: Third-party minor bump with org precedent

- **WHEN** a Dependabot PR bumps a third-party dependency with a minor update,
  the dependency review passes, the release is at least 24 hours old, and org
  precedent exists
- **THEN** the PR SHALL be auto-approved and auto-merge SHALL be enabled

#### Scenario: Major bump with org precedent

- **WHEN** a Dependabot PR bumps a dependency with a major update and org
  precedent exists
- **THEN** the PR SHALL NOT be auto-approved regardless of precedent (risk
  gate takes priority)

#### Scenario: Org precedent with failing dependency review

- **WHEN** a Dependabot PR has org precedent but the dependency review
  concludes with failure
- **THEN** the PR SHALL NOT be auto-approved (review gate takes priority)

#### Scenario: Org precedent with release age under 24 hours

- **WHEN** a Dependabot PR has org precedent but the release is less than
  24 hours old
- **THEN** the PR SHALL NOT be auto-approved (release age gate takes priority)

#### Scenario: No org precedent for third-party dependency

- **WHEN** a Dependabot PR bumps a third-party dependency with no org
  precedent, the dependency review passes, and the release is at least
  24 hours old
- **THEN** the PR SHALL be auto-approved but auto-merge SHALL NOT be enabled
  (existing Path A behavior preserved)

### Requirement: PR comment reflects org precedent

The PR comment posted by the pipeline SHALL include the org precedent status
to give maintainers visibility into the cross-repo trust signal used in the
automated decision.

#### Scenario: Precedent found and used for auto-merge

- **WHEN** a Dependabot PR is auto-approved with auto-merge enabled based on
  org precedent
- **THEN** the PR comment SHALL display the precedent source repository, PR
  number, and the reviewer who approved it

#### Scenario: Precedent not found

- **WHEN** no org precedent exists for the dependency update
- **THEN** the PR comment SHALL indicate that no prior merge was found in the
  organization

#### Scenario: Precedent found but other gates block approval

- **WHEN** org precedent exists but the PR is not auto-approved due to another
  gate (risk, review, release age)
- **THEN** the PR comment SHALL display the precedent information alongside
  the blocking condition

## MODIFIED Requirements

### Requirement: Third-party approval unchanged

The approval pipeline SHALL continue to apply the existing approval conditions
for third-party (non-org-owned) dependencies: risk not high, dependency review
passes, release age known, and release age at least 24 hours. When org
precedent exists and all gates pass, auto-merge SHALL additionally be enabled.

#### Scenario: Third-party patch bump with sufficient age

- **WHEN** a Dependabot PR bumps a third-party dependency with a patch update,
  the dependency review passes, and the release is at least 24 hours old
- **THEN** the PR SHALL be auto-approved (existing behavior preserved)

#### Scenario: Third-party bump with unknown release age

- **WHEN** a Dependabot PR bumps a third-party dependency and the release age
  cannot be determined
- **THEN** the PR SHALL NOT be auto-approved (existing behavior preserved)

#### Scenario: Third-party bump with org precedent and sufficient age

- **WHEN** a Dependabot PR bumps a third-party dependency with a patch update,
  the dependency review passes, the release is at least 24 hours old, and org
  precedent exists
- **THEN** the PR SHALL be auto-approved and auto-merge SHALL be enabled

### Requirement: PR comment reflects ownership and approval decision

The PR comment posted by the pipeline SHALL include the ownership
classification, the org precedent status, and the approval decision to give
maintainers full visibility into the automated decision. The comment reports
the approval *intent* based on conditions evaluated at comment time, not
post-facto auto-merge outcomes (since the comment and approval jobs execute
in parallel).

#### Scenario: Org-owned dependency auto-approved with auto-merge requested

- **WHEN** an org-owned Dependabot PR meets the auto-approval conditions
  (patch/minor, review passes)
- **THEN** the PR comment SHALL indicate the dependency is org-owned, the PR
  was auto-approved, and auto-merge was requested

#### Scenario: Third-party dependency auto-approved without auto-merge

- **WHEN** a third-party Dependabot PR meets the auto-approval conditions
  (patch/minor, review passes, release age >= 24h) and no org precedent exists
- **THEN** the PR comment SHALL indicate the dependency is third-party, the PR
  was auto-approved, and auto-merge is not applicable

#### Scenario: Third-party dependency auto-approved with precedent auto-merge

- **WHEN** a third-party Dependabot PR meets the auto-approval conditions and
  org precedent exists
- **THEN** the PR comment SHALL indicate the dependency is third-party, org
  precedent was found, the PR was auto-approved, and auto-merge was requested

#### Scenario: Dependency requiring manual review

- **WHEN** a Dependabot PR is not auto-approved (any reason)
- **THEN** the PR comment SHALL indicate manual review is required and display
  the reason (e.g., major update, failed review, unknown release age for
  third-party)
