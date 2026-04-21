## ADDED Requirements

### Requirement: Reusable workflow references use immutable SHA pins

All `uses:` references to org-infra reusable workflows SHALL be pinned to a full
40-character commit SHA corresponding to a tagged release. This applies to both consumer
workflows and reusable-to-reusable calls within org-infra.

#### Scenario: Consumer workflow references a reusable workflow

- **WHEN** a consumer workflow (`ci_*`) calls a reusable workflow from org-infra
- **THEN** the `uses:` value SHALL contain a full 40-character commit SHA (not a branch name, short SHA, or mutable tag)

#### Scenario: Reusable workflow references another reusable workflow

- **WHEN** a reusable workflow calls another reusable workflow from org-infra
- **THEN** the `uses:` value SHALL contain a full 40-character commit SHA (not a branch name, short SHA, or mutable tag)

### Requirement: SHA pins include version comment

Each SHA-pinned reusable workflow reference SHALL include an inline comment identifying
the corresponding release version for human readability.

#### Scenario: Version comment format

- **WHEN** a workflow file contains a SHA-pinned reusable workflow reference
- **THEN** the line SHALL include a trailing comment in the format `# v<major>.<minor>.<patch>`

### Requirement: No mutable references to org-infra reusable workflows

No `uses:` reference to an org-infra reusable workflow SHALL use a mutable ref such as
a branch name or tag. This convention SHALL be maintained across all releases.

#### Scenario: No mutable references in any workflow file

- **WHEN** a reviewer inspects all workflow files in `.github/workflows/`
- **THEN** zero `uses:` lines referencing `complytime/org-infra` SHALL contain `@main`, `@master`, or any other branch name

#### Scenario: New release requires SHA update

- **WHEN** a new org-infra release is tagged
- **THEN** consumer workflows SHALL be updated to reference the new release's commit SHA before the next org sync

### Requirement: SHA pins are updated as part of the release process

Updating reusable workflow SHA pins SHALL be a required step in the org-infra release
process. The pins SHALL always reference the most recent tagged release.

#### Scenario: Release checklist includes pin update

- **WHEN** a maintainer cuts a new org-infra release
- **THEN** all reusable workflow SHA pins and version comments SHALL be updated to the new release's commit SHA and version before syncing to downstream repos
