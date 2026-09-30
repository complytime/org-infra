## ADDED Requirements

### Requirement: SHA-pinned actions MUST have verified version comments

When pinact runs in verify mode, every `uses:` clause pinned to a full
40-character commit SHA MUST have a trailing version comment (`# vX.Y.Z`)
that matches the actual tag the SHA resolves to in the upstream repository.

#### Scenario: Valid SHA with correct version comment

- **GIVEN** a workflow file containing `uses: actions/checkout@<SHA> # v7.0.1`
- **WHEN** the SHA resolves to tag `v7.0.1` in the `actions/checkout` repository
- **THEN** pinact SHALL report no error for this action reference

#### Scenario: Valid SHA with incorrect version comment

- **GIVEN** a workflow file containing `uses: actions/checkout@<SHA> # v7.0.1`
- **WHEN** the SHA actually resolves to tag `v3.5.1` in the `actions/checkout` repository
- **THEN** pinact SHALL report a verification error (exit code 2)
- **AND** the CI job SHALL fail

#### Scenario: Non-existent SHA (hallucinated)

- **GIVEN** a workflow file containing `uses: actions/checkout@<fabricated-SHA> # v7.0.1`
- **WHEN** the SHA does not exist in the `actions/checkout` repository or its fork network
- **THEN** pinact SHALL report a GitHub API error (exit code 3)
- **AND** the CI job SHALL fail

#### Scenario: SHA-pinned action without version comment

- **GIVEN** a workflow file containing `uses: actions/checkout@<SHA>` with no trailing comment
- **WHEN** pinact processes the file
- **THEN** pinact SHALL report a missing version comment error (exit code 2)
- **AND** the CI job SHALL fail

### Requirement: Unpinned action references MUST be detected

Actions using mutable tag references (e.g., `@v4`, `@main`) without a full
40-character SHA MUST be flagged as needing pinning.

#### Scenario: Action using mutable tag

- **GIVEN** a workflow file containing `uses: actions/checkout@v4`
- **WHEN** pinact processes the file in check mode
- **THEN** pinact SHALL report the action as needing pinning (exit code 1)
- **AND** the CI job SHALL fail

#### Scenario: Local and Docker actions are skipped

- **GIVEN** a workflow file containing `uses: ./local-action` or `uses: docker://image:tag`
- **WHEN** pinact processes the file
- **THEN** pinact SHALL skip these references without error
