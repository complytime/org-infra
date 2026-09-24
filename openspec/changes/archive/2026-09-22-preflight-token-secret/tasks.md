## 1. Add optional token secret to workflow declaration

- [x] 1.1 Add `secrets:` block with `tag_push_token` (required: false) after the existing `inputs:` block in `reusable_release_preflight.yml`, with description: "Optional elevated token for tag creation. When provided, the tag event can trigger downstream workflows. WARNING: Do not use an elevated token in downstream workflows that re-invoke this preflight workflow, or you will create a recursive loop."
- [x] 1.2 Verify the `secrets:` block does not conflict with existing `inputs:` or `outputs:` blocks

## 2. Scope elevated token to tag-creation step

- [x] 2.1 Replace `GH_TOKEN: ${{ secrets.GITHUB_TOKEN }}` with `GH_TOKEN: ${{ secrets.tag_push_token != '' && secrets.tag_push_token || secrets.GITHUB_TOKEN }}` in the "Create and push tag" step's `env:` block
- [x] 2.2 Verify no other step references `secrets.tag_push_token` — confirm all steps that use `GH_TOKEN` still reference `secrets.GITHUB_TOKEN` directly, and steps without `GH_TOKEN` (e.g., "Check tag uniqueness") remain unaffected

## 3. Validation

- [x] 3.1 Run `yamllint` on the modified workflow file
- [x] 3.2 Verify the workflow file parses as valid GitHub Actions syntax (all required keys present, no duplicate keys)
- [x] 3.3 Confirm the header comment block reflects the new `tag_push_token` secret capability

## 4. YAML-structure test assertions

> _Test strategy: This is a declarative YAML-only change to a GitHub Actions
> workflow. There is no application code to unit-test. Coverage relies on static
> YAML-structure assertions that verify the spec scenarios against the modified
> workflow file. These assertions run as shell commands during validation._

- [x] 4.1 Assert `secrets.tag_push_token` exists with `required: false` in the workflow YAML
- [x] 4.2 Assert the fallback expression `secrets.tag_push_token != '' && secrets.tag_push_token || secrets.GITHUB_TOKEN` appears only in the "Create and push tag" step
- [x] 4.3 Assert no other step references `secrets.tag_push_token` (negative test)
- [x] 4.4 Assert the `description` field of `secrets.tag_push_token` contains the exact warning text specified in the spec

## 5. Update documentation

- [x] 5.1 Add a "Secrets" row to the `reusable_release_preflight.yml` Workflow Inputs Reference in `docs/RELEASE_WORKFLOWS.md` documenting the `tag_push_token` secret (required: false, description, fallback behavior)
- [x] 5.2 Add an example or note to the relevant adoption pattern in `docs/RELEASE_WORKFLOWS.md` showing how callers pass `secrets: tag_push_token: ${{ secrets.RELEASE_TOKEN }}` for downstream triggering
- [x] 5.3 Update the Preflight Validation table in `docs/RELEASE_PROCESS.md` to note the optional `tag_push_token` and its effect on downstream workflow triggering
