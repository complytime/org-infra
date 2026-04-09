## Context

The org-infra repo maintains reusable GitHub Actions workflows for the complytime org. The existing
`reusable_publish_ghcr.yml` provides supply-chain-secure publishing (SLSA + SBOM) for container
images. It is tightly coupled to Docker Buildx and requires a `Containerfile` — making it unusable
for repos that publish data-only OCI artifacts (YAML policy bundles, JSON configs, etc.).

The `complytime-policies` repo is the first concrete consumer: it produces Gemara YAML bundles
(catalogs, policies, guidance) that `complyctl` fetches by OCI layer media type. These must be
pushed as proper OCI artifacts with the exact media types defined in `complyctl`'s source code, not
as container images.

## Goals / Non-Goals

**Goals:**
- Push arbitrary local files as a multi-layer OCI artifact to GHCR via ORAS CLI
- Attach SLSA provenance attestation (`actions/attest-build-provenance`)
- Generate an SPDX SBOM from a local directory scan (`anchore/sbom-action` with `path:`, not `image:`)
- Attach SBOM attestation (`actions/attest`)
- Match the input/output contract shape of `reusable_publish_ghcr.yml` where applicable
- All actions pinned to full commit SHAs per org policy

**Non-Goals:**
- Container image publishing (covered by `reusable_publish_ghcr.yml`)
- Quay.io or other non-GHCR registries
- Multi-platform / multi-arch ORAS pushes
- Vulnerability scanning of data-only artifacts
- Making `reusable_sign_and_verify.yml`'s vuln check optional (tracked in issue #173)

## Decisions

### 1. ORAS CLI instead of Docker Buildx
**Decision**: Use `oras-project/setup-oras` + `oras push` instead of `docker build`.  
**Rationale**: ORAS pushes arbitrary files directly as OCI artifacts with explicit media-type
annotations. Docker Buildx produces an OCI container image manifest — the wrong artifact type for
data-only content.  
**Alternative considered**: `crane` — rejected because it doesn't support per-layer `mediaType`
annotations required by `complyctl`'s `LoadLayerByMediaType`.

### 2. Digest capture via `oras manifest fetch` post-push
**Decision**: Capture the digest by calling `oras manifest fetch --descriptor` after `oras push`,
not by parsing push stdout.  
**Rationale**: `oras push` stdout format is not guaranteed stable. `oras manifest fetch
--descriptor | jq -r '.digest'` always returns `sha256:<64-hex>` regardless of ORAS version.
The step validates the format with a regex before writing to `$GITHUB_OUTPUT`.  
**Alternative considered**: Parsing `oras push --output json` — rejected; JSON output flag not
available in ORAS v1.x.

### 3. Directory SBOM, not image SBOM
**Decision**: Use `anchore/sbom-action` with `path: <sbom_scan_path>` (default `.`).  
**Rationale**: There is no container image to scan. A directory SPDX scan of the source repo
produces an SBOM that accurately lists file checksums. An empty `packages` array in the SPDX
document is semantically valid for YAML-only content.  
**Alternative considered**: Skipping SBOM — rejected to maintain supply-chain parity with
`reusable_publish_ghcr.yml`.

### 4. Defense-in-depth ref gate
**Decision**: Apply `if: github.ref_protected` at both the job level AND on each individual
attestation step.  
**Rationale**: The job gate prevents any execution on unprotected refs. The per-step gates ensure
attestations cannot run even if the job-level condition is circumvented (e.g., a future caller
override).

### 5. Annotations via environment variables
**Decision**: All OCI annotations (`--annotation "key=value"`) are passed using shell variables
sourced from `env:` blocks, never via `${{ inputs.foo }}` interpolated directly in the `run:` script.  
**Rationale**: Prevents shell injection from untrusted caller-supplied strings. Input values are
assigned to env vars at the GitHub Actions layer (safely quoted); the shell only sees variable
references.

### 6. Empty-line filtering for `paths` input
**Decision**: Filter blank lines from the newline-separated `paths` input before building the
`oras push` argument array.  
**Rationale**: YAML multiline string inputs commonly include a trailing newline. Passing an empty
string as a positional argument to `oras push` causes a parse error.

## Risks / Trade-offs

- **Media type caller error** → `complyctl list`/`generate`/`scan` silently fail to find content if
  wrong media types are used. Mitigation: document the exact types from `complyctl/internal/complytime/consts.go`
  in the workflow header and in spec examples; the workflow itself is generic and cannot validate types.

- **Issue #173 blocks full supply-chain chain** → `reusable_sign_and_verify.yml` requires a vuln
  attestation step that has no equivalent for data-only artifacts. Callers must set
  `enable_verify_vuln: false` until #173 adds an opt-out flag. Mitigation: document prominently in
  workflow header comment; tracked separately.

- **ORAS version drift** → Pinning `oras-project/setup-oras` to `version: 1.3.0` prevents
  unexpected behaviour from ORAS CLI changes. Mitigation: review on each ORAS minor release.
