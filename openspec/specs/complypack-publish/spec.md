## ADDED Requirements

### Requirement: Reusable complypack pack and push
The reusable workflow SHALL accept a content directory path, registry image name, tag, evaluator ID, complypack ID, and complypack version as inputs and produce a complypack OCI artifact pushed to GHCR.

#### Scenario: Successful pack and push
- **WHEN** the reusable workflow is called with valid inputs including a content directory containing policy files
- **THEN** the workflow packs the content directory into a complypack OCI artifact and pushes it to `ghcr.io/<image_name>:<tag>`

#### Scenario: Complypack config generated from inputs
- **WHEN** the reusable workflow executes
- **THEN** the workflow generates a `complypack.yaml` containing `id`, `evaluator-id`, and `version` fields from the provided inputs, without requiring a checked-in config file

#### Scenario: Digest and output validation
- **WHEN** the artifact is successfully pushed to GHCR
- **THEN** the workflow outputs `digest` in `sha256:<64-hex-chars>` format, `image` matching the input `image_name`, and `tag` matching the input `tag`

#### Scenario: Pack failure
- **WHEN** the complypack CLI fails to pack the content directory (invalid path, malformed content, or CLI error)
- **THEN** the workflow fails with a non-zero exit code and the CLI error output is visible in the workflow logs

#### Scenario: Digest retrieval failure
- **WHEN** the ORAS manifest fetch fails or returns a digest not matching `sha256:<64-hex-chars>` format
- **THEN** the workflow fails with a clear error message indicating the unexpected digest format

### Requirement: Supply chain attestations
The reusable workflow SHALL generate SLSA provenance and SBOM attestations for published complypack artifacts when attestation generation is enabled.

#### Scenario: Provenance and SBOM on protected ref
- **WHEN** the workflow runs on a protected ref with attestation generation set to auto
- **THEN** SLSA provenance attestation and an SBOM attestation (scanning the content directory) are generated and pushed to the registry alongside the artifact

#### Scenario: No attestations on unprotected ref with auto mode
- **WHEN** the workflow runs on an unprotected ref with attestation generation set to auto
- **THEN** no attestations are generated

#### Scenario: Forced attestation generation
- **WHEN** the workflow runs with attestation generation set to true
- **THEN** SLSA provenance and SBOM attestations are generated regardless of ref protection status

### Requirement: Automatic publish on policy change
The consumer workflow SHALL publish a complypack artifact to GHCR whenever ampel branch-protection policy files change on the main branch.

#### Scenario: Policy file pushed to main
- **WHEN** a commit is pushed to the main branch that modifies files under `compliance/ampel/branch-protection/`
- **THEN** the complypack is packed and pushed to GHCR with a `sha-<commit>` tag

#### Scenario: Unrelated files changed
- **WHEN** a commit is pushed to the main branch that does not modify files under `compliance/ampel/branch-protection/`
- **THEN** the complypack publish workflow does not trigger

### Requirement: Keyless signing on GHCR
The consumer workflow SHALL sign the GHCR artifact using Sigstore keyless signing after a successful publish on a protected ref.

#### Scenario: Sign after publish on protected ref
- **WHEN** a complypack artifact is successfully pushed to GHCR on a protected ref
- **THEN** the artifact is signed with Sigstore keyless signing and the signature is verifiable with cosign

#### Scenario: No signing on unprotected branch
- **WHEN** a complypack artifact is published from an unprotected branch (not a tag)
- **THEN** the signing job is skipped because the publish guard blocks unprotected branch builds

### Requirement: Rebuild-and-promote Quay promotion
The consumer workflow SHALL promote the complypack artifact from GHCR to Quay via manual `workflow_dispatch` with `promote_quay=true`, rebuilding the artifact from the release commit before promotion. The `release: published` trigger has been removed in favor of manual dispatch.

#### Scenario: Manual dispatch triggers rebuild and promotion
- **WHEN** the workflow is manually dispatched with `promote_quay=true` from a release tag
- **THEN** the complypack artifact is rebuilt from the release commit, published to GHCR with the release tag and forced attestations, signed, and promoted to Quay with the release tag

#### Scenario: Promotion requires tag dispatch or release_tag input
- **WHEN** the workflow is dispatched with `promote_quay=true` from a branch without providing `release_tag`
- **THEN** the prepare job fails with a clear error message indicating that dispatching from a tag or providing `release_tag` is required

#### Scenario: Immutable Quay tags
- **WHEN** a release tag already exists on Quay
- **THEN** the promotion fails with a non-zero exit code and an error message indicating the destination tag already exists, without modifying the existing artifact

### Requirement: Manual dispatch
The consumer workflow SHALL support manual triggering for re-publishing or testing.

#### Scenario: Manual dispatch without tag override
- **WHEN** the workflow is manually dispatched without a `tag_override` input
- **THEN** the workflow publishes the complypack artifact to GHCR with tag `sha-<github.sha>`

#### Scenario: Manual dispatch with tag override
- **WHEN** the workflow is manually dispatched with a `tag_override` value
- **THEN** the workflow publishes the complypack artifact to GHCR with the provided tag

### Requirement: Workflow file naming correction
The misspelled promote workflow file SHALL be renamed from `resuable_publish_quay.yml` to `reusable_publish_quay.yml` with all in-repo references updated.

#### Scenario: Renamed file
- **WHEN** the rename is applied
- **THEN** the file exists at `.github/workflows/reusable_publish_quay.yml` and no file exists at the old path

#### Scenario: In-repo references updated
- **WHEN** the rename is applied
- **THEN** all references within org-infra (including README.md) use the corrected filename
