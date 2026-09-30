## ADDED Requirements

### Requirement: Outdated action versions SHOULD produce warnings

When pinact detects that a SHA-pinned action is not at the latest available
version, a warning annotation SHOULD be emitted on the PR without failing CI.

#### Scenario: Action at latest version

- **GIVEN** a workflow file containing `uses: actions/checkout@<SHA> # v7.0.1`
- **WHEN** `v7.0.1` is the latest release of `actions/checkout`
- **THEN** the freshness check SHALL produce no warning for this action

#### Scenario: Action at outdated version

- **GIVEN** a workflow file containing `uses: actions/checkout@<SHA> # v3.5.1`
- **WHEN** `v7.0.1` is the latest release of `actions/checkout`
- **THEN** the freshness check SHALL emit a `::warning` annotation identifying the outdated action
- **AND** the CI job SHALL NOT fail

#### Scenario: Freshness check failure does not block CI

- **GIVEN** the freshness check step encounters an error (API failure, timeout)
- **WHEN** the step completes
- **THEN** the CI job SHALL NOT fail (the step uses `continue-on-error: true`)

### Requirement: Minimum release age MUST be enforced

Actions SHALL NOT be pinned to versions released fewer than 3 days ago. This
provides a supply chain cooldown window against compromised newly-published
releases.

#### Scenario: Action version released more than 3 days ago

- **GIVEN** a workflow file pinned to a version released 5 days ago
- **WHEN** pinact processes the file with `--min-age 3`
- **THEN** the minimum age check SHALL pass

#### Scenario: Action version released less than 3 days ago

- **GIVEN** a workflow file pinned to a version released 1 day ago
- **WHEN** pinact processes the file with `--min-age 3`
- **THEN** pinact SHALL report a minimum age violation (exit code 2)
- **AND** the CI job SHALL fail
