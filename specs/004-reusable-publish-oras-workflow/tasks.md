# Task List: Reusable ORAS OCI Artifact Publish Workflow

**Branch**: `feat/reusable-publish-oras` | **Plan**: [plan.md](plan.md)
**Generated from**: `/speckit.tasks`

## Tasks

### Task 1 — Pin `oras-project/setup-oras` SHA ✅

**Result**: `oras-project/setup-oras@22ce207df3b08e061f537244349aac6ae1d214f6` (v1.2.4)

**Gotcha found during POC**: `setup-oras@v1.2.4` supports ORAS CLI up to `1.3.0`. Requesting
`version: 1.3.1` fails at runtime with "official ORAS CLI releases does not contain version 1.3.1".
Workflow uses `version: 1.3.0`.

---

### Task 2 — Create `reusable_publish_oras.yml` ✅

**File**: `.github/workflows/reusable_publish_oras.yml`

All sections implemented and verified:
- Header comment + `name:` / `on: workflow_call:` with all inputs and outputs
- Workflow-level `permissions:` all `none`
- `concurrency:` block (`reusable-oras-${{ inputs.image_name }}-${{ github.ref }}`)
- `jobs.publish:` — `if: github.ref_protected`, `runs-on: ubuntu-latest`, `timeout-minutes: 10`
- All steps implemented with pinned SHAs
- `paths` input parsed via safe `while IFS= read -r` loop into bash array
- Digest captured via `oras manifest fetch --descriptor | jq -r '.digest'`

---

### Task 3 — Verify `yamllint` passes ✅

`yamllint -c .yamllint.yml .github/workflows/reusable_publish_oras.yml` exits `0`. `actionlint` also
exits `0`.

---

### Task 4 — Document downstream issue: vuln verification ✅

Issue [#173](https://github.com/complytime/org-infra/issues/173) is open. The `enable_verify_vuln`
boolean input pattern was **POC-validated** — added to `reusable_sign_and_verify.yml` in the test org
([sonupreetam/org-infra-tests](https://github.com/sonupreetam/org-infra-tests)) and confirmed working
with `enable_verify_vuln: false` in the caller workflow.

---

### Task 5 — Integrate spike findings (complytime-policies#10) ✅

Confirmed from spike and direct repo/source inspection:

- ✅ **Per-bundle publishing** — `reusable_publish_oras.yml` is compatible as-is; the caller
  (complytime-policies#7) handles the per-bundle matrix
- ✅ **Correct Gemara layer media types** — sourced from `complyctl/internal/complytime/consts.go`;
  `paths` input description in the workflow updated with correct examples
- ✅ **Actual bundle structure** documented in `plan.md` (3 bundles, layer counts, shared guidance blob)
- ✅ **Issue #172 updated** with two comments: spike alignment + POC success

---

### Task 6 — Self-review checklist

Before opening the PR to `complytime/org-infra`:

- [x] `reusable_publish_oras.yml` exists in `.github/workflows/`
- [x] All `uses:` are pinned to full SHA with `# vX.Y.Z` comment
- [x] Workflow-level permissions are all `none`
- [x] Job runs only when `github.ref_protected`
- [x] Outputs `digest`, `image`, `sha_tag` are wired through correctly
- [x] SLSA provenance step uses `subject-name` + `subject-digest` (not `subject-path`)
- [x] SBOM step uses `path:` input (not `image:`)
- [x] All env vars used in `run:` steps are set via `env:` block (no inline `${{ }}` interpolation)
- [x] `yamllint` exits `0`; `actionlint` exits `0`
- [x] Spec and plan files exist under `specs/004-reusable-publish-oras-workflow/`
- [x] End-to-end POC green: [run #24032400693](https://github.com/sonupreetam/image-publish-test/actions/runs/24032400693)
- [x] Issue #172 updated with media type corrections and POC result
- [ ] PR description references issue #172 with `Closes #172`
- [ ] PR description notes companion issue #173 (`enable_verify_vuln`) is a separate PR
