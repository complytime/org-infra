# Feature Specification: Reusable ORAS OCI Artifact Publish Workflow

## Document Overview

This specification details a reusable GitHub Actions workflow for publishing non-container OCI artifacts
(e.g., YAML policy content, data files) to GHCR via ORAS CLI, with full supply-chain security parity to
`reusable_publish_ghcr.yml`: SLSA provenance attestation and SPDX SBOM attestation.

**Key Metadata:**
- Workflow File: `.github/workflows/reusable_publish_oras.yml`
- Issue: [#172](https://github.com/complytime/org-infra/issues/172)
- Date: 2026-04-06
- Current Status: **POC Validated** — end-to-end green ([run #24032400693](https://github.com/sonupreetam/image-publish-test/actions/runs/24032400693)); ready for PR
- First Consumer: `complytime-policies` (Gemara YAML bundles, per-bundle publishing — see spike [complytime-policies#10](https://github.com/complytime/complytime-policies/issues/10))

## ⚠️ Media Type Correction (from complyctl source audit)

Issue #172 used example layer media types of `application/vnd.complytime.gemara.yaml`. These are
**incorrect** and would cause `complyctl get` to store the artifact but `complyctl list` / `generate` /
`scan` to silently fail to find catalog or policy content.

The definitive media types, sourced from
[`internal/complytime/consts.go`](https://github.com/complytime/complyctl/blob/main/internal/complytime/consts.go)
and confirmed by
[`internal/policy/loader.go:LoadLayerByMediaType`](https://github.com/complytime/complyctl/blob/main/internal/policy/loader.go):

| Layer content | Correct media type |
|--------------|-------------------|
| Gemara catalog YAML | `application/vnd.gemara.catalog.v1+yaml` |
| Gemara policy YAML | `application/vnd.gemara.policy.v1+yaml` |
| Gemara guidance YAML | `application/vnd.gemara.guidance.v1+yaml` |

The `complytime-policies` caller workflow **must** use these exact types in the `paths` input. The
reusable workflow is generic (it accepts whatever the caller provides), so no change is needed to
`reusable_publish_oras.yml` itself — but the caller and the issue example must be corrected.

Correct `paths` input example for a catalog + policy pair:
```text
bundles/nist-800-53-r5-catalog.yaml:application/vnd.gemara.catalog.v1+yaml
bundles/nist-800-53-r5-policy.yaml:application/vnd.gemara.policy.v1+yaml
```

## Background and Motivation

Several complytime repos publish non-container artifacts (e.g., YAML policy content, data files) as OCI
artifacts to GHCR. The existing `reusable_publish_ghcr.yml` is container-image specific: it requires a
Containerfile, uses Docker Buildx, and generates an SBOM from the resulting image layer. Repositories
producing data-only OCI artifacts have no Containerfile and no container image to scan.

ORAS (OCI Registry As Storage) enables pushing arbitrary files directly to any OCI registry without
building a container image. A parallel reusable workflow using ORAS provides the same supply-chain
security posture (SLSA + SBOM) for data artifacts.

## Core User Scenarios

### Priority 1: Push OCI Artifact with Supply-Chain Attestations

A repository maintainer calls `reusable_publish_oras.yml` from a caller workflow, supplying the artifact
paths (with their OCI media types), the artifact type annotation, and an image name. The workflow pushes
the artifact to GHCR tagged as `sha-<40-char-commit-sha>`, attaches SLSA provenance, generates an SPDX
SBOM from the specified directory, and attaches the SBOM as an attestation to the pushed digest.

**Test Coverage:** Validates that the digest output matches the pushed artifact, that SLSA provenance and
SBOM attestations are present on the artifact in GHCR, and that the workflow only executes on protected
refs.

### Priority 2: Caller Controls Artifact Content — Per-Bundle

The `complytime-policies` caller iterates `bundles/*.yaml` files, each of which contains a `layers:` list
of relative file paths. For each bundle, it calls `reusable_publish_oras.yml` once with a unique
`image_name` (e.g., `complytime/policies/ampel-branch-protection`) and a `paths` input derived from
the bundle's `layers:` list, mapping each file to its correct Gemara media type by directory path
convention (`catalogs/` → catalog type, `policies/` → policy type, `guidance/` → guidance type).

Example for `bundles/ampel-branch-protection.yaml` (2 layers, no guidance):
```text
governance/catalogs/ampel-branch-protection-catalog.yaml:application/vnd.gemara.catalog.v1+yaml
governance/policies/ampel-branch-protection-policy.yaml:application/vnd.gemara.policy.v1+yaml
```

Example for `bundles/cis-fedora-l1-server.yaml` (3 layers with shared guidance):
```text
governance/guidance/cis-fedora-l1-guidance.yaml:application/vnd.gemara.guidance.v1+yaml
governance/catalogs/cis-fedora-l1-server-catalog.yaml:application/vnd.gemara.catalog.v1+yaml
governance/policies/cis-fedora-l1-server-policy.yaml:application/vnd.gemara.policy.v1+yaml
```

**Test Coverage:** Validates that multiple path:mediatype pairs are correctly passed to `oras push` as
positional arguments, producing a multi-layer OCI manifest that `complyctl get` stores and
`complyctl generate`/`scan` can consume.

### Priority 2: SBOM Covers the Artifact Content

The SBOM scan path defaults to the repository root (`.`) and is configurable by the caller. For
data-only artifacts the SPDX document accurately lists file paths and checksums; there are no software
package entries. An empty SPDX package list is semantically correct for YAML-only content and passes
enterprise SBOM ingest pipelines.

**Test Coverage:** Verifies `sbom.spdx.json` is generated, is valid SPDX-JSON, and is attached to the
pushed digest as an attestation.

## Edge Cases Addressed

- **Protected ref gate**: Workflow runs only when `github.ref_protected` is true; both the push job and
  each attestation step are gated individually (defense in depth).
- **Digest capture**: The manifest digest from `oras push` is captured via `oras manifest fetch` after
  push to guarantee format consistency (`sha256:<64-hex>`).
- **Empty path lines**: Newline-separated paths input may contain blank lines; these are filtered before
  constructing the push argument array.
- **Annotation injection**: All OCI annotations are passed via environment variables, not interpolated
  directly into `run:` scripts.

## Functional Requirements Summary

The `reusable_publish_oras.yml` workflow must:

1. **Accept caller inputs**: `image_name` (required), `artifact_type` (required), `paths` (required),
   `image_description` (optional), `sbom_scan_path` (optional, default `.`).
2. **Push OCI artifact to GHCR**: Tag as `sha-<GITHUB_SHA>`, annotate with OCI source/revision labels.
3. **Output digest, image, sha_tag**: After a successful push.
4. **Attach SLSA provenance**: Via `actions/attest-build-provenance` against the pushed digest.
5. **Generate directory SBOM**: Via `anchore/sbom-action` with `path:` (not `image:`) input.
6. **Attach SBOM attestation**: Via `actions/attest` with the generated `sbom.spdx.json`.
7. **Run only on protected refs**: Via `if: github.ref_protected` on the job.
8. **Use pinned action SHAs**: All `uses:` references pinned to a full commit SHA with a version comment.
9. **Follow least-privilege permissions**: `contents: read`, `packages: write`, `id-token: write`,
   `attestations: write` at the job level; workflow-level permissions default to `none`.

## Success Metrics

- Any complytime repository can publish data-only OCI artifacts to GHCR via a two-file caller workflow.
- SLSA provenance and SBOM attestations are verifiable via `cosign verify-attestation` on the pushed
  digest.
- The workflow passes `yamllint` with the org-infra `.yamllint.yml` configuration.
- `reusable_sign_and_verify.yml` can be called against the published digest when vuln verification is
  made optional (tracked in issue #173).
- The first consumer (`complytime-policies`) successfully publishes Gemara YAML bundles end-to-end.

## Scope Boundaries

**Included:**
- `reusable_publish_oras.yml` reusable workflow
- SLSA provenance via `actions/attest-build-provenance`
- SPDX SBOM via `anchore/sbom-action` (directory scan) + `actions/attest`
- ORAS CLI install via `oras-project/setup-oras`
- GHCR authentication via `docker/login-action`

**Excluded:**
- Making `verify_vuln` optional in `reusable_sign_and_verify.yml` (tracked separately in issue #173)
- Consumer caller workflow for `complytime-policies` (tracked in complytime-policies#5)
- Multi-platform / multi-arch ORAS pushes
- Quay.io registry support
- Vulnerability scanning of data-only OCI artifacts
