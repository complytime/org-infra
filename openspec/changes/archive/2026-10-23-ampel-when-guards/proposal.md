# Proposal

## Why

When a merged ampel policy bundle contains policies targeting different predicate
types (e.g., branch-rules + check-runs), policies whose declared predicate types
do not match the attestation being evaluated produce `FAIL` with "required
attestations missing to verify subject" instead of `SKIP`. This blocks
multi-predicate-type policy bundles including the merge readiness demo
(complytime-demos#97). Ampel 1.4.2 supports `when:` gate predicates that allow
policies to cleanly `SKIP` when their required evidence types are not present.

Closes #685.

## What Changes

- Add a `"when"` field to each of the 5 branch-protection policy files in
  `compliance/ampel/branch-protection/` so they produce `SKIP` instead of `FAIL`
  when their required predicate types are not available. The expression uses
  `predicates.exists()` filtered by `predicate_type` (not `size(predicates) > 0`,
  which is always true when any attestation exists).
- Add a `lint-policies` Makefile target that validates `when` expression
  consistency with tenet predicate types across all policy files. Wire it into the
  existing `make lint` target.

## Non-goals

- Changes to ampel itself (upstream, already done in 1.4.2).
- Provider-side SKIP handling (complytime-providers#200, separate repo).
- The merge readiness demo (complytime-demos#97, separate repo).
- Adding `when` guards to future policy domains -- only branch-protection is in
  scope. Future domains will follow the pattern established here.

## Capabilities

### New Capabilities

_None._

### Modified Capabilities

- `semantic-ampel-policies`: Add requirement that policies include `when` guards
  with expressions matching their tenet predicate types, and that a lint check
  validates this consistency.

## Impact

- **Policy files**: 5 JSON files in `compliance/ampel/branch-protection/` gain a
  `when` field. No existing fields are modified or removed.
- **Build tooling**: `Makefile` gains a `lint-policies` target. The existing `lint`
  target is updated to include it. Requires `jq` to be installed (already available
  on CI runners and standard dev setups).
- **Downstream**: No sync impact -- these policy files are not in `sync-config.yml`.
- **Dependencies**: Requires ampel >= 1.4.2 (already released) for `when` gate
  support and `--allow-skip` flag.
