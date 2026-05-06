## Context

`reusable_crapload_analysis.yml` runs CRAP score regression detection across org repos. In the `compare` step, shell variables are assigned from `workflow_call` inputs. Two of the three input-derived variables (`BASELINE`, `EPSILON`) use defensive quoting. The third (`NEW_FUNC_THRESHOLD`) does not.

This inconsistency was flagged as a pre-existing finding during the PR #224 review (convention pack SC-002 — external input validation) but was outside that PR's scope. No follow-up was created.

## Goals / Non-Goals

**Goals:**

- Quote `NEW_FUNC_THRESHOLD=${{ inputs.new-function-threshold }}` to match the established pattern
- Eliminate the last unquoted input interpolation in the workflow

**Non-Goals:**

- Auditing other reusable workflows for similar patterns
- Changing input types, defaults, or workflow behavior
- Refactoring the shell script structure

## Decisions

### Decision 1: Add double quotes around the interpolation

**Change:**
```diff
-          NEW_FUNC_THRESHOLD=${{ inputs.new-function-threshold }}
+          NEW_FUNC_THRESHOLD="${{ inputs.new-function-threshold }}"
```

**Alternative A considered:** Leave as-is since the input is `type: number` and caller-controlled.

**Rejected because:** Inconsistency with adjacent lines (`BASELINE` and `EPSILON` are quoted). Defensive quoting is a convention in this repo and costs nothing. The PR #224 reviewer specifically flagged this for follow-up.

**Alternative B considered:** Refactor to use `env:` block indirection to pass inputs to the shell (as established in the `release-workflow` spec, per GitHub Security Lab guidance).

**Rejected because:** The inputs are `workflow_call` caller-controlled (not from untrusted sources like PR titles), and the quoting fix achieves consistency with adjacent lines at minimal cost. A broader refactor to `env:` blocks could be a separate change.

## Risks / Trade-offs

- **Risk:** None. Quoting a numeric shell variable assignment is a behavioral no-op.
- **Trade-off:** None. The change is one character pair (`"..."`) on a single line.
