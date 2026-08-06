# Compliance Automation Project Board Sync

Automates keeping the private
[Compliance Automation planning](https://github.com/orgs/complytime/projects/14)
board populated with open issues and pull requests from:

| Organization | Selection |
|---|---|
| `Agentic-SSDLC` | All repositories |
| `complytime` | All repositories **except** `roadmap` and `complytime` |
| `unbound-force` | All repositories |

Archived repositories are skipped by default.

## What the automation does

On a daily schedule (and via manual `workflow_dispatch`):

1. Discovers repositories from `project-sync-config.yml`
2. Links each repository to project `#14` (idempotent)
3. Collects open issues and open PRs
4. Adds any missing items to the board with **Status = Backlog**

The workflow lives only in `org-infra` (it is **not** synced out to consumer repos).

| File | Role |
|---|---|
| `project-sync-config.yml` | Orgs, exclusions, and project target |
| `scripts/sync-project-board.py` | Discovery + GraphQL mutations |
| `.github/workflows/sync_project_board.yml` | Schedule + manual trigger |

## Why a PAT (not the sync GitHub App)

GitHub App installation tokens are scoped to a **single** organization.
Adding an issue from `Agentic-SSDLC` or `unbound-force` onto a project owned
by `complytime` requires a credential that can see all three orgs and write
to the project. Use a classic or fine-grained personal access token (or a
machine-user token) stored as `PROJECT_SYNC_TOKEN`.

## One-time setup

### 1. Create the token

**Classic PAT** (simplest for multi-org):

- Scopes: `repo`, `read:org`, `project`
- The token owner must be able to access private repos in all three orgs and
  edit project `#14`

**Fine-grained PAT** alternative:

- Resource owner / repository access covering the three orgs (or all repos the
  bot can see)
- Permissions: Issues (read), Pull requests (read), Metadata (read)
- Organization permission for `complytime`: **Projects = Read and write**

### 2. Add the repository secret

In `complytime/org-infra` → Settings → Secrets and variables → Actions:

- Name: `PROJECT_SYNC_TOKEN`
- Value: the PAT from step 1

### 3. Run an initial backfill

Actions → **Sync Compliance Automation Project Board** → Run workflow

- Leave `dry_run` checked first to validate discovery
- Re-run with `dry_run` unchecked to add items

Optional: set `orgs` to a single org (for example `complytime`) to stage the rollout.

## Local dry-run

```bash
export GITHUB_TOKEN="$(gh auth token)"   # needs project write for apply mode
pip install -r requirements.txt
python scripts/sync-project-board.py --config project-sync-config.yml --dry-run
```

## Changing scope

Edit `project-sync-config.yml`:

- Add/remove orgs under `organizations`
- Adjust `exclude_repos`
- Toggle `sync.issues` / `sync.pull_requests`
- Change `project.default_status` (must match a Status option on the board)
