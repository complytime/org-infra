## Why

The ampel granular policies in `compliance/ampel/` use opaque, benchmark-coupled IDs (`BP-1.01` .. `BP-5.01`) that are not self-documenting. The directory structure (`policies/branch-protection-rules/BP-*.json`) is unnecessarily deep, and the CI workflow sources these files from `complytime-providers/testdata/` instead of from org-infra itself -- making the testdata directory the de facto production source of truth. This change centralizes the canonical policies here, adopts semantic IDs, and aligns the directory structure with future OCI-based distribution.

**Connected changes:**
- **complytime-providers** (`opsx/refactor-ampel-policy-ids`): Updates testdata fixtures to use new semantic IDs; adds recursive directory walking to `LoadGranularPolicies`.
- **complytime-policies** (GitHub issue): Updates Gemara catalog control/requirement IDs and policy assessment plan IDs to match the new semantic scheme.

## Non-goals

- Implementing OCI distribution for granular policies (future feature).
- Changing CEL expressions, predicate URLs, or assessment/error messages in the policy files.
- Modifying the `complytime.yaml` structure or the `complyctl get` command.

## What Changes

- **BREAKING**: Rename all granular policy IDs from positional numeric (`BP-1.01` .. `BP-5.01`) to semantic slugs (`require-pull-request`, `minimum-approvals`, `block-force-push`, `prevent-admin-bypass`, `require-code-owner-review`).
- Rename `meta.controls[].id` references from `BP-1` .. `BP-5` to semantic control IDs (`pull-request-enforcement`, `approval-requirements`, `force-push-restriction`, `admin-bypass-prevention`, `code-owner-enforcement`).
- Restructure directory from `compliance/ampel/policies/branch-protection-rules/` to `compliance/ampel/branch-protection/` (flatter, one group = one future OCI artifact).
- Delete the old monolithic `compliance/ampel/branch-protection-rules.json` (superseded by per-policy files, contains invalid JSON with trailing comma).
- Update `reusable_compliance.yml`: add an org-infra checkout step, change the `cp` source to `_org-infra/compliance/ampel/branch-protection/*`, and document the step as temporary pending OCI distribution.
- Update spec docs (`specs/003-github-branch-protection-workflow/quickstart.md` and `spec.md`) with new IDs and paths.

## Capabilities

### New Capabilities

- `semantic-ampel-policies`: Restructured ampel granular policy directory with semantic, benchmark-agnostic IDs and workflow updates to source policies from org-infra.

### Modified Capabilities

## Impact

- **`compliance/ampel/`**: Directory restructured; old files deleted, new files created with renamed IDs and filenames.
- **`reusable_compliance.yml`**: New checkout step for org-infra; changed `cp` source path. The `_providers` checkout remains needed for building the provider binary.
- **`specs/003-*/`**: Documentation updated with new IDs and paths.
- **Downstream workflows**: Consumer workflows calling `reusable_compliance.yml` are unaffected (the interface is unchanged -- same inputs, same behavior).
- **complytime-providers**: After this change, the workflow no longer copies policies from `_providers/cmd/ampel-provider/convert/testdata/policies/`. The testdata directory in complytime-providers becomes purely for tests.
