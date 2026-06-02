## 1. Directory Restructuring

- [x] 1.1 Create `compliance/ampel/branch-protection/` directory
- [x] 1.2 Create `compliance/ampel/branch-protection/require-pull-request.json` with `id` set to `require-pull-request` and `meta.controls[0].id` set to `pull-request-enforcement` (content from `policies/branch-protection-rules/BP-01.01-require-pull-request.json`, CEL/predicates/messages unchanged)
- [x] 1.3 Create `compliance/ampel/branch-protection/minimum-approvals.json` with `id` set to `minimum-approvals` and `meta.controls[0].id` set to `approval-requirements`
- [x] 1.4 Create `compliance/ampel/branch-protection/block-force-push.json` with `id` set to `block-force-push` and `meta.controls[0].id` set to `force-push-restriction`
- [x] 1.5 Create `compliance/ampel/branch-protection/prevent-admin-bypass.json` with `id` set to `prevent-admin-bypass` and `meta.controls[0].id` set to `admin-bypass-prevention`
- [x] 1.6 Create `compliance/ampel/branch-protection/require-code-owner-review.json` with `id` set to `require-code-owner-review` and `meta.controls[0].id` set to `code-owner-enforcement`

## 2. Cleanup

- [x] 2.1 Delete `compliance/ampel/branch-protection-rules.json` (old monolithic bundle)
- [x] 2.2 Delete `compliance/ampel/policies/branch-protection-rules/` directory and all its contents

## 3. Workflow Update

- [x] 3.1 Add org-infra checkout step to `.github/workflows/reusable_compliance.yml` (after the complytime-providers checkout, before the calling repository checkout): checkout `complytime/org-infra` to `_org-infra` path with `sparse-checkout: compliance/ampel`, pinned to same SHA as other checkout actions, `persist-credentials: false`
- [x] 3.2 Update the "Copy ampel policy files" step in `.github/workflows/reusable_compliance.yml`: change source from `_providers/cmd/ampel-provider/convert/testdata/policies/*` to `_org-infra/compliance/ampel/branch-protection/*`; add comment documenting the step as temporary pending OCI distribution

## 4. Spec Documentation

- [x] 4.1 Update `specs/003-github-branch-protection-workflow/quickstart.md`: replace all `BP-X.YY` policy IDs in the requirements table with new semantic IDs
- [x] 4.2 Update `specs/003-github-branch-protection-workflow/spec.md`: replace the granular policy source path reference from `cmd/ampel-plugin/convert/testdata/policies/*` to `compliance/ampel/branch-protection/`

## 5. Cross-Repository Coordination

- [x] 5.1 ~~File GitHub issue in `complytime/complytime-providers`~~ — covered by existing PR (`opsx/refactor-ampel-policy-ids` branch, nearly merged)
- [x] 5.2 ~~File GitHub issue in `complytime/complytime-policies`~~ — covered by parallel PR in progress

## 6. Validation

- [x] 6.1 Verify all 5 JSON policy files in `compliance/ampel/branch-protection/` are valid JSON with correct `id` fields
- [x] 6.2 Verify `compliance/ampel/branch-protection-rules.json` and `compliance/ampel/policies/` directory no longer exist
- [x] 6.3 Run yamllint on modified workflow file
- [x] 6.4 Verify the workflow checkout action SHA is pinned correctly with version comment

<!-- spec-review: passed -->
<!-- code-review: passed -->
