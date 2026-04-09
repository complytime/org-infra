# Quickstart: Reusable ORAS OCI Artifact Publish Workflow

## For Repository Maintainers (Publishing Data-Only OCI Artifacts)

### 1. Add the caller workflow

Create `.github/workflows/publish_<artifact>.yml` in your repository. The example below is for
a `complytime-policies` style caller that publishes a single Gemara YAML bundle:

```yaml
# SPDX-License-Identifier: Apache-2.0

name: Publish Gemara Bundle

on:
  push:
    branches:
      - main

permissions:
  contents: none

jobs:
  publish-bundle:
    name: Publish ampel-branch-protection bundle
    permissions:
      contents: read
      packages: write
      id-token: write
      attestations: write
    uses: complytime/org-infra/.github/workflows/reusable_publish_oras.yml@main
    with:
      image_name: complytime/policies/ampel-branch-protection
      artifact_type: application/vnd.complytime.gemara.policies.v1
      paths: |
        governance/catalogs/ampel-branch-protection-catalog.yaml:application/vnd.gemara.catalog.v1+yaml
        governance/policies/ampel-branch-protection-policy.yaml:application/vnd.gemara.policy.v1+yaml
```

### 2. Use the correct Gemara layer media types

The `paths` input maps each local file to its OCI layer media type. The exact types are defined in
[`complyctl/internal/complytime/consts.go`](https://github.com/complytime/complyctl/blob/main/internal/complytime/consts.go).
Using the wrong type causes `complyctl list` / `generate` / `scan` to silently fail to find content.

| Layer content | Correct media type |
|--------------|-------------------|
| Gemara catalog YAML | `application/vnd.gemara.catalog.v1+yaml` |
| Gemara policy YAML | `application/vnd.gemara.policy.v1+yaml` |
| Gemara guidance YAML | `application/vnd.gemara.guidance.v1+yaml` |

> **Do NOT use** `application/vnd.complytime.gemara.yaml` — this is the incorrect example from
> issue #172 and will cause `complyctl` to silently fail.

### 3. Verify the workflow runs on a protected ref

The workflow is gated on `github.ref_protected`. It will be skipped entirely on feature branches.
Push to a protected branch (e.g., `main`) to trigger the publish job and attestations.

## Customizing Inputs

| Input | Required | Default | Description |
|-------|----------|---------|-------------|
| `image_name` | Yes | — | Image name without registry, e.g. `complytime/policies/my-bundle` |
| `artifact_type` | Yes | — | OCI `artifactType` annotation for manifest-level discovery |
| `paths` | Yes | — | Newline-separated `file:mediatype` pairs passed to `oras push` |
| `image_description` | No | `image_name` | OCI `org.opencontainers.image.description` annotation |
| `sbom_scan_path` | No | `.` | Local directory to scan for SPDX SBOM generation |

### Multi-bundle caller (matrix strategy)

For repositories with multiple bundles, use a matrix job to call the workflow once per bundle:

```yaml
jobs:
  publish-bundles:
    strategy:
      matrix:
        bundle:
          - name: ampel-branch-protection
            catalog: governance/catalogs/ampel-branch-protection-catalog.yaml
            policy: governance/policies/ampel-branch-protection-policy.yaml
    uses: complytime/org-infra/.github/workflows/reusable_publish_oras.yml@main
    with:
      image_name: complytime/policies/${{ matrix.bundle.name }}
      artifact_type: application/vnd.complytime.gemara.policies.v1
      paths: |
        ${{ matrix.bundle.catalog }}:application/vnd.gemara.catalog.v1+yaml
        ${{ matrix.bundle.policy }}:application/vnd.gemara.policy.v1+yaml
```

## Viewing Results

After the workflow runs on a protected ref:

1. **Job outputs**: The `digest`, `image`, and `sha_tag` outputs are available to downstream jobs
   that call `reusable_sign_and_verify.yml`.
2. **GHCR package**: The artifact appears at `ghcr.io/<image_name>:sha-<commit-sha>`.
3. **Attestations**: Verify SLSA provenance and SBOM attestations with:
   ```bash
   cosign verify-attestation \
     --type https://slsa.dev/provenance/v1 \
     ghcr.io/<image_name>@<digest>

   cosign verify-attestation \
     --type https://spdx.dev/Document/v2.3 \
     ghcr.io/<image_name>@<digest>
   ```

## Downstream: `reusable_sign_and_verify.yml`

**Important**: `reusable_sign_and_verify.yml` requires a vulnerability attestation by default.
ORAS artifacts have no equivalent vuln scan. Callers must set `enable_verify_vuln: false` until
issue [#173](https://github.com/complytime/org-infra/issues/173) is resolved:

```yaml
uses: complytime/org-infra/.github/workflows/reusable_sign_and_verify.yml@main
with:
  enable_verify_vuln: false
  digest: ${{ needs.publish-bundle.outputs.digest }}
  image: ${{ needs.publish-bundle.outputs.image }}
```

## Troubleshooting

### `complyctl list` / `generate` / `scan` finds no content after `complyctl get`

The artifact was pushed with incorrect layer media types. Verify `paths` uses the exact types from
the table above. Re-push with the corrected types — the digest will change.

### Workflow is skipped entirely (no steps run)

The triggering ref is not protected. The `publish` job gates on `github.ref_protected`. Push to
a branch with protection rules enabled, or trigger from a protected tag.

### `oras push` fails: "unexpected digest format"

The digest fetch step validates the format `sha256:<64-hex>`. If ORAS CLI returns a different
format (e.g., after a version upgrade), file an issue against `oras-project/setup-oras`. The
workflow currently pins ORAS CLI `1.3.0` via `setup-oras@v1.2.4`.

### Attestation steps skipped but push succeeded

Attestation steps have an additional `if: github.ref_protected` guard beyond the job-level gate.
If the job ran but attestations were skipped, check that `id-token: write` and `attestations: write`
permissions are granted in the caller workflow.

## For org-infra Contributors

The reusable workflow lives at `.github/workflows/reusable_publish_oras.yml`. All `uses:` actions
are pinned to full commit SHAs. When updating action versions, pin to the new SHA and update the
inline `# vX.Y.Z` comment.

The workflow is intentionally generic — it does not validate media types, artifact structure, or
ORAS version compatibility. These are the caller's responsibility.
