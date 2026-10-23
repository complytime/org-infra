## ADDED Requirements

### Requirement: Replaces key in sync configuration
Each entry in `files_to_sync` SHALL support an optional `replaces` key containing a list of file paths relative to the downstream repository root. These paths identify files that the current entry supersedes.

#### Scenario: Entry with replaces key is parsed
- **WHEN** a `files_to_sync` entry includes a `replaces` key with one or more file paths
- **THEN** the sync script SHALL read and store those paths for processing during the sync operation

#### Scenario: Entry without replaces key
- **WHEN** a `files_to_sync` entry does not include a `replaces` key
- **THEN** the sync script SHALL process the entry identically to its current behavior with no deletion logic invoked

#### Scenario: Replaces key with multiple paths
- **WHEN** a `files_to_sync` entry includes a `replaces` key with multiple file paths
- **THEN** the sync script SHALL process each path individually as a file to be removed

#### Scenario: Replaces key with empty list
- **WHEN** a `files_to_sync` entry includes a `replaces` key set to an empty list
- **THEN** the sync script SHALL process the entry identically to an entry without a `replaces` key, with no deletion logic invoked

### Requirement: Replaces paths are relative to downstream repo root
All paths listed in the `replaces` key MUST be interpreted as relative to the root of the downstream repository, not relative to the source or destination path.

#### Scenario: Path interpretation
- **WHEN** a `replaces` entry contains the path `.github/ISSUE_TEMPLATE/bug_report.md`
- **THEN** the sync script SHALL resolve that path relative to the cloned downstream repository root directory

### Requirement: Replaces paths validated for traversal safety
All `replaces` paths MUST be validated to ensure they resolve within the downstream repository clone directory. Paths containing `..` segments or that resolve outside the repository root after canonicalization SHALL be rejected.

#### Scenario: Replaces path with directory traversal
- **WHEN** a `replaces` entry contains a path with `..` segments (e.g., `../../etc/important`)
- **THEN** the sync script SHALL reject the entry, log an error, and skip the deletion without removing any file

#### Scenario: Replaces path is a clean relative path
- **WHEN** a `replaces` entry contains a path without `..` segments that resolves within the repository root
- **THEN** the sync script SHALL accept and process the path normally
