## ADDED Requirements

### Requirement: Granular policies use semantic IDs
Each granular ampel policy file SHALL have a self-documenting, benchmark-agnostic `id` field that describes the verifiable condition as a kebab-case verb-phrase.

#### Scenario: Policy ID is self-documenting
- **WHEN** a user inspects any granular policy JSON file
- **THEN** the `id` field clearly communicates what the policy verifies without requiring a lookup table

#### Scenario: Policy IDs match the defined mapping
- **WHEN** the `compliance/ampel/branch-protection/` directory is loaded
- **THEN** the policy IDs are exactly: `require-pull-request`, `minimum-approvals`, `block-force-push`, `prevent-admin-bypass`, `require-code-owner-review`

### Requirement: Control references use semantic IDs
Each granular policy's `meta.controls[]` entry referencing the `repo-branch-protection` framework SHALL use a semantic control ID that describes the safeguard area as a kebab-case noun-phrase.

#### Scenario: Control reference IDs match the defined mapping
- **WHEN** any granular policy file's `meta.controls` array is inspected
- **THEN** the entry with `"framework": "repo-branch-protection"` has one of: `pull-request-enforcement`, `approval-requirements`, `force-push-restriction`, `admin-bypass-prevention`, `code-owner-enforcement`

#### Scenario: External framework references are unchanged
- **WHEN** any granular policy file has an OSPS framework control reference
- **THEN** the OSPS `class` and `id` values remain unchanged from their current values

### Requirement: Policies grouped by domain
Granular policy files SHALL be organized under `compliance/ampel/<domain>/` where each domain subdirectory represents one logical policy group.

#### Scenario: Branch protection policies are grouped
- **WHEN** the `compliance/ampel/branch-protection/` directory is listed
- **THEN** it contains exactly 5 JSON files, one per branch protection policy

#### Scenario: No nested subdirectories within a group
- **WHEN** a domain directory (e.g., `branch-protection/`) is listed
- **THEN** it contains only JSON files and no subdirectories

### Requirement: Old monolithic bundle is removed
The old `compliance/ampel/branch-protection-rules.json` file and the `compliance/ampel/policies/` directory SHALL NOT exist.

#### Scenario: No legacy files remain
- **WHEN** the `compliance/ampel/` directory is listed
- **THEN** it contains only domain subdirectories (e.g., `branch-protection/`) and no top-level JSON files or `policies/` directory

### Requirement: Workflow sources policies from org-infra
The `reusable_compliance.yml` workflow SHALL source granular policy files from the org-infra repository's `compliance/ampel/` directory, not from any other repository's testdata.

#### Scenario: Workflow checks out org-infra
- **WHEN** the workflow runs
- **THEN** it performs a checkout of the `complytime/org-infra` repository at the default branch with sparse-checkout limited to `compliance/ampel` and `persist-credentials: false`

#### Scenario: Workflow copies from org-infra directory
- **WHEN** the workflow stages granular policies
- **THEN** it copies files from the org-infra checkout's `compliance/ampel/branch-protection/` directory to the runtime `.complytime/ampel/granular-policies/` directory

#### Scenario: Staging step documents temporary nature
- **WHEN** the workflow's copy step is inspected
- **THEN** it includes a comment indicating this manual staging is temporary pending OCI-based distribution

### Requirement: Spec docs reflect current IDs and paths
The spec documentation SHALL reference the current semantic policy IDs and directory paths.

#### Scenario: Quickstart table uses semantic IDs
- **WHEN** the spec quickstart document is read
- **THEN** the policy requirements table uses the new semantic IDs instead of `BP-X.YY` identifiers

#### Scenario: Spec references correct source path
- **WHEN** the spec document references the granular policy source
- **THEN** it references `compliance/ampel/branch-protection/` instead of `cmd/ampel-plugin/convert/testdata/policies/`
