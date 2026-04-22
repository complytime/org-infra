## ADDED Requirements

### Requirement: Per-file variable declaration

The sync configuration file SHALL support an optional `vars` key on each file entry.
Each var SHALL have a `default` value and an optional `repos` map of per-repo overrides.

#### Scenario: File entry with vars defined
- **WHEN** a file entry in the sync config includes a `vars` key with one or more variable
  definitions
- **THEN** each variable MUST have a `default` value and MAY have a `repos` map

#### Scenario: File entry without vars
- **WHEN** a file entry in the sync config does not include a `vars` key
- **THEN** the file MUST be synced verbatim (existing behavior, unchanged)

### Requirement: Variable resolution per repository

The sync process SHALL resolve each variable's value for a given target repository by checking
the `repos` map first, then falling back to the `default` value.

#### Scenario: Repository listed in repos map
- **WHEN** the target repository name exists as a key in the variable's `repos` map
- **THEN** the resolved value MUST be the value from the `repos` map for that repository

#### Scenario: Repository not listed in repos map
- **WHEN** the target repository name does not exist in the variable's `repos` map
- **THEN** the resolved value MUST be the variable's `default` value

### Requirement: Text substitution in file content

The sync process SHALL substitute each declared variable's value in the file content using
text-based replacement that preserves all other file content (comments, formatting, whitespace).

#### Scenario: Variable found in source content
- **WHEN** the source file contains a key matching the variable name followed by a value
- **THEN** the value portion MUST be replaced with the resolved value for the target repository
- **AND** all other file content (comments, indentation, SHA references) MUST be preserved

#### Scenario: Variable not found in source content
- **WHEN** the source file does not contain a key matching the variable name
- **THEN** the sync process MUST log a warning indicating the variable was not found
- **AND** the file MUST still be synced with remaining substitutions applied

### Requirement: File comparison uses resolved content

The sync process SHALL compare the resolved content (after variable substitution) against the
destination file to determine whether an update is needed.

#### Scenario: Resolved content matches destination
- **WHEN** the resolved content is identical to the existing destination file
- **THEN** the file MUST be reported as up to date
- **AND** no changes MUST be staged for that file

#### Scenario: Resolved content differs from destination
- **WHEN** the resolved content differs from the existing destination file
- **THEN** the file MUST be reported as needing update
- **AND** the resolved content MUST be written to the destination

### Requirement: Dry-run shows resolved values

The dry-run mode SHALL display the resolved variable values for each file and repository so
operators can verify the configuration before applying.

#### Scenario: Dry-run with vars configured
- **WHEN** the sync process runs in dry-run mode for a file with vars
- **THEN** the output MUST indicate which variables were resolved and to what values
- **AND** no files MUST be modified on disk
