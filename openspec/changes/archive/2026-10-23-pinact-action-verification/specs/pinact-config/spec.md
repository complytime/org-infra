This spec defines requirements for the `.pinact.yaml` configuration file and its
org-wide distribution via the sync mechanism.

## ADDED Requirements

### Requirement: Org-wide pinact configuration synced to all repositories

A `.pinact.yaml` configuration file SHALL be maintained in org-infra and synced
to all downstream repositories via `sync-config.yml`, providing consistent
defaults for minimum release age and exclusion rules.

#### Scenario: Configuration defines minimum release age

- **GIVEN** `.pinact.yaml` contains `min_age: { value: 3 }`
- **WHEN** pinact runs in any org repository
- **THEN** the 3-day minimum release age SHALL be enforced

#### Scenario: Repository without local override

- **GIVEN** a downstream repository receives `.pinact.yaml` via sync
- **AND** the repository does not have a local override
- **WHEN** pinact runs
- **THEN** the org-wide defaults SHALL apply

#### Scenario: Repository with local override

- **GIVEN** a downstream repository requires different pinact settings
- **WHEN** the repository is added to the `exclude_repos` list for the `.pinact.yaml` sync entry in `sync-config.yml`
- **AND** the repository maintains a local `.pinact.yaml` with its own settings
- **THEN** the local configuration SHALL take precedence because the sync mechanism will not overwrite it

> **Note**: The sync mechanism copies files unconditionally. Repositories that need
> local overrides MUST be added to `exclude_repos` for the `.pinact.yaml` entry in
> `sync-config.yml` to prevent their local configuration from being overwritten on
> each sync run.

## MODIFIED Requirements

### Requirement: sync-config.yml extended with pinact configuration

The `files_to_sync` list in `sync-config.yml` SHALL include an entry for
`.pinact.yaml` to ensure org-wide distribution.

Previously: `.pinact.yaml` did not exist in the sync configuration.

#### Scenario: Pinact config synced to downstream repo

- **GIVEN** `.pinact.yaml` is listed in `files_to_sync` in `sync-config.yml`
- **WHEN** the sync script processes a downstream repository
- **THEN** `.pinact.yaml` SHALL be copied to the downstream repository root
