## ADDED Requirements

### Requirement: Direct push to target repositories

The sync system SHALL clone each target repository directly using the authenticated
token, create a feature branch, apply file changes, push the branch, and open a
pull request against the default branch.

#### Scenario: Successful sync creates PR

- **WHEN** the sync runs for a target repo with files that need updating
- **THEN** a new branch is created, changes are pushed, and a PR is opened against
  the default branch

#### Scenario: No changes needed

- **WHEN** all synced files in the target repo are already up to date
- **THEN** no branch is created and no PR is opened

### Requirement: Branch name enforcement

The sync system SHALL only push to branches matching a designated sync prefix. The
system SHALL validate the branch name before any push operation and refuse to push
if the name does not match the expected pattern.

#### Scenario: Valid branch name accepted

- **WHEN** the sync creates a branch with the sync prefix
- **THEN** the push operation proceeds

#### Scenario: Invalid branch name rejected

- **WHEN** a branch name does not start with the sync prefix
- **THEN** the push operation is refused and an error is logged

### Requirement: No force push

The sync system SHALL NOT use force push under any circumstances. All push
operations SHALL be standard (fast-forward or create-new-branch) pushes only.

#### Scenario: Push operation uses standard push

- **WHEN** the sync pushes a branch to a target repository
- **THEN** the git push command does not include any force flags

### Requirement: API endpoint restriction

The sync system SHALL maintain an allowlist of permitted GitHub API endpoints and
methods. Any API request not matching the allowlist SHALL be rejected by the script
before the request is sent.

#### Scenario: Allowed endpoint succeeds

- **WHEN** the script makes a request to an allowed endpoint with a permitted method
- **THEN** the request is sent to the GitHub API

#### Scenario: Disallowed endpoint blocked

- **WHEN** the script attempts a request to an endpoint not in the allowlist
- **THEN** the request is blocked and an error is returned without contacting the API

### Requirement: Duplicate PR detection

The sync system SHALL check for existing open pull requests from the sync process
before creating a new one. If an open sync PR already exists for a target
repository, the system SHALL skip PR creation and log the existing PR URL.

#### Scenario: No existing sync PR

- **WHEN** the sync checks for open PRs and finds none matching the sync title
- **THEN** a new PR is created

#### Scenario: Existing sync PR found

- **WHEN** the sync checks for open PRs and finds one matching the sync title
- **THEN** PR creation is skipped and the existing PR URL is logged

### Requirement: Dry run mode

The sync system SHALL support a dry-run mode that shows what changes would be made
without actually pushing branches or creating pull requests.

#### Scenario: Dry run reports changes without modifying repos

- **WHEN** the sync runs in dry-run mode
- **THEN** the system reports which files would be updated for each repo but does
  not push any branches or create any PRs

### Requirement: Repository inventory accuracy

The sync configuration SHALL only reference repositories that exist in the target
organization. The script SHALL gracefully handle cases where a configured repository
does not exist (e.g., was deleted or moved).

#### Scenario: Configured repo does not exist

- **WHEN** the sync encounters a repository that does not exist in the organization
- **THEN** the script logs a warning and continues processing the remaining repos
