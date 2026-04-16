## ADDED Requirements

### Requirement: Common Dependabot entries applied to all repos

The sync system SHALL define a set of common Dependabot ecosystem entries in the
sync configuration. These common entries SHALL be included in the generated
`dependabot.yml` for every target repository unless the repository is in the
Dependabot exclude list.

#### Scenario: Repo with no overrides receives common entries

- **WHEN** the sync runs for a repository that has no per-repo overrides
- **THEN** the generated `dependabot.yml` contains exactly the common entries

#### Scenario: Excluded repo receives no Dependabot config

- **WHEN** the sync runs for a repository listed in the Dependabot exclude list
- **THEN** no `dependabot.yml` is generated or modified for that repository

### Requirement: Per-repo Dependabot overrides

The sync system SHALL support per-repo override entries in the sync configuration.
An override entry for a given `package-ecosystem` SHALL replace the common entry
for that same ecosystem entirely.

#### Scenario: Override replaces common entry for same ecosystem

- **WHEN** a repo has an override for `github-actions` and the common set also
  defines a `github-actions` entry
- **THEN** the generated file uses the override version, not the common version

#### Scenario: Override adds ecosystem not in common

- **WHEN** a repo has an override for `gomod` and the common set does not define
  a `gomod` entry
- **THEN** the generated file includes both the common entries and the `gomod`
  override

### Requirement: Unmanaged ecosystem entries preserved

The sync system SHALL preserve any Dependabot ecosystem entries in the target
repository's existing `dependabot.yml` that are not managed by org-infra. An entry
is considered unmanaged if its `package-ecosystem` value does not appear in the
managed set (common entries merged with overrides).

#### Scenario: Repo has unmanaged ecosystem entry

- **WHEN** the target repo's existing `dependabot.yml` contains an entry for
  `docker` and org-infra does not manage the `docker` ecosystem for that repo
- **THEN** the `docker` entry is preserved in the generated file

#### Scenario: Repo has no existing dependabot.yml

- **WHEN** the target repo has no `.github/dependabot.yml`
- **THEN** the generated file contains only the managed entries (common + overrides)

#### Scenario: Managed entry replaces existing entry

- **WHEN** the target repo has an existing `gomod` entry and org-infra manages
  `gomod` for that repo via an override
- **THEN** the existing `gomod` entry is replaced by the org-infra version

### Requirement: Generated file structure

The generated `dependabot.yml` SHALL be a valid Dependabot v2 configuration file.
It SHALL include the `version: 2` header, followed by managed entries, followed by
any preserved unmanaged entries.

#### Scenario: Valid output structure

- **WHEN** the sync generates a `dependabot.yml` for any target repo
- **THEN** the file starts with `version: 2` and contains an `updates` list with
  all applicable entries

### Requirement: No-op when config unchanged

The sync system SHALL compare the generated `dependabot.yml` against the existing
file in the target repository. If the content is identical, the file SHALL NOT be
included in the sync changeset.

#### Scenario: Config already up to date

- **WHEN** the generated `dependabot.yml` is identical to the existing file
- **THEN** the file is not marked as changed and is not included in the commit
