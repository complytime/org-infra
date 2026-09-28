# Complypack Publish Pipeline

This document describes how ampel branch-protection policies are published as
[complypack](https://github.com/complytime/complypack) OCI artifacts, the
dual-registry strategy, and how to cut a release.

## Overview

The ampel branch-protection granular policies (JSON files in
`compliance/ampel/branch-protection/`) are packaged as complypack OCI artifacts
and published to container registries. Downstream consumers (e.g., `complyctl`)
pull these artifacts via the `complypacks:` section in their `complytime.yaml`.

```text
┌──────────────────────────────┐
│  compliance/ampel/           │
│    branch-protection/        │
│      block-force-push.json   │
│      minimum-approvals.json  │     complypack pack
│      prevent-admin-bypass.json ──────────────────┐
│      require-code-owner-     │                   │
│        review.json           │                   ▼
│      require-pull-request.json  ┌─────────────────────────────┐
│                              │  │  OCI Artifact               │
└──────────────────────────────┘  │  artifactType:              │
                                  │    application/vnd.          │
                                  │    complypack.artifact.v1    │
                                  │  config: id, evaluator-id,  │
                                  │          version             │
                                  │  content: tar+gzip of       │
                                  │           policy JSON files  │
                                  └─────────────────────────────┘
```

## Dual-Registry Strategy

| Registry                                                | Purpose    | Tag format        | Trigger                                              |
|---------------------------------------------------------|------------|-------------------|------------------------------------------------------|
| `ghcr.io/complytime/complypack-ampel-branch-protection` | Dev / test | `sha-<commit>`    | Push to `main` (policy file changes)                 |
| `ghcr.io/complytime/complypack-ampel-branch-protection` | Release    | `vX.Y.Z` (semver) | `workflow_dispatch` (promote_quay=true, from a tag)  |
| `quay.io/complytime/complypack-ampel-branch-protection` | Production | `vX.Y.Z` (semver) | `workflow_dispatch` (promote_quay=true, from a tag)  |

GHCR is the staging area. Every push to `main` that modifies files under
`compliance/ampel/branch-protection/` triggers a publish to GHCR with a
commit-based tag. The artifact is signed with Sigstore keyless signing and
includes SLSA provenance and SBOM attestations.

Quay is the production registry. Promotion from GHCR to Quay is done via
`workflow_dispatch` with `promote_quay=true`, dispatched from a release tag.
The workflow rebuilds the complypack from the release commit, publishes to
GHCR with the release tag, signs it, then promotes the signed artifact to
Quay.

> **Note:** Automated release-triggered promotion via App token is a follow-up.

```text
Push to main                    workflow_dispatch
     │                          (promote_quay=true, from tag)
     ▼                                │
 prepare                          prepare
     │                                │
     ▼                                ▼
 publish-ghcr                    publish-ghcr
 (sha-<commit>, 0.0.0-dev)      (vX.Y.Z, X.Y.Z, attestations: true)
     │                                │
     ▼                                ▼
 sign-ghcr                       sign-ghcr
     │                                │
     ▼                                ▼
 ghcr.io/complytime/             promote-quay
   complypack-ampel-                  │
   branch-protection:                 ▼
   sha-abc123                    quay.io/complytime/
                                   complypack-ampel-
                                   branch-protection:
                                   v1.0.0
```

## Workflows

### `reusable_publish_complypack.yml`

Reusable workflow that packs and pushes complypack OCI artifacts to GHCR.
Designed to be consumed by any repository that needs to publish complypacks
for any evaluator.

**Key inputs:**

| Input                   | Required | Description                                    |
|-------------------------|----------|------------------------------------------------|
| `content_path`          | yes      | Directory containing policy files              |
| `image_name`            | yes      | Image name without registry                    |
| `tag`                   | yes      | Image tag                                      |
| `evaluator_id`          | yes      | Evaluator ID (e.g., `ampel`, `opa`)            |
| `complypack_id`         | yes      | Globally unique pack identifier                |
| `complypack_version`    | yes      | Version to embed in config                     |
| `go_version`            | no       | Go version for CLI install (default: `stable`) |
| `complypack_cli_ref`    | no       | CLI install ref (default: `latest`)            |
| `generate_attestations` | no       | `auto` or `true` (default: `auto`)             |

### `ci_publish_complypack.yml`

Consumer workflow specific to org-infra's ampel branch-protection policies.

**Triggers:**

- `push` to `main` with changes in `compliance/ampel/branch-protection/**`
- `workflow_dispatch` with the following inputs:

| Input          | Required                 | Description                                                                 |
|----------------|--------------------------|-----------------------------------------------------------------------------|
| `tag_override` | no                       | Custom GHCR tag (leave empty for default `sha-<commit>`)                    |
| `promote_quay` | no                       | Rebuild and publish to GHCR, then promote to Quay                           |
| `release_tag`  | when `promote_quay=true` | Quay destination tag (defaults to `github.ref_name` when dispatched from a tag) |

## Cutting a Release

### Prerequisites

- Quay credentials (`QUAY_USERNAME`, `QUAY_PASSWORD`) must be configured as
  repository secrets in org-infra.
- The policy changes you want to release must already be merged to `main`.

### Steps

1. **Create a GitHub Release** with a semver tag:

   ```bash
   gh release create v1.0.0 \
     --repo complytime/org-infra \
     --title "v1.0.0" \
     --notes "Publish ampel branch-protection complypack v1.0.0"
   ```

2. **Trigger the publish-and-promote workflow** from the release tag:

   ```bash
   gh workflow run ci_publish_complypack.yml \
     --repo complytime/org-infra \
     --ref v1.0.0 \
     -f promote_quay=true
   ```

   The workflow will:
   - Rebuild the complypack from the release commit
   - Publish to GHCR with the release tag (`v1.0.0`) and forced attestations
   - Sign the GHCR artifact with Sigstore keyless signing
   - Promote the signed artifact to `quay.io/complytime/complypack-ampel-branch-protection:v1.0.0`

3. **Monitor the workflow**:

   ```bash
   gh run watch --repo complytime/org-infra
   ```

4. **Verify the Quay artifact**:

   ```bash
   crane manifest \
     quay.io/complytime/complypack-ampel-branch-protection:v1.0.0
   ```

### Troubleshooting

**Promotion fails with "destination tag already exists":**

Quay tags are immutable. You cannot overwrite an existing release. If you need
to republish, use a new version tag (e.g., `v1.0.1`).

**Publish fails with "promote_quay requires dispatching from a tag":**

The workflow was dispatched from a branch instead of a tag. Re-run the
workflow using `--ref v1.0.0` to dispatch from the release tag.

## Manual Quay Promotion

Quay promotion is always manual via `workflow_dispatch` with
`promote_quay=true`. The workflow rebuilds the complypack from the specified
commit (tag or protected branch), publishes to GHCR, signs it, then
promotes to Quay.

> **Note:** Automated promotion via App token in `release.yml` is a
> follow-up. Until then, manual dispatch from a tag is the canonical
> promotion path.

### Steps

1. **Ensure a release tag exists** for the commit you want to promote.

2. **Trigger the publish-and-promote workflow** from the tag:

   ```bash
   gh workflow run ci_publish_complypack.yml \
     --repo complytime/org-infra \
     --ref v0.5.0 \
     -f promote_quay=true
   ```

   When dispatched from a tag, `release_tag` defaults to the tag name
   (`v0.5.0`). To use a different Quay tag, pass `-f release_tag=v0.5.1`.

3. **Monitor the workflow**:

   ```bash
   gh run watch --repo complytime/org-infra
   ```

4. **Verify the Quay artifact**:

   ```bash
   crane manifest \
     quay.io/complytime/complypack-ampel-branch-protection:v0.5.0
   ```

### When to use manual promotion

- **Standard release flow**: After creating a GitHub Release, dispatch the
  workflow from the release tag to publish and promote.
- **Re-promotion after failure**: If the workflow failed mid-run, re-dispatch
  from the same tag (use a new version tag if the Quay tag already exists,
  since Quay tags are immutable).

## Local Testing

### Prerequisites

```bash
# Install the complypack CLI
go install github.com/complytime/complypack/cmd/complypack@latest

# Verify
complypack --help
```

### Pack locally (no push)

```bash
# Create a workspace
WORK=$(mktemp -d)
cp compliance/ampel/branch-protection/*.json "$WORK/"

# Generate config at workspace root (where the CLI expects it)
cat > complypack.yaml <<EOF
id: io.complytime.ampel-branch-protection
evaluator-id: ampel
version: 0.0.0-dev
EOF

# Pack (--skip-validation required for non-OPA evaluators)
complypack pack --skip-validation "$WORK" \
  "ghcr.io/<your-username>/complypack-ampel-branch-protection:test"

# Cleanup
rm -f complypack.yaml
rm -rf "$WORK"
```

**Notes:**

- The `complypack.yaml` config must be at the **current working directory**,
  not inside the content directory. The CLI reads `./complypack.yaml` by
  default (override with `--config`).
- `--skip-validation` is required because `ampel` is not a registered
  evaluator in complypack (only OPA/Rego is built-in). The policy JSON files
  are packed as opaque content and consumed by the ampel provider.
- Pushing to GHCR requires authentication with `write:packages` scope. In CI,
  this is handled by `docker/login-action` with `GITHUB_TOKEN`.

## Consumer Configuration

Downstream repositories pull the complypack artifact in their
`complytime.yaml`:

```yaml
complypacks:
  - url: quay.io/complytime/complypack-ampel-branch-protection:v1.0.0
    id: ampel-bp-pack
```

The `complyctl get` command resolves the OCI reference, pulls the artifact,
and extracts the policy files for the compliance scan.

### Digest pinning

For production use, pin to a digest instead of a mutable tag. Digests are
immutable and ensure that every consumer pulls the exact same artifact.

1. **Get the digest** after Quay promotion:

   ```bash
   crane digest \
     quay.io/complytime/complypack-ampel-branch-protection:v1.0.0
   # Output: sha256:abc123...
   ```

2. **Pin to the digest** in `complytime.yaml`:

   ```yaml
   complypacks:
     - url: quay.io/complytime/complypack-ampel-branch-protection@sha256:abc123...
       id: ampel-bp-pack
   ```

Tag-based pins (e.g., `:v1.0.0`) are acceptable for development because Quay
tags are immutable in this pipeline (`fail_if_dest_exists: true`). Digest pins
provide an additional guarantee that the reference cannot be altered by
registry-side tag mutations.

### Updating dependent repositories after a release

After promoting a new version to Quay:

1. Retrieve the digest for the new tag (see above).
2. Update the `complypacks` entry in each dependent repository's
   `.complytime/complytime.yaml` to reference the new version or digest.
3. Open a PR in each dependent repository with the updated pin.

## Related

- [Issue #306](https://github.com/complytime/org-infra/issues/306) —
  Original issue for this feature.
- [Issue #307](https://github.com/complytime/org-infra/issues/307) —
  Remove TEMPORARY manual staging from `reusable_compliance.yml`
  (depends on downstream provider adoption of this complypack).
- [complypack](https://github.com/complytime/complypack) —
  The complypack library and CLI.
- [complyctl#536](https://github.com/complytime/complyctl/pull/536) —
  complyctl `complypack-pull` feature that consumes these artifacts.
