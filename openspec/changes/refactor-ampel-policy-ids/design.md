## Context

The `compliance/ampel/` directory contains granular ampel policy JSON files used for automated branch protection scanning. These files define CEL expressions evaluated by the ampel tool against in-toto attestations collected by snappy.

Currently, the directory has two layers of content:
- An old monolithic `branch-protection-rules.json` with `OSPS-*/MYORG-*` IDs, GitHub-only CEL, and invalid JSON (trailing comma). This file is not used by the CI workflow.
- A newer `policies/branch-protection-rules/` subdirectory with per-policy `BP-*.json` files supporting GitHub+GitLab. These are identical to the copies in `complytime-providers/testdata/`.

The `reusable_compliance.yml` workflow sources policies from `complytime-providers/testdata/`, not from org-infra's own `compliance/` directory. This makes a test fixtures directory the de facto production source of truth.

## Goals / Non-Goals

**Goals:**

- Establish org-infra as the canonical source of granular ampel policies.
- Replace opaque `BP-X.YY` IDs with semantic, benchmark-agnostic slugs.
- Flatten the directory structure to align with future OCI artifact boundaries.
- Update the CI workflow to self-source policies.
- Clean up the old monolithic bundle.
- Update spec documentation.

**Non-Goals:**

- Implementing OCI-based distribution for granular policies.
- Changing CEL expressions, predicate URLs, or assessment/error messages.
- Modifying the workflow interface (inputs, secrets, outputs).
- Changing the `complytime.yaml` format or `complyctl` behavior.

## Decisions

### 1. ID Naming Convention

**Decision**: Use the Gemara semantic model distinction. Control IDs are noun-phrases describing the safeguard area. Requirement IDs (which become the policy JSON `id` field) are verb-phrases describing the verifiable condition.

| Old | New Policy ID (Requirement) | New Control Ref |
|-----|---------------------------|-----------------|
| `BP-1.01` | `require-pull-request` | `pull-request-enforcement` |
| `BP-2.01` | `minimum-approvals` | `approval-requirements` |
| `BP-3.01` | `block-force-push` | `force-push-restriction` |
| `BP-4.01` | `prevent-admin-bypass` | `admin-bypass-prevention` |
| `BP-5.01` | `require-code-owner-review` | `code-owner-enforcement` |

OSPS framework references remain unchanged (`"framework": "OSPS", "class": "OSPS-QA", "id": "07"`).

**Alternative rejected**: Keeping `BP-X.YY` but adding human-readable filenames only. This leaves the matching key opaque in logs, scan reports, and workflow summaries.

### 2. Directory Structure

**Decision**: `compliance/ampel/branch-protection/<slug>.json` (one level of grouping by domain).

```
compliance/ampel/
  branch-protection/
    require-pull-request.json
    minimum-approvals.json
    block-force-push.json
    prevent-admin-bypass.json
    require-code-owner-review.json
```

Each subdirectory under `compliance/ampel/` maps to one future OCI artifact (e.g., `ampel-content-branch-protection`).

**Alternative rejected**: Fully flat (`compliance/ampel/*.json`). Loses grouping when multiple policy categories exist. Would require renaming files or adding prefixes to distinguish categories.

**Alternative rejected**: Keeping the current depth (`policies/branch-protection-rules/`). The extra `policies/` nesting adds no value and the `branch-protection-rules` name is redundant with the file content.

### 3. Workflow Checkout Strategy

**Decision**: Add a 4th checkout step for org-infra with `sparse-checkout: compliance/ampel` to minimize checkout footprint.

```yaml
- name: Checkout org-infra (policy source)
  uses: actions/checkout@de0fac2e4500dabe0009e67214ff5f5447ce83dd # v6.0.2
  with:
    repository: complytime/org-infra
    path: _org-infra
    sparse-checkout: compliance/ampel
    persist-credentials: false
```

The `_providers` checkout remains for building the provider binary. The `cp` step becomes:

```yaml
- name: Copy ampel policy files
  # TEMPORARY: Manual staging until provider content is distributed
  # via OCI (see: complyctl provider content fetch feature).
  run: |
    mkdir -p .complytime/ampel/granular-policies
    cp _org-infra/compliance/ampel/branch-protection/* \
       .complytime/ampel/granular-policies/
```

**Alternative rejected**: Embedding policies in the provider binary or OCI image. This is the future solution but requires `complyctl` feature work not yet available.

**Alternative rejected**: Using `actions/checkout` without `sparse-checkout`. The full org-infra checkout is unnecessarily large for this purpose.

### 4. Old Monolithic Bundle Cleanup

**Decision**: Delete `compliance/ampel/branch-protection-rules.json` entirely.

**Rationale**: It is superseded by the per-policy files, uses a different (older) ID scheme, only supports GitHub, has simpler CEL expressions, and contains invalid JSON (trailing comma on line 7). No code or workflow references it.

**Alternative rejected**: Updating it to match the new scheme. The per-policy structure is the correct format for the ampel tool. A monolithic bundle would need to be regenerated at runtime anyway (`MergeToBundle`), making a static monolith redundant.

## Risks / Trade-offs

- **Temporary breakage window**: Between this change landing and the `complytime-policies` Gemara update, the Gemara policy bundle (published OCI artifact) will still reference old `BP-X.YY` requirement IDs while the canonical policies use new IDs. The workflow's `cp` + generate + scan pipeline will work correctly only after the Gemara bundle is republished with new IDs. Mitigation: merge `complytime-policies` Gemara update first (republishing the OCI bundle with new semantic IDs), then merge this org-infra change second. This eliminates the breakage window entirely. If the strict ordering is not feasible, the breakage affects only the `complyctl generate` mapping step -- the scan still executes and produces results, but requirement-to-policy matching may be incomplete during the mismatch window.
- **4th checkout step**: Adds ~5-10 seconds to workflow runtime. Mitigation: `sparse-checkout` limits the checkout to `compliance/ampel/` only.
- **Spec doc updates**: The existing `specs/003-github-branch-protection-workflow/` docs reference old IDs and paths. These are historical spec artifacts. Mitigation: update the specific references while preserving the overall document structure.
