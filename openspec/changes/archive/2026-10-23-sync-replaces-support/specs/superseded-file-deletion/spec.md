## ADDED Requirements

### Requirement: Delete superseded files during sync
When processing a `files_to_sync` entry with a `replaces` key, the sync script SHALL delete each listed file from the downstream repository clone if the file exists.

#### Scenario: Superseded file exists in downstream repo
- **WHEN** a `replaces` path refers to a file that exists in the downstream repository clone
- **THEN** the sync script SHALL delete the file from the working tree and stage the deletion for commit

#### Scenario: Superseded file does not exist in downstream repo
- **WHEN** a `replaces` path refers to a file that does not exist in the downstream repository clone
- **THEN** the sync script SHALL skip the deletion silently without error

#### Scenario: Deletion included in sync commit
- **WHEN** one or more superseded files are deleted during the sync operation
- **THEN** the deletions SHALL be included in the same commit as the replacement file additions and updates

#### Scenario: Superseded file is a symlink
- **WHEN** a `replaces` path resolves to a symlink in the downstream repository
- **THEN** the sync script SHALL remove the symlink itself without following it

#### Scenario: Replaces path is a directory
- **WHEN** a `replaces` path refers to a directory in the downstream repository clone
- **THEN** the sync script SHALL skip the entry without error and SHALL NOT attempt recursive deletion

#### Scenario: Replaces path matches the destination path
- **WHEN** a `replaces` entry contains a path identical to the `destination` of the same `files_to_sync` entry
- **THEN** the sync script SHALL skip the deletion for that path

#### Scenario: Repeated sync with replaces (idempotency)
- **WHEN** the sync script runs against a repo where superseded files were already deleted in a previous sync
- **THEN** the script SHALL skip the already-deleted files silently and not produce errors or duplicate entries in reporting

### Requirement: Replacement skipped for excluded repos
When a `files_to_sync` entry is excluded for a repository via `exclude_repos`, the `replaces` entries for that file SHALL also be skipped.

#### Scenario: Entry excluded for repo
- **WHEN** a `files_to_sync` entry has both `exclude_repos` containing the current repository and a `replaces` key
- **THEN** the sync script SHALL not process the `replaces` entries for that repository

### Requirement: Dry run reports planned deletions
In dry-run mode, the sync script SHALL report which superseded files would be deleted without performing any actual deletions.

#### Scenario: Dry run with existing superseded file
- **WHEN** the sync script runs in dry-run mode and a `replaces` path refers to an existing file
- **THEN** the script SHALL print a message indicating the file would be removed as a replacement

#### Scenario: Dry run with non-existent superseded file
- **WHEN** the sync script runs in dry-run mode and a `replaces` path refers to a file that does not exist
- **THEN** the script SHALL skip the file without printing a removal message
