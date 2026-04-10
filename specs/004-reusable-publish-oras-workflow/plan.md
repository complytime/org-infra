# Implementation Plan: Reusable ORAS OCI Artifact Publish Workflow

**Branch**: `feat/reusable-publish-oras` | **Date**: 2026-04-06 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `/specs/004-reusable-publish-oras-workflow/spec.md`
**Resolves**: [complytime/org-infra#172](https://github.com/complytime/org-infra/issues/172)

## Summary

Add `.github/workflows/reusable_publish_oras.yml` — a reusable workflow that mirrors the supply-chain
security posture of `reusable_publish_ghcr.yml` but targets data-only OCI artifacts pushed via ORAS CLI.
The workflow installs ORAS, authenticates to GHCR, pushes the artifact, attaches SLSA provenance, and
generates and attaches an SPDX SBOM from a directory scan.

## Technical Context

**Language/Version**: YAML (GitHub Actions workflow syntax)
**Primary Dependencies**:
- `oras-project/setup-oras` — installs ORAS CLI from a pinned release
- `docker/login-action` — GHCR authentication (already used in `reusable_publish_ghcr.yml`)
- `actions/attest-build-provenance` — SLSA provenance (already pinned in `reusable_publish_ghcr.yml`)
- `anchore/sbom-action` — SPDX SBOM generation (already pinned in `reusable_publish_ghcr.yml`)
- `actions/attest` — SBOM attestation (already pinned in `reusable_publish_ghcr.yml`)

**Testing**: Validated via `yamllint` (local), MegaLinter (CI), and end-to-end call from
`complytime-policies` publish pipeline.

**Target Platform**: GitHub Actions (`ubuntu-latest`)
**Project Type**: CI/CD infrastructure (reusable workflow)
**Performance Goals**: Complete within 10 minutes for typical Gemara YAML artifact sets.
**Constraints**: Must pass `.yamllint.yml`; all `uses:` pinned to full SHA; least-privilege permissions.
**Scale/Scope**: Any complytime repository publishing non-container OCI artifacts to GHCR.

## Constitution Check

| Principle | Status | Evidence |
|-----------|--------|----------|
| I. Single Source of Truth | PASS | One reusable workflow for all ORAS OCI publishes; no per-repo duplication |
| II. Simplicity & Isolation | PASS | Focused responsibility: ORAS push + attestations only; no build steps |
| III. Incremental Improvement | PASS | New file only; no changes to existing workflows in this PR |
| IV. Readability First | PASS | Header comment, descriptive step names, input descriptions |
| V. Do Not Reinvent the Wheel | PASS | Reuses existing pinned action versions from `reusable_publish_ghcr.yml` |
| VI. Composability | PASS | Outputs `digest`, `image`, `sha_tag` for downstream composition (sign_and_verify) |
| VII. Convention Over Configuration | PASS | Sensible defaults (`sbom_scan_path: '.'`); image_description optional |
| YAML Naming Conventions | PASS | `reusable_publish_oras.yml` follows org naming pattern |
| YAML Security | PASS | Workflow-level permissions all `none`; job-level minimal grant |
| YAML Design | PASS | All inputs have descriptions and required flags |
| YAML Formatting | PASS | Header comment; 2-space indent; yamllint clean |
| Lint Configuration Awareness | PASS | Must pass `.yamllint.yml` and MegaLinter CI |

**Gate result**: PASS — no violations detected.

## Project Structure

```text
specs/004-reusable-publish-oras-workflow/
├── spec.md     # Feature specification
├── plan.md     # This file
└── tasks.md    # Actionable task list

.github/workflows/
└── reusable_publish_oras.yml   # NEW — reusable ORAS publish workflow
```

## Action Version Pinning

All actions reuse SHAs already established in the org-infra codebase where available:

| Action | SHA (pinned) | Version |
|--------|-------------|---------|
| `actions/checkout` | `de0fac2e4500dabe0009e67214ff5f5447ce83dd` | v6.0.2 |
| `docker/login-action` | `b45d80f862d83dbcd57f89517bcf500b2ab88fb2` | v4.0.0 |
| `actions/attest-build-provenance` | `a2bbfa25375fe432b6a289bc6b6cd05ecd0c4c32` | v4.1.0 |
| `anchore/sbom-action` | `e22c389904149dbc22b58101806040fa8d37a610` | v0.24.0 |
| `actions/attest` | `59d89421af93a897026c735860bf21b6eb4f7b26` | v4.1.0 |
| `oras-project/setup-oras` | `22ce207df3b08e061f537244349aac6ae1d214f6` | v1.2.4 — installs ORAS CLI **1.3.0** (v1.2.4 supports up to 1.3.0; 1.3.1 was released after this action tag). **Upgrade path**: setup-oras v2.0.0 is being prepared ([issue #160](https://github.com/oras-project/setup-oras/issues/160)) which includes v1.3.1 support (merged [PR #150](https://github.com/oras-project/setup-oras/pull/150) on Apr 1 2026). Update SHA + switch to `version: 1.3.1` once v2.0.0 is tagged. |

## Digest Capture Strategy

`oras push` prints output including the manifest digest. The most reliable cross-version capture strategy
is to call `oras manifest fetch` on the pushed tag immediately after push:

```bash
DIGEST=$(oras manifest fetch "ghcr.io/${IMAGE_NAME}:sha-${GITHUB_SHA}" --descriptor \
  | jq -r '.digest')
echo "digest=${DIGEST}" >> "$GITHUB_OUTPUT"
```

This avoids parsing `oras push` stdout (which has changed across ORAS versions) and is idempotent.

## SBOM: Directory Scan vs Image Scan

**Key difference from `reusable_publish_ghcr.yml`:**
- Container workflow: `anchore/sbom-action` uses `image:` input → scans the pushed OCI image layers.
- ORAS workflow: `anchore/sbom-action` uses `path:` input → scans a local directory for files.

For YAML-only artifacts the resulting SPDX document will contain:
- Files with checksums (SHA1, SHA256)
- No software package entries (accurate for data-only content)
- A valid `spdxVersion: SPDX-2.3` document header

The attestation type stored in GHCR (`https://spdx.dev/Document/v2.3`) is identical. The
`reusable_sign_and_verify.yml` verification step `cosign verify-attestation --type
https://spdx.dev/Document/v2.3` will succeed without modification.

## Per-Bundle Publishing — `complytime-policies` Structure

Confirmed from spike [complytime-policies#10](https://github.com/complytime/complytime-policies/issues/10)
and direct repo inspection. The `complytime-policies` `bundles/` directory contains:

```text
bundles/
├── ampel-branch-protection.yaml     # 2 layers (catalog + policy, no guidance)
├── cis-fedora-l1-server.yaml        # 3 layers (guidance + catalog + policy)
└── cis-fedora-l1-workstation.yaml   # 3 layers (shared guidance + catalog + policy)
```

Each bundle YAML has a flat `layers:` list of relative paths:

```yaml
# bundles/ampel-branch-protection.yaml
layers:
  - governance/catalogs/ampel-branch-protection-catalog.yaml
  - governance/policies/ampel-branch-protection-policy.yaml
```

The `complytime-policies` caller workflow (issue #7) reads each bundle YAML dynamically and calls
`reusable_publish_oras.yml` once per bundle. Layer→media-type mapping is derived from the governance
directory path (`catalogs/` → catalog, `policies/` → policy, `guidance/` → guidance). No hardcoded
layer count — the `ampel-branch-protection` bundle proves 2-layer manifests work correctly.

**Key finding from spike:** OCI content-addressing handles shared blobs (e.g.,
`cis-fedora-l1-guidance.yaml` is shared between server and workstation bundles) — the blob is uploaded
once and referenced by both manifests. No CI-level deduplication logic needed.

**`reusable_publish_oras.yml` is compatible as-is.** It is a generic per-artifact workflow. The
per-bundle matrix strategy is entirely the caller's responsibility (complytime-policies#7).

## POC Result

End-to-end validated in personal test repos:
- **Reusable workflow**: [`sonupreetam/org-infra-tests`](https://github.com/sonupreetam/org-infra-tests/blob/main/.github/workflows/reusable_publish_oras.yml)
- **Caller + fixtures**: [`sonupreetam/image-publish-test`](https://github.com/sonupreetam/image-publish-test/blob/main/.github/workflows/ci_publish_oras.yml)
- **Successful run**: [actions/runs/24032400693](https://github.com/sonupreetam/image-publish-test/actions/runs/24032400693)

All steps passed: checkout → GHCR login → ORAS install → push → digest fetch → SLSA provenance → SBOM → SBOM attest → cosign sign → verify signature → verify SLSA → verify SBOM.

**Gotcha found**: `setup-oras@v1.2.4` advertises ORAS CLI `1.3.0` support in release notes. Requesting `version: 1.3.1` fails at runtime with "official ORAS CLI releases does not contain version 1.3.1". Fixed by using `version: 1.3.0`.

## ⚠️ complyctl Media Type Audit — Issue #172 Example Is Incorrect

Source-audited from [complytime/complyctl](https://github.com/complytime/complyctl):

**`internal/complytime/consts.go`** defines the canonical Gemara layer media types:
```go
const (
    MediaTypeCatalog  = "application/vnd.gemara.catalog.v1+yaml"
    MediaTypeGuidance = "application/vnd.gemara.guidance.v1+yaml"
    MediaTypePolicy   = "application/vnd.gemara.policy.v1+yaml"
)
```

**`internal/policy/loader.go:LoadLayerByMediaType`** routes to the correct YAML content by matching
`layer.MediaType` exactly against these constants. No fuzzy match, no fallback.

**Impact on this workflow:**
- `reusable_publish_oras.yml` is generic — it passes whatever `paths` the caller provides to
  `oras push`. The workflow itself requires **no change**.
- The issue #172 example (`application/vnd.complytime.gemara.yaml`) would cause `complyctl get` to
  store a valid OCI artifact, but `complyctl generate`/`scan` would fail with "layer not found".
- The `complytime-policies` caller workflow **must** use the correct per-layer media types.

**Correct `paths` input for `complytime-policies`:**
```text
bundles/nist-800-53-r5-catalog.yaml:application/vnd.gemara.catalog.v1+yaml
bundles/nist-800-53-r5-policy.yaml:application/vnd.gemara.policy.v1+yaml
```

**`artifact_type`:** `application/vnd.complytime.gemara.policies.v1` (from the issue) is an OCI
manifest-level `artifactType` annotation. complyctl does not filter by this field — it uses layer
`mediaType` for routing. The value is still useful for OCI ecosystem discoverability but is not
required to match anything in complyctl's source.

## Downstream Impact: `reusable_sign_and_verify.yml`

`reusable_sign_and_verify.yml` currently verifies four attestation types for any artifact it receives:

| Step | Cosign type | Container image? | ORAS artifact? |
|------|-------------|-----------------|----------------|
| Verify signature | N/A (cosign sign) | ✅ | ✅ |
| Verify SLSA provenance | `https://slsa.dev/provenance/v1` | ✅ | ✅ |
| Verify SBOM | `https://spdx.dev/Document/v2.3` | ✅ | ✅ (directory SPDX) |
| Verify vuln scan | `vuln` | ✅ | ❌ not applicable |

**Impact**: The vuln verification step will **fail** when `reusable_sign_and_verify.yml` is called on an
ORAS artifact digest because no `vuln` attestation is attached by `reusable_publish_oras.yml`.

**Resolution**: Issue [#173](https://github.com/complytime/org-infra/issues/173) — add an
`verify_vuln` boolean input (default `true`) to `reusable_sign_and_verify.yml` so callers
publishing ORAS artifacts can opt out. This is a companion change tracked separately.

## Downstream Impact: `docker/build-push-action` buildx SPDX

`reusable_publish_ghcr.yml` sets `sbom: false` and `provenance: mode=max` on the buildx step to prevent
Docker Buildx from auto-attaching its own SPDX/SLSA documents (which would conflict with the
`actions/attest-build-provenance` and `actions/attest` attestations). This is container-workflow
specific. The ORAS workflow has no Buildx step, so this concern does not apply.

**No action required** for the ORAS workflow itself. The `sbom: false` note is documented here to clarify
why the ORAS workflow omits any equivalent buildx configuration.

## Downstream Impact: `anchore/sbom-action` — Format Compatibility

`anchore/sbom-action@v0.24.0` supports both `image:` and `path:` inputs. When using `path:`, the action
calls `syft` under the hood with a directory target. The `format: spdx-json` output and the
`spdxVersion: SPDX-2.3` header are identical regardless of input type. The `output-file: sbom.spdx.json`
name and the downstream `actions/attest` call are unchanged.

**No compatibility mismatch** between container and ORAS SBOM attestations from the cosign verification
perspective.

## Paths Input Parsing

The `paths` input is a multiline GitHub Actions string. Safe shell parsing:

```bash
PUSH_ARGS=()
while IFS= read -r line; do
  [[ -n "$line" ]] && PUSH_ARGS+=("$line")
done <<< "$PATHS_INPUT"

oras push "${IMAGE}:${TAG}" \
  --artifact-type "${ARTIFACT_TYPE}" \
  --annotation "org.opencontainers.image.source=${SOURCE}" \
  --annotation "org.opencontainers.image.revision=${REVISION}" \
  "${PUSH_ARGS[@]}"
```

All variable values sourced from `env:` block (not `${{ }}` interpolation inside `run:`) to prevent
injection.

## Complexity Tracking

No constitution violations to justify. The only material complexity is the paths input multi-line
parsing; mitigated by the safe `while read` pattern with env vars.
