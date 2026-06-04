## 1. Org-Ownership Detection (reusable workflow)

- [ ] 1.1 Add `is_org_owned` output to the `workflow_call` outputs block in `.github/workflows/reusable_dependabot_reviewer.yml`
- [ ] 1.2 Add `REPO_OWNER: "${{ github.repository_owner }}"` to the job-level env or to a new step env in `.github/workflows/reusable_dependabot_reviewer.yml`
- [ ] 1.3 Add a new step `Detect Org Ownership` (after `get_dep_info`) in `.github/workflows/reusable_dependabot_reviewer.yml` that extracts the first path segment of `DEP_NAME`, compares it to `REPO_OWNER`, and outputs `is_org_owned` (`true`/`false`)
- [ ] 1.4 Wire the `is_org_owned` step output through the job outputs and `workflow_call` outputs in `.github/workflows/reusable_dependabot_reviewer.yml`

## 2. Approval Logic Changes (consumer workflow)

- [ ] 2.1 Add `contents: write` permission to the `approve_dependabot_prs` job in `.github/workflows/ci_dependencies.yml` (alongside existing `pull-requests: write`)
- [ ] 2.2 Add the `is_org_owned` output consumption from `call_dependabot_reviewer` in `.github/workflows/ci_dependencies.yml`
- [ ] 2.3 Update the `Auto-approve if Confident` step condition in `.github/workflows/ci_dependencies.yml` to also approve when the dependency is org-owned, risk is not high, and review passes (without requiring release age)
- [ ] 2.4 Add a new step `Enable Auto-merge for Org-owned` in the `approve_dependabot_prs` job in `.github/workflows/ci_dependencies.yml` that runs `gh pr merge --auto --squash` when the dependency is org-owned, risk is not high, and review passes. Use `continue-on-error: true` and `GH_TOKEN: ${{ secrets.GITHUB_TOKEN }}`

## 3. PR Comment Update (consumer workflow)

- [ ] 3.1 Update the comment template in the `comment_on_dependabot_prs` job in `.github/workflows/ci_dependencies.yml` to add an `Ownership` row showing `org-owned` or `third-party`
- [ ] 3.2 Update the `Auto-approval` line in the comment template in `.github/workflows/ci_dependencies.yml` to reflect the three possible states: auto-approved with auto-merge (org-owned), auto-approved (third-party), or manual review required

## 4. Validation

- [ ] 4.1 Run `make lint` to verify all YAML changes pass yamllint
- [ ] 4.2 Verify all action `uses:` references in modified files remain SHA-pinned with inline version comments
- [ ] 4.3 Review the complete diff to confirm third-party approval logic is unchanged and no permissions are broader than required
