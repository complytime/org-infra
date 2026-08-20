# Evidence Locker MVP Reviewer Assignment

Automatically assigns the `evidence-locker-mvp-reviewers` GitHub team to
open issues and pull requests in the `complytime` organization whose
milestone title is **Evidence Locker MVP** (or **Internal Evidence Locker
MVP**).

CODEOWNERS cannot filter on milestones, so this is a scheduled org-infra
workflow rather than a CODEOWNERS rule. The workflow is **not** synced to
consumer repositories.

## Membership

Team membership is the source of truth and lives in
[`complytime/.github` `peribolos.yaml`](https://github.com/complytime/.github/blob/main/peribolos.yaml).

To add or remove reviewers:

1. Edit the `members` list on `evidence-locker-mvp-reviewers` in
   `peribolos.yaml`.
2. Merge that PR. Peribolos applies the team change.
3. The next assignment run reads the updated member list from
   `peribolos.yaml` on `main`. No workflow change is required.

Current members: `@hbraswelrh`, `@sedonnel`, `@trevor-vaughan`.

## What the automation does

On a 15-minute schedule and via manual `workflow_dispatch`:

1. Reads `milestone-reviewers-config.yml`
2. Loads `evidence-locker-mvp-reviewers` members from `peribolos.yaml`
3. Scans non-archived `complytime` repositories for matching open milestones
4. **Issues:** adds those members as assignees (does not remove anyone)
5. **Pull requests:** requests those members as reviewers (does not
   remove existing review requests)
6. Skips the item author so people are not assigned to review themselves

GitHub cannot assign a team as an issue assignee, so individuals from the
team are used. Changing the team later only affects new/unassigned items;
existing assignees and review requests are left alone.

## Files

| File | Role |
| --- | --- |
| `milestone-reviewers-config.yml` | Org, team slug, and milestone titles |
| `scripts/assign-milestone-reviewers.py` | Discovery + assignment |
| `.github/workflows/assign_milestone_reviewers.yml` | Schedule + manual trigger |

## Run the workflow

Go to **Actions → Assign Evidence Locker MVP Reviewers → Run workflow**:

- **dry_run**: `true` to preview, `false` to apply (manual runs default to `true`)

Scheduled runs always apply.

Authentication uses the org-infra sync GitHub App
(`SYNC_APP_CLIENT_ID`, `SYNC_APP_PRIVATE_KEY`) with `contents:read`,
`issues:write`, and `pull-requests:write`.

## Local dry-run

```bash
export GITHUB_TOKEN="$(gh auth token)"
python3 scripts/assign-milestone-reviewers.py \
  --config milestone-reviewers-config.yml \
  --peribolos-file /path/to/peribolos.yaml \
  --dry-run
```

## Adding another milestone-based reviewer team

Add a new closed team in `peribolos.yaml`, then either extend
`milestone-reviewers-config.yml` (if this script is generalized) or add a
second config/workflow pair. Prefer a peribolos team over a hardcoded
login list so membership stays editable in one place.
