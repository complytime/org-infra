# Repository Label Sync

Use the **Sync Repository Labels** workflow for label-only changes across
organization repositories. This complements repository file sync
(`sync_org_repositories.yml`) and org-level tooling in `complytime/.github`.

## Why a custom workflow

GitHub organization default labels apply only within a single org and do not
cover rename/cleanup of existing labels across many repositories. This workflow
reads `labels-policy.json` and applies three kinds of changes:

1. Ensure a shared set of standard labels exists everywhere.
2. Rename legacy labels only in repositories where they already exist.
3. Delete only explicitly-listed labels, leaving all other local labels alone.

This is useful when some labels must remain repo-specific and should not be
replicated across the organization.

Native org default labels are still useful for brand-new repositories inside
one org; this workflow is for cross-repo reconciliation and cleanup.

## Files

| File | Purpose |
| --- | --- |
| `labels-policy.json` | Source of truth for standard labels, renames, local-only preserves, and deletes |
| `scripts/sync-labels.py` | Applies the policy repo by repo via the GitHub API |
| `.github/workflows/sync_labels.yml` | Manual (`workflow_dispatch`) runner with dry-run support |

## Run the workflow

Go to **Actions → Sync Repository Labels → Run workflow**:

- **dry_run**: `true` to preview, `false` to apply (defaults to `true`)
- **repos**: comma-separated list of repos to target. Leave empty to apply to
  all repos except those excluded in `labels-policy.json`

Authentication uses the existing org-infra sync GitHub App secrets
(`SYNC_APP_CLIENT_ID`, `SYNC_APP_PRIVATE_KEY`) with `issues:write` so labels
can be created, renamed, and deleted.

## Assumptions encoded in the policy

- `private-sprint-sub-issue` is treated as **preserve**, not delete
- `docker` is renamed to `container`
- `question`, `to validate`, and `to validade` are consolidated into `validate`
- `complytime/complytime` and `roadmap` are excluded from org-wide apply by default

## Follow-ups

As discussed for multi-org label management (CT, UF, ASDLC), org-infra may later
host configs/workflows that cover those orgs as well. This first PR targets the
current complytime org policy and runner.
