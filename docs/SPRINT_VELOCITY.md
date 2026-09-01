# Sprint velocity report

How to generate the end-of-sprint report for the
[Compliance Automation planning](https://github.com/orgs/complytime/projects/14)
board, and where to find the output.

The report counts **Done** issues on each completed Iteration (sprint), then
averages those counts across closed sprints — by **Size**, **Organization**,
and **Milestone**. Typed user stories (`[Story]` title or `type:story`) are
counted separately.

GitHub Insights can draw one bar per sprint. It cannot compute an average
across sprints. This report does.

## Where the report lives

The report is **not** a view on the project board. It is produced by a GitHub
Actions workflow in `complytime/org-infra`.

1. Open [org-infra → Actions](https://github.com/complytime/org-infra/actions).
2. In the left sidebar, click **Report sprint velocity**.
3. Open the run you want (the latest, or the one from the sprint-close day).
4. On that run:
   - **Summary** — the full markdown report (tables and averages).
   - **Artifacts** — download `sprint-velocity.md` (same report) and
     `sprint-velocity.json` (machine-readable).

Artifacts expire with the workflow retention policy (GitHub default is 90
days unless org-infra is configured otherwise). Download them if you need
to keep a sprint snapshot.

Until this workflow is merged to `main`, it will not appear under Actions.

## How to run it (GitHub)

The workflow lives only in `org-infra`. It is not synced to other repos.
The filename `report_sprint_velocity.yml` follows the org-infra-only verb
prefix (`sync_`, `report_`), not `ci_` or `reusable_`.
It reuses the existing `PROJECT_SYNC_TOKEN` secret (project read).

1. Go to [org-infra → Actions → Report sprint velocity](https://github.com/complytime/org-infra/actions/workflows/report_sprint_velocity.yml).
2. Click **Run workflow**.
3. Run against `main` (or the branch that contains this workflow).
4. When the job finishes, open the run and read **Summary** / **Artifacts**
   as above.

Run this at sprint close. You can also run it mid-sprint: the open sprint
is listed as “Done so far” and is **not** included in the averages.

## How to run it (ask in Cursor)

You do not have to follow the GitHub or local steps yourself. In this
workspace, ask the agent to generate the sprint velocity report (for
example: “run the sprint report”). The agent runs
`scripts/report-sprint-velocity.py` with your GitHub token and pastes
the result in the chat.

## How to run it (local)

Needs a token that can read project `#14`:

```bash
cd org-infra
export GITHUB_TOKEN="$(gh auth token)"
pip install -r requirements.txt
python scripts/report-sprint-velocity.py --config project-sync-config.yml
```

That prints the report to the terminal. To write files instead:

```bash
python scripts/report-sprint-velocity.py \
  --config project-sync-config.yml \
  --output sprint-velocity.md \
  --json-output sprint-velocity.json
```

## What is counted

For each **completed** Iteration:

- Issues whose Status starts with `Done`
- Size (XS / S / M / L / XL)
- Organization
- Milestone

A completed sprint with no Done issues counts as **0**, so empty sprints do
not inflate velocity.

**Not in the averages**

- The open (current) sprint — shown separately
- Done issues with no Iteration (older board work from before sprints)
- Pull requests

Before any sprint has closed, the command still succeeds. You get the
current sprint snapshot and a note that averages appear after GitHub moves
an Iteration into `completedIterations` (when its date range ends). No
config change is required when that happens; run the same workflow again.

## Files

| File | Role |
|---|---|
| `scripts/report-sprint-velocity.py` | GraphQL read + markdown/JSON report |
| `scripts/lib/github_client.py` | Shared REST/GraphQL client |
| `scripts/lib/project_config.py` | Shared project owner/number config |
| `.github/workflows/report_sprint_velocity.yml` | Manual GitHub Actions trigger |
| `project-sync-config.yml` | Project owner and number |
