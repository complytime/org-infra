# Tasks

## 1. Add when guards to policy files

- [x] 1.1 Add `when` field to `compliance/ampel/branch-protection/block-force-push.json` after `id` and before `meta`, using `predicates.exists(p, p.predicate_type == '...branch-rules.yaml' || p.predicate_type == '...branch-protection.yaml')`. Verify the file is valid JSON with `jq . < block-force-push.json`.
- [x] 1.2 Add `when` field to `compliance/ampel/branch-protection/require-pull-request.json` with the same expression as 1.1. Verify valid JSON with `jq`.
- [x] 1.3 Add `when` field to `compliance/ampel/branch-protection/prevent-admin-bypass.json` with the same expression as 1.1. Verify valid JSON with `jq`.
- [x] 1.4 Add `when` field to `compliance/ampel/branch-protection/require-code-owner-review.json` with the same expression as 1.1. Verify valid JSON with `jq`.
- [x] 1.5 Add `when` field to `compliance/ampel/branch-protection/minimum-approvals.json` using `predicates.exists(p, p.predicate_type == '...branch-rules.yaml' || p.predicate_type == '...project-approvals.yaml')` (note: `project-approvals.yaml`, not `branch-protection.yaml`). Verify valid JSON with `jq`.

## 2. Add lint-policies Makefile target

- [x] 2.1 Add a `lint-policies` target to `Makefile` that iterates over `compliance/ampel/**/*.json`, skips files without a `when` field, and uses `jq` to verify every predicate type URL from `tenets[].predicates.types` appears in the `when.expression` string. Exit non-zero with a descriptive error naming the file and missing type if any are missing. Verify by running `make lint-policies` against the updated policy files (should pass).
- [x] 2.2 Wire `lint-policies` into the `lint` target by adding it to the dependency list (`lint: lint-yaml lint-python lint-policies`). Verify `make lint` runs all three sub-targets.

## 3. Validation

- [x] 3.1 Run `make lint` end-to-end and verify zero errors across all three lint sub-targets (yaml, python, policies).
- [x] 3.2 Temporarily remove one predicate type URL from a `when.expression` (e.g., in `block-force-push.json`) and run `make lint-policies`. Verify it exits non-zero and names the missing predicate type URL in the error output. Restore the file after validation.

<!-- spec-review: passed -->
<!-- code-review: passed -->
