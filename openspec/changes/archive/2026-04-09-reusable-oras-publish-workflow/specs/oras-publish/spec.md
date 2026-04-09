## ADDED Requirements

### Requirement: Accept caller-defined artifact inputs
The workflow SHALL accept `image_name` (required), `artifact_type` (required), and `paths`
(required) as inputs. It SHALL also accept `image_description` (optional) and `sbom_scan_path`
(optional, default `.`).

#### Scenario: Required inputs provided
- **WHEN** a caller workflow invokes `reusable_publish_oras.yml` with `image_name`, `artifact_type`, and `paths`
- **THEN** the workflow executes without input validation errors

#### Scenario: Optional inputs omitted
- **WHEN** a caller omits `image_description` and `sbom_scan_path`
- **THEN** `image_description` defaults to the value of `image_name`
- **AND** `sbom_scan_path` defaults to `.` (repository root)

---

### Requirement: Push OCI artifact to GHCR via ORAS
The workflow SHALL push the caller-specified files as a single OCI artifact to
`ghcr.io/<image_name>:sha-<40-char-commit-sha>` using the ORAS CLI with the provided
`artifact_type` annotation and OCI source/revision labels.

#### Scenario: Single-file artifact push
- **WHEN** `paths` contains one `file.yaml:application/vnd.gemara.policy.v1+yaml` entry
- **THEN** a single-layer OCI manifest is pushed to GHCR tagged `sha-<GITHUB_SHA>`

#### Scenario: Multi-file artifact push
- **WHEN** `paths` contains multiple `path:mediatype` entries (e.g., catalog + policy + guidance)
- **THEN** a multi-layer OCI manifest is pushed with each file as a separate layer with its declared media type

#### Scenario: Empty lines in paths input filtered
- **WHEN** the `paths` input string contains blank lines (e.g., trailing newline from YAML multiline)
- **THEN** blank lines are silently ignored and do not cause an `oras push` argument error

---

### Requirement: Expose digest, image reference, and sha_tag as outputs
The workflow SHALL output `digest` (`sha256:<64-hex>`), `image` (`ghcr.io/<image_name>`), and
`sha_tag` (`sha-<40-char-commit-sha>`) after a successful push.

#### Scenario: Digest format validation
- **WHEN** the artifact is pushed successfully
- **THEN** `digest` is fetched via `oras manifest fetch --descriptor` and validated against `^sha256:[a-f0-9]{64}$`
- **AND** the workflow fails with an error if the format does not match

---

### Requirement: Attach SLSA provenance attestation
The workflow SHALL attach a SLSA provenance attestation to the pushed artifact digest using
`actions/attest-build-provenance`, only when running on a protected ref.

#### Scenario: SLSA provenance on protected ref
- **WHEN** the workflow runs on a protected branch or tag (`github.ref_protected = true`)
- **THEN** SLSA provenance is attached to the pushed digest and verifiable via `cosign verify-attestation`

---

### Requirement: Generate and attach SPDX SBOM attestation
The workflow SHALL generate an SPDX-JSON SBOM by scanning the directory at `sbom_scan_path` using
`anchore/sbom-action`, then attach it as an attestation to the pushed digest using `actions/attest`.
Both steps run only on protected refs.

#### Scenario: Directory SBOM generated and attached
- **WHEN** the workflow runs on a protected ref
- **THEN** `sbom.spdx.json` is generated from the scanned directory
- **AND** it is attached to the pushed digest as a verifiable SPDX attestation

#### Scenario: SBOM valid for data-only content
- **WHEN** the scanned directory contains only YAML files (no software packages)
- **THEN** the SPDX document is valid with an empty `packages` array and file-level entries

---

### Requirement: Execute only on protected refs
The workflow job SHALL only execute when `github.ref_protected` is `true`. Each attestation step
SHALL additionally gate on `github.ref_protected` individually.

#### Scenario: Workflow skipped on unprotected ref
- **WHEN** a caller triggers the workflow from a non-protected branch
- **THEN** the `publish` job is skipped entirely (no push, no attestations)

#### Scenario: Attestation steps gated independently
- **WHEN** the job runs on a protected ref
- **THEN** each of the three attestation steps (SLSA, SBOM generate, SBOM attest) individually checks `github.ref_protected`

---

### Requirement: Least-privilege permissions
The workflow SHALL declare `permissions: none` at the workflow level and grant only the minimum
required permissions at the job level: `contents: read`, `packages: write`, `id-token: write`,
`attestations: write`.

#### Scenario: Workflow-level permissions default to none
- **WHEN** the workflow file is parsed
- **THEN** all permissions at the `permissions:` workflow-level block are set to `none`
- **AND** the job-level block grants only the four required permissions

---

### Requirement: All action references pinned to full commit SHAs
The workflow SHALL pin every `uses:` action reference to a full 40-character commit SHA with an
inline version comment.

#### Scenario: SHA-pinned action references
- **WHEN** the workflow file is linted with the org's SHA-pin checker
- **THEN** no action reference uses a mutable tag or branch ref
