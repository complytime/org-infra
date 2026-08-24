# Sprint velocity report

Builds a completed-sprint average from the
[Compliance Automation planning](https://github.com/orgs/complytime/projects/14)
board so it is ready once Iterations start closing.

GitHub Insights can chart one bar per sprint. It cannot compute “average Done
issues per sprint.” This report does.

## What it measures

For each **completed** Iteration:

- Done issues (Status starts with `Done`)
- Typed user stories (`[Story]` title or `type:story`)
- Size (XS–XL), Organization, and Milestone

Then it averages those counts across completed sprints. A completed sprint
with no Done issues counts as **0**, so empty sprints do not inflate velocity.

**Excluded from averages**

- The open sprint (shown separately as “Done so far”)
- Done issues with no Iteration (older board work)
- Pull requests

## Run it

The workflow lives only in `org-infra` (it is not synced to consumer repos).
It reuses `PROJECT_SYNC_TOKEN` from board sync.

Actions → **Report sprint velocity** → Run workflow

The job summary is the markdown report. Artifacts `sprint-velocity.md` and
`sprint-velocity.json` are attached to the run.

Locally (needs a token that can read project `#14`):

```bash
export GITHUB_TOKEN="$(gh auth token)"
pip install -r requirements.txt
python scripts/report-sprint-velocity.py --config project-sync-config.yml
```

Add `--json-output sprint-velocity.json` to also write machine-readable averages.

## Before any sprint has closed

The command still succeeds. You get the current sprint snapshot and a note
that averages appear after GitHub moves an Iteration into
`completedIterations` (when its date range ends). Re-run at each sprint close;
no config change is required.

## Files

| File | Role |
|---|---|
| `scripts/report-sprint-velocity.py` | GraphQL read + markdown/JSON report |
| `.github/workflows/report_sprint_velocity.yml` | Manual trigger |
| `project-sync-config.yml` | Project owner and number |
