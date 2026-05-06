## Why

`reusable_crapload_analysis.yml` has an unquoted `${{ inputs.new-function-threshold }}` shell variable assignment. This was identified as a pre-existing finding during the PR #224 review (convention pack SC-002 — external input validation), outside that PR's scope. No follow-up was created to address it.

The adjacent `BASELINE` and `EPSILON` assignments already use defensive quoting — this is the last remaining unquoted input interpolation in the workflow. While `workflow_call` inputs are caller-controlled and not directly exploitable, unquoted interpolation is inconsistent with the established pattern and violates the project's defensive security conventions.

## What Changes

- Quote the `NEW_FUNC_THRESHOLD` shell variable assignment in `reusable_crapload_analysis.yml` to match the quoting pattern used by `BASELINE` and `EPSILON`

## Capabilities

### New Capabilities

_None — this is a single-line defensive fix, not a new capability._

### Modified Capabilities

_None — no spec-level behavior changes._

### Removed Capabilities

_None._

## Impact

- **File**: `.github/workflows/reusable_crapload_analysis.yml` (line 154)
- **Downstream**: This reusable workflow is referenced cross-repository by consumer workflows (e.g., `ci_crapload.yml`) in all org repos. The fix propagates automatically on their next workflow run. Adding quotes around a numeric value does not change shell behavior, so no downstream breakage is expected
- **References**: PR #224 review comment by @hbraswelrh — [link](https://github.com/complytime/org-infra/pull/224#discussion_r2625741610)

## Constitution Alignment

Assessed against the Unbound Force org constitution.

### I. Autonomous Collaboration

**Assessment**: N/A — No change to artifact-based communication or self-describing outputs.

### II. Composability First

**Assessment**: N/A — No new dependencies or coupling introduced.

### III. Observable Quality

**Assessment**: PASS — Eliminates an inconsistency in defensive quoting, improving code hygiene.

### IV. Testability

**Assessment**: N/A — Behavioral no-op; workflow outputs remain identical.
