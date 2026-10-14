# Tasks

## 1. Add Org Precedent Step to Reusable Workflow

- [ ] 1.1 Add new outputs `org_precedent` and `precedent_detail` to the
  `workflow_call` outputs block and the `dependabot_review` job outputs
  in `.github/workflows/reusable_dependabot_reviewer.yml`. Verify by
  running `yamllint .github/workflows/reusable_dependabot_reviewer.yml`
  with zero errors.
- [ ] 1.2 Add step "Check Org Precedent" after the existing "Search GitHub
  for Dependency Usage" step in
  `.github/workflows/reusable_dependabot_reviewer.yml`. The step SHALL:
  (a) skip if `DEP_NAME` or `DEP_VERSION` is empty;
  (b) search for merged dependabot PRs matching the dep+version across the
  org using `gh search prs` with `--owner`, `--author dependabot[bot]`,
  `--merged`, `--review approved`, `--match title`, `--limit 5`;
  (c) filter out the current repository (`GITHUB_REPOSITORY`);
  (d) for each candidate, call the Reviews API to check for a human
  approval (`user.type != "Bot"` and `state == "APPROVED"`);
  (e) stop at the first valid precedent;
  (f) use the same retry pattern as the existing popularity search step
  (3 attempts, 15s/30s/45s backoff, 30s timeout);
  (g) output `org_precedent` (`true`/`false`) and `precedent_detail`
  (human-readable string with repo, PR number, reviewer) to
  `GITHUB_OUTPUT`.
  Verify by running `yamllint .github/workflows/reusable_dependabot_reviewer.yml`
  with zero errors and confirming the step references only `GITHUB_TOKEN`
  (no new secrets).

## 2. Extend Consumer Workflow Approval Logic

- [ ] 2.1 Add the new outputs (`org_precedent`, `precedent_detail`) to the
  `call_dependabot_reviewer` job's `needs` consumption in
  `.github/workflows/ci_dependencies.yml`. Add Path C to the
  `approve_dependabot_prs` job's `Auto-approve if Confident` step
  condition: `org_precedent == 'true'` AND `risk_level != 'high'` AND
  `review_conclusion == 'success'` AND `release_age_hours != '-1'` AND
  `release_age_hours >= MIN_RELEASE_AGE_HOURS`. Verify by running
  `yamllint .github/workflows/ci_dependencies.yml` with zero errors.
- [ ] 2.2 Extend the `Enable Auto-merge for Org-owned` step in
  `.github/workflows/ci_dependencies.yml` to also trigger when
  `org_precedent == 'true'` (in addition to `is_org_owned == 'true'`).
  Update the step name to reflect the broader scope (e.g., "Enable
  Auto-merge"). Verify the `if:` condition covers both org-owned and
  org-precedent cases.

## 3. Extend PR Comment

- [ ] 3.1 Add a new table row for "Org Precedent" to the
  `comment_on_dependabot_prs` job in
  `.github/workflows/ci_dependencies.yml`. Pass `org_precedent` and
  `precedent_detail` from the dependabot reviewer outputs into the
  step's `env:` block. The row SHALL display: status (found/none),
  and the precedent detail (repo, PR link, reviewer) when available.
  Verify by running `yamllint .github/workflows/ci_dependencies.yml`
  with zero errors.
- [ ] 3.2 Update the auto-approval summary line in the comment body to
  include the org-precedent approval path. When `org_precedent == 'true'`
  and all gates pass, the summary SHALL indicate approval with auto-merge
  via org precedent. Verify the expression logic handles all combinations
  (org-owned, precedent, neither).

## 4. Validation

- [ ] 4.1 Run `make lint` from the repository root and confirm zero lint
  errors across both modified workflow files.
- [ ] 4.2 Verify all action `uses:` references in the modified files remain
  SHA-pinned with inline version comments (no mutable tags introduced).
- [ ] 4.3 Verify that no new secrets are referenced in the modified
  workflows -- the precedent step SHALL use only `GITHUB_TOKEN` via
  `secrets.GITHUB_TOKEN`.
- [ ] 4.4 Verify that the workflow-level `permissions` in
  `reusable_dependabot_reviewer.yml` remain unchanged (`contents: read`,
  no writes added) and that no new permissions are added to
  `ci_dependencies.yml` beyond the existing job-level permissions.

## Workflow follow-up

- Archive the change after the project's review requirements are satisfied.
- Verify the archived result.
- Test the feature end-to-end by triggering a Dependabot PR in a repo where
  the same dependency version was already merged in another org repo. Confirm
  the PR comment shows precedent and auto-merge is enabled.
