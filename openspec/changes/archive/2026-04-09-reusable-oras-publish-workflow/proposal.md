## Why

Several complytime repos publish non-container OCI artifacts (e.g., Gemara YAML bundles) to GHCR.
The existing `reusable_publish_ghcr.yml` is container-image specific — it requires a Containerfile,
uses Docker Buildx, and generates an SBOM from a container image layer. Repositories producing
data-only artifacts have no Containerfile and no image to scan.

## What Changes

- **New reusable workflow**: `.github/workflows/reusable_publish_oras.yml` — pushes arbitrary files
  as OCI artifacts to GHCR via ORAS CLI, with supply-chain security parity to
  `reusable_publish_ghcr.yml`: SLSA provenance attestation and SPDX SBOM attestation.
- **Inputs**: `image_name`, `artifact_type`, `paths` (newline-separated `path:mediatype` pairs),
  `image_description` (optional), `sbom_scan_path` (optional, defaults to `.`).
- **Outputs**: `digest`, `image`, `sha_tag` — matching the output contract of the existing GHCR workflow.
- **Protected-ref gate**: Workflow and each attestation step are individually gated on
  `github.ref_protected`.
- **Pinned action SHAs**: All `uses:` references pinned to full commit SHAs with version comments.

## Capabilities

### New Capabilities

- `oras-publish`: Reusable GitHub Actions workflow for publishing data-only OCI artifacts to GHCR
  via ORAS CLI, with SLSA provenance and SPDX SBOM attestations.

### Modified Capabilities

<!-- None — this is a net-new workflow; no existing requirement specs are changing. -->

## Impact

- **New file**: `.github/workflows/reusable_publish_oras.yml`
- **First consumer**: `complytime-policies` repo — per-bundle publishing of Gemara YAML bundles
  (catalogs, policies, guidance) using exact layer media types from `complyctl`.
- **Downstream note**: `reusable_sign_and_verify.yml` requires vuln attestation by default; callers
  of this workflow must set `enable_verify_vuln: false` until issue #173 is resolved.
- **Media type constraint**: Callers must use exact Gemara types (`application/vnd.gemara.catalog.v1+yaml`,
  `application/vnd.gemara.policy.v1+yaml`, `application/vnd.gemara.guidance.v1+yaml`) — not the
  incorrect `application/vnd.complytime.gemara.yaml` example used in issue #172.
