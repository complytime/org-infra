## 1. Workflow Scaffold

- [x] 1.1 Create `.github/workflows/reusable_publish_oras.yml` with `on: workflow_call` trigger
- [x] 1.2 Declare workflow-level `permissions: none` and define all inputs and outputs
- [x] 1.3 Set `concurrency` group to prevent parallel runs per `image_name` + `ref`

## 2. Permissions and Security Posture

- [x] 2.1 Set job-level permissions: `contents: read`, `packages: write`, `id-token: write`, `attestations: write`
- [x] 2.2 Gate the entire `publish` job on `if: github.ref_protected`
- [x] 2.3 Ensure all action `uses:` references are pinned to full 40-character commit SHAs with inline version comments

## 3. Artifact Push

- [x] 3.1 Add `actions/checkout` step with `persist-credentials: false`
- [x] 3.2 Add `docker/login-action` step for GHCR authentication
- [x] 3.3 Add `oras-project/setup-oras` step pinned to ORAS v1.3.0
- [x] 3.4 Add `Set image reference` step outputting `image` and `sha_tag` from env vars (no direct interpolation)
- [x] 3.5 Add `Push OCI artifact` step: filter blank lines from `paths` input, build `oras push` args array, pass annotations via env vars

## 4. Digest Capture and Validation

- [x] 4.1 Add `Fetch digest` step: call `oras manifest fetch --descriptor | jq -r '.digest'`
- [x] 4.2 Validate digest format with `grep -qE '^sha256:[a-f0-9]{64}$'`; fail with `::error::` if invalid
- [x] 4.3 Write validated digest to `$GITHUB_OUTPUT`

## 5. Supply-Chain Attestations

- [x] 5.1 Add `Attest SLSA provenance` step using `actions/attest-build-provenance` gated on `if: github.ref_protected`
- [x] 5.2 Add `Generate SBOM` step using `anchore/sbom-action` with `path: ${{ inputs.sbom_scan_path }}`, output `sbom.spdx.json`, gated on `if: github.ref_protected`
- [x] 5.3 Add `Attest SBOM` step using `actions/attest` with `sbom-path: sbom.spdx.json`, gated on `if: github.ref_protected`

## 6. Validation

- [x] 6.1 Confirm workflow passes `yamllint` with the org-infra `.yamllint.yml` config
- [x] 6.2 Confirm all action SHAs pass the org SHA-pin checker
- [x] 6.3 Validate end-to-end: POC run confirmed green (run #24032400693 on `sonupreetam/image-publish-test`)
- [x] 6.4 Verify SLSA provenance and SBOM attestations are present on pushed digest via `cosign verify-attestation`
