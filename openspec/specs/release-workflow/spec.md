## ADDED Requirements

### Requirement: Manual release trigger with semver tag
The release workflow SHALL be triggered via `workflow_dispatch` with a required `tag` input
that specifies the semver version to release.

#### Scenario: Valid semver tag provided
- **WHEN** a maintainer triggers the release workflow with tag `v1.0.0`
- **THEN** the workflow proceeds to tag creation and release publishing

#### Scenario: Release candidate tag provided
- **WHEN** a maintainer triggers the release workflow with tag `v1.0.0-rc.1`
- **THEN** the workflow proceeds and the release is marked as a prerelease

---

### Requirement: Tag format validation
The release workflow SHALL validate that the provided tag matches semver format
(`v<major>.<minor>.<patch>` or `v<major>.<minor>.<patch>-rc.<n>`) and reject invalid tags.

#### Scenario: Invalid tag rejected
- **WHEN** a maintainer triggers the release workflow with tag `1.0.0` (missing `v` prefix)
- **THEN** the workflow fails with an error message explaining the required format

#### Scenario: Partial version rejected
- **WHEN** a maintainer triggers the release workflow with tag `v1.0` (missing patch component)
- **THEN** the workflow fails with an error message explaining the required format

---

### Requirement: Release restricted to default branch
The release workflow SHALL reject triggers from any branch other than `main` to prevent
tagging untested code from feature branches.

#### Scenario: Release from main branch
- **WHEN** the release workflow is triggered from `refs/heads/main`
- **THEN** the workflow proceeds normally

#### Scenario: Release from feature branch rejected
- **WHEN** the release workflow is triggered from a feature branch (e.g., `refs/heads/feat/foo`)
- **THEN** the workflow fails with an error stating releases MUST be created from main

---

### Requirement: Dynamic prerelease detection
The release workflow SHALL mark releases as prerelease only when the tag contains a release
candidate suffix (`-rc.<n>`). Stable tags SHALL NOT be marked as prerelease.

#### Scenario: Stable release not marked prerelease
- **WHEN** the tag is `v1.0.0` (no RC suffix)
- **THEN** the published GitHub Release is NOT marked as a prerelease

#### Scenario: RC release marked prerelease
- **WHEN** the tag is `v1.0.0-rc.1`
- **THEN** the published GitHub Release IS marked as a prerelease

---

### Requirement: Conditional tag creation
The release workflow SHALL create and push the tag on the current branch HEAD if the tag does
not already exist. If the tag already exists, the step SHALL be skipped.

#### Scenario: Tag does not exist
- **WHEN** the provided tag does not exist in the repository
- **THEN** the workflow creates the tag on the current HEAD and pushes it to origin

#### Scenario: Tag already exists
- **WHEN** the provided tag already exists in the repository
- **THEN** the tag creation step is skipped and the existing tag is used

---

### Requirement: Publish GitHub Release with auto-generated changelog
The release workflow SHALL publish a GitHub Release using release-drafter with a changelog
auto-generated from merged PRs since the previous release tag, categorized by PR labels.

#### Scenario: Release published with categorized changelog
- **WHEN** the release workflow completes successfully
- **THEN** a GitHub Release exists for the specified tag
- **AND** the release body contains PRs grouped by category (workflows, features, fixes, etc.)

#### Scenario: No PRs since last release
- **WHEN** no PRs have been merged since the previous release tag
- **THEN** the release body contains a "no changes" message

---

### Requirement: Auto-label PRs from conventional commits and file paths
The release-drafter configuration SHALL map conventional commit prefixes in PR titles and
changed file paths to changelog labels automatically.

#### Scenario: Conventional commit prefix mapped
- **WHEN** a PR title starts with `feat:`
- **THEN** the PR is labeled `feature` and appears in the Features changelog section

#### Scenario: File path mapped
- **WHEN** a PR changes files in `.github/workflows/`
- **THEN** the PR is labeled `workflows` and appears in the Workflows changelog section

---

### Requirement: Version resolution from PR labels
The release-drafter configuration SHALL resolve the next version number from PR labels,
using major/minor/patch bumps as appropriate, defaulting to patch.

#### Scenario: Feature PR bumps minor version
- **WHEN** the highest-priority label among merged PRs is `feature`
- **THEN** the resolved version increments the minor component

#### Scenario: No matching labels default to patch
- **WHEN** no PRs have major, minor, or patch-mapped labels
- **THEN** the resolved version increments the patch component

---

### Requirement: Exclude bot contributions from changelog
The release-drafter configuration SHALL exclude PRs authored by `dependabot[bot]` and
`github-actions[bot]` from the changelog.

#### Scenario: Dependabot PR excluded
- **WHEN** a dependabot PR is merged between releases
- **THEN** it does not appear in the release changelog

---

### Requirement: Dry-run release notes preview
A separate preview workflow SHALL generate release notes without creating a release, outputting
the result to the job summary and as a downloadable artifact.

#### Scenario: Preview without side effects
- **WHEN** a maintainer runs the release notes preview workflow
- **THEN** the draft changelog is displayed in the job summary
- **AND** a `release-notes-preview.md` artifact is uploaded
- **AND** no GitHub Release or tag is created

---

### Requirement: Least-privilege permissions
The release workflow SHALL declare empty permissions at the workflow level and grant only
`contents: write` at the job level. The preview workflow SHALL use read-only permissions.

#### Scenario: Release workflow permissions
- **WHEN** the release workflow file is parsed
- **THEN** workflow-level `permissions` is `{}`
- **AND** job-level permissions grant only `contents: write`

#### Scenario: Preview workflow permissions
- **WHEN** the preview workflow file is parsed
- **THEN** permissions grant only `contents: read` and `pull-requests: read`

---

### Requirement: User inputs routed through env blocks
All workflow `run:` steps that reference user-controlled inputs SHALL use `env:` block
indirection rather than direct `${{ }}` expression interpolation to prevent command injection.

#### Scenario: Tag input in run block
- **WHEN** a `run:` step references the `tag` input
- **THEN** the value is accessed via an environment variable set in the step's `env:` block
- **AND** no `${{ inputs.tag }}` expression appears inside the `run:` script body

---

### Requirement: All action references pinned to full commit SHAs
All workflow files SHALL pin every `uses:` action reference to a full 40-character commit SHA
with an inline version comment.

#### Scenario: SHA-pinned action references
- **WHEN** the workflow files are linted with the org's SHA-pin checker
- **THEN** no action reference uses a mutable tag or branch ref
