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

- **GIVEN** a downstream repository has a local `.pinact.yaml` with different settings
- **WHEN** pinact runs
- **THEN** the local configuration SHALL take precedence over the synced default

## MODIFIED Requirements

### Requirement: sync-config.yml extended with pinact configuration

The `files_to_sync` list in `sync-config.yml` SHALL include an entry for
`.pinact.yaml` to ensure org-wide distribution.

Previously: `.pinact.yaml` did not exist in the sync configuration.

#### Scenario: Pinact config synced to downstream repo

- **GIVEN** `.pinact.yaml` is listed in `files_to_sync` in `sync-config.yml`
- **WHEN** the sync script processes a downstream repository
- **THEN** `.pinact.yaml` SHALL be copied to the downstream repository root
