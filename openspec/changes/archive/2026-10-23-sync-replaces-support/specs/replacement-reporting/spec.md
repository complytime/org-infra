## ADDED Requirements

### Requirement: Commit message lists replaced files
When superseded files are deleted, the sync commit message SHALL distinguish between updated files and removed files.

#### Scenario: Commit with both updates and replacements
- **WHEN** a sync commit includes both file updates and file deletions from `replaces`
- **THEN** the commit message SHALL include a section with the heading "Removed files (replaced):" listing each removed file in the format `- <removed_path> (replaced by <replacement_path>)`, separate from the "Updated files:" section

#### Scenario: Commit with only updates
- **WHEN** a sync commit includes only file updates and no replacements
- **THEN** the commit message format SHALL remain unchanged from current behavior

### Requirement: PR description lists replaced files
When a sync PR includes superseded file deletions, the PR body SHALL include a section listing the removed files and their replacements.

#### Scenario: PR with replaced files
- **WHEN** a sync PR is created or updated with commits that include file replacements
- **THEN** the PR body SHALL include a "## Files Removed (Replaced)" section listing each removed file with the format `- \`<removed_path>\` (replaced by \`<replacement_path>\`)`

#### Scenario: PR without replaced files
- **WHEN** a sync PR is created or updated with no file replacements
- **THEN** the PR body format SHALL remain unchanged from current behavior
