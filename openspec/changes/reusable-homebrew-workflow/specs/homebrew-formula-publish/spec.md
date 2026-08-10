## ADDED Requirements

### Requirement: Formula generation from workflow inputs
The reusable workflow SHALL generate a valid Homebrew source-build formula from
caller-provided inputs without requiring template files or sed substitution.

#### Scenario: Successful formula generation
- **WHEN** a caller invokes the reusable workflow with valid inputs (tag, project name, description, binary name, tap repo, Go main path, ldflags module, homepage)
- **THEN** the workflow generates a Ruby formula file containing the correct class name, tarball URL, SHA256 checksum, license, Go build instructions, and version assertion test

#### Scenario: Formula class name derived from project name
- **WHEN** the project name contains hyphens (e.g., `complyctl`)
- **THEN** the formula class name is the PascalCase equivalent (e.g., `Complyctl`)

### Requirement: Source tarball SHA256 verification
The workflow SHALL download the source tarball for the given tag and compute
its SHA256 checksum for inclusion in the formula.

#### Scenario: Tarball download and checksum
- **WHEN** the workflow downloads the source tarball from the GitHub release
- **THEN** the computed SHA256 checksum is exactly 64 hexadecimal characters and is embedded in the formula

#### Scenario: Tarball not available
- **WHEN** the source tarball download fails after retries
- **THEN** the workflow fails with a clear error message indicating the tarball URL and HTTP status

### Requirement: Tag format validation
The workflow SHALL validate the tag input matches semver format as a
defense-in-depth measure.

#### Scenario: Valid semver tag
- **WHEN** the tag matches `^v[0-9]+\.[0-9]+\.[0-9]+(-[a-zA-Z0-9.]+)?$`
- **THEN** the workflow proceeds with formula generation

#### Scenario: Invalid tag format
- **WHEN** the tag does not match the expected semver format
- **THEN** the workflow fails with an error annotation before any formula generation

### Requirement: Formula quality gate
The workflow SHALL run `brew audit --strict` on the generated formula before
pushing to the tap repository.

#### Scenario: Audit passes
- **WHEN** `brew audit --strict --formula` passes on the generated formula
- **THEN** the workflow proceeds to push the formula to the tap

#### Scenario: Audit fails
- **WHEN** `brew audit --strict --formula` reports errors
- **THEN** the workflow fails and does not push to the tap repository

### Requirement: Tap repository push
The workflow SHALL push the generated formula to the configured tap repository
using a scoped GitHub App token.

#### Scenario: Successful push
- **WHEN** the formula passes audit and the tap repository is accessible
- **THEN** the workflow clones the tap repo, writes the formula to `Formula/<binary_name>.rb`, commits with a descriptive message, and pushes

#### Scenario: No changes needed (idempotent re-run)
- **WHEN** the generated formula is identical to the existing formula in the tap
- **THEN** the workflow exits successfully without creating a commit

#### Scenario: Token never persisted in git config
- **WHEN** the workflow pushes to the tap repository
- **THEN** the GitHub App token is used only via environment variable and is never written to git credential storage

### Requirement: Cross-repo authentication via GitHub App
The workflow SHALL use `actions/create-github-app-token` with caller-provided
secrets for cross-repo tap access.

#### Scenario: Token generation with scoped permissions
- **WHEN** the workflow generates a GitHub App token
- **THEN** the token is scoped to the tap repository with only contents:write permission

### Requirement: Minimum permissions
The workflow SHALL declare minimum required permissions at both workflow
and job level.

#### Scenario: Permission declarations
- **WHEN** the workflow is defined
- **THEN** workflow-level permissions are set to none (empty map) and job-level permissions grant only `contents: read`
