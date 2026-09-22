## ADDED Requirements

### Requirement: Commit body version extraction fallback

The version extraction pipeline SHALL scan the full commit body for version
numbers when the commit subject yields fewer than two semver matches. The system
SHALL extract versions from patterns matching `from <version> to <version>` in
the commit body text.

#### Scenario: Grouped Dependabot PR with versions in commit body only

- **WHEN** a grouped Dependabot commit has a subject without version numbers
  (e.g., `bump lxml in the pip group across 1 directory`) and the commit body
  contains `Updates lxml from 6.0.0 to 6.1.0`
- **THEN** the extraction step SHALL populate `from_version` as `6.0.0` and
  `to_version` as `6.1.0`

#### Scenario: Non-grouped Dependabot PR with versions in subject

- **WHEN** a non-grouped Dependabot commit has version numbers in the subject
  (e.g., `bump lxml from 6.0.0 to 6.1.0`)
- **THEN** the commit body fallback SHALL NOT be used and the versions SHALL be
  extracted from the subject as before

#### Scenario: No versions in subject or body

- **WHEN** neither the commit subject nor the commit body contain recognizable
  semver version numbers
- **THEN** the extraction step SHALL proceed to the next fallback source without
  error

### Requirement: PR title version extraction fallback

The version extraction pipeline SHALL use the pull request title as a final
fallback source for version numbers when neither the commit subject nor the
commit body yield at least two semver matches.

#### Scenario: Versions available only in PR title

- **WHEN** the commit subject and body do not contain semver version numbers and
  the PR title contains `from 6.0.0 to 6.1.0`
- **THEN** the extraction step SHALL populate `from_version` as `6.0.0` and
  `to_version` as `6.1.0` from the PR title

#### Scenario: PR title unavailable

- **WHEN** the PR title is empty or not available in the event context
- **THEN** the extraction step SHALL continue without error and leave version
  fields unpopulated if no prior source provided them

### Requirement: Derived update type from extracted versions

The extraction step SHALL compute `update_type` from `from_version` and
`to_version` when the commit metadata does not include an `update-type` field.
The computation SHALL compare major, minor, and patch components to classify the
update as `semver-patch`, `semver-minor`, or `semver-major`.

#### Scenario: Grouped PR with no update-type metadata

- **WHEN** a Dependabot commit metadata block omits the `update-type` field and
  `from_version` is `6.0.0` and `to_version` is `6.1.0`
- **THEN** the extraction step SHALL derive `update_type` as
  `version-update:semver-minor`

#### Scenario: Non-grouped PR with update-type in metadata

- **WHEN** a Dependabot commit metadata block includes
  `update-type: version-update:semver-patch`
- **THEN** the extraction step SHALL use the metadata value and SHALL NOT
  override it with a derived value

#### Scenario: No versions available for derivation

- **WHEN** both `from_version` and `to_version` are empty or unknown
- **THEN** the extraction step SHALL leave `update_type` empty and downstream
  classification SHALL default to high risk

### Requirement: Risk classification with derived data

The risk classification step SHALL produce correct risk levels for grouped
Dependabot PRs by using either the metadata `update-type` or the derived
`update_type` from the extraction step, falling back to semver comparison of
`from_version` and `to_version`.

#### Scenario: Minor update correctly classified from derived data

- **WHEN** a grouped Dependabot PR updates a dependency from `6.0.0` to `6.1.0`
  and the commit metadata omits `update-type`
- **THEN** the risk classification SHALL be `medium` (not `high`)

#### Scenario: Patch update correctly classified from derived data

- **WHEN** a grouped Dependabot PR updates a dependency from `6.0.0` to `6.0.1`
  and the commit metadata omits `update-type`
- **THEN** the risk classification SHALL be `low`

#### Scenario: Major update correctly classified from derived data

- **WHEN** a grouped Dependabot PR updates a dependency from `5.2.0` to `6.0.0`
  and the commit metadata omits `update-type`
- **THEN** the risk classification SHALL be `high`
