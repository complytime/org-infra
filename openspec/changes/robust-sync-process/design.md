## Context

The `sync-org-repositories.py` script synchronizes configuration files and workflows
from org-infra to all repositories in the `complytime` GitHub organization. It is
triggered manually via `workflow_dispatch` from `sync_org_repositories.yml`.

**Current state:**

- The script uses a fork-based workflow: it forks each target repo under the GitHub
  App's account, pushes changes to the fork, then opens PRs from fork to upstream.
- This approach fails in CI because the script calls `GET /app` with an installation
  access token (which requires a JWT), making actor detection impossible.
- Two static Dependabot template files are copied verbatim to target repos, carrying
  repo-specific directories that don't exist in most targets.
- The repository inventory in `sync-config.yml` references repos that no longer exist
  in the `complytime` org (moved to `complytime-labs`, renamed, or deleted).

**Constraints:**

- Branch protection is enforced on `main` in all target repos (PR review required).
- The GitHub App installation token is short-lived (~1 hour) and auto-revoked.
- The sync workflow remains manual-only (`workflow_dispatch`).
- The script targets a single organization per invocation.

## Goals / Non-Goals

**Goals:**

- Make the sync workflow reliably executable from GitHub Actions CI.
- Eliminate the fork-based complexity and its authentication issues.
- Generate per-repo Dependabot configs dynamically while preserving repo-specific
  entries not managed by org-infra.
- Bring the repository inventory up to date with the current org structure.

**Non-Goals:**

- Multi-org support in a single run.
- Automated triggers (push-to-main, scheduled).
- Deep-merging of individual fields within managed Dependabot ecosystem entries.
- Managing Dependabot configs for repos in `complytime-labs`.

## Decisions

### D1: Direct push to target repos (replacing fork-based workflow)

The sync script will clone target repos directly using the GitHub App token, create
a feature branch, push changes, and open a PR via the GitHub API.

**Alternative considered: Fix the fork-based approach.** This would require resolving
the JWT vs installation-token mismatch in actor detection, and verifying that GitHub
App bot users can own forks and push to them. Rejected because: (a) GitHub's
documentation is ambiguous on App bot fork ownership, (b) forks add operational
complexity (sync drift, cleanup), and (c) direct push is simpler and the security
concern is addressed by branch protection.

**Security model (4 layers):**

1. **GitHub App permission scoping** — `contents: write` and `pull_requests: write`
   only, installed on specific repos. No admin, secrets, or workflow write access.
2. **Branch protection on `main`** — Human review required before merge. The App
   cannot push directly to `main`.
3. **Script-level guardrails:**
   - API endpoint allowlist (only `GET /repos`, `GET /pulls`, `GET /contents`,
     `POST /pulls`).
   - Branch name prefix enforcement (`sync-repo-standards-*`).
   - No `--force` push.
   - Only files listed in `sync-config.yml` are touched.
4. **Token lifetime** — Installation tokens expire in ~1 hour and are revoked in
   the workflow's post-job step.

### D2: Dynamic Dependabot generation with managed/unmanaged merge

The `dependabot` section in `sync-config.yml` defines:

- `common`: Entries applied to all repos (github-actions at `/`, pre-commit at `/`).
- `overrides`: Per-repo entries keyed by repository name. Each entry specifies a
  complete Dependabot ecosystem configuration.
- `exclude_repos`: Repos that should not receive any Dependabot config.

**Merge algorithm:**

1. Build the "managed set" — start with `common` entries, then apply `overrides` for
   the target repo. An override for the same `package-ecosystem` replaces the common
   entry entirely.
2. Read the existing `.github/dependabot.yml` from the target repo (if it exists).
3. Identify "unmanaged" entries — entries in the existing file whose
   `package-ecosystem` is not in the managed set.
4. Render the final file: `version: 2`, managed entries first, then unmanaged entries.
5. Compare against existing file — only include in the PR if content changed.

**Identity key:** `package-ecosystem`. Org-infra fully owns the configuration for any
ecosystem it manages. Repo-specific customizations for managed ecosystems (e.g.,
`ignore` blocks) must be added to the override in `sync-config.yml`.

**Alternative considered: Deep merge of entry fields.** This would preserve
repo-specific fields like `ignore` or `reviewers` within managed ecosystem entries.
Rejected because it adds significant complexity to the merge logic and makes the
config harder to audit centrally. Centralizing all managed-ecosystem config in
`sync-config.yml` is simpler and aligns with the Single Source of Truth principle.

**Alternative considered: Comment-based markers** (like `<!-- MANUAL ADDITIONS -->`).
Rejected because Dependabot's YAML is structured by ecosystem entries, making
ecosystem-level merge a natural and reliable boundary. Markers add fragility.

### D3: Duplicate PR detection before creation

Before creating a sync PR for a target repo, the script queries `GET /pulls?state=open`
and checks for an existing PR with the title `chore: sync repository standards`.

If found, the script skips PR creation and logs the existing PR URL. This prevents
accumulation of duplicate PRs when the sync is run multiple times before previous PRs
are merged.

**Alternative considered: Update existing PR by force-pushing to its branch.** This
would reuse the existing PR and update its contents. Rejected because force-push
violates the script's security guardrails and could discard review comments on the
existing PR. Creating a clean new PR after the old one is merged is safer.

### D4: Repository inventory cleanup

The `exclude_repos` list and per-file `exclude_repos` in `sync-config.yml` are updated
to reflect the current org structure:

- **Removed** (no longer in `complytime` org): `cac-content`,
  `compliance-to-policy-go`, `complytime-collector-distro`, `creme-brulee`,
  `oscal-content`, `oscal-sdk-go`, `compliance-to-policy-plugins`, `gemara2oscal`,
  `vagrant-boxes`, `complybeacon`.
- **Added to exclude**: `website` (managed independently), `nunya` (internal),
  `roadmap` (internal).
- **Added as sync targets**: `gemara-content-service` (Go), `complytime` (Go, soon),
  `complytime-providers` (Go, soon).
- **Updated**: `complybeacon` references become `complytime-collector-components`
  with updated Go module directories (`/proofwatch`, `/truthbeam` — no root `go.mod`,
  no `/compass`).

### D5: Static template cleanup

- `.github/dependabot_python.yml` is deleted (no longer needed as a sync template).
- `.github/dependabot.yml` is rewritten to serve as org-infra's own Dependabot config
  with three ecosystems: `github-actions` at `/`, `pre-commit` at `/`, `pip` at `/`.
- Both entries are removed from `files_to_sync` in `sync-config.yml`.

**Alternative considered: Keep template files alongside dynamic generation.** Rejected
because it creates two sources of truth for Dependabot configuration. The `dependabot`
section in `sync-config.yml` becomes the single source.

## Risks / Trade-offs

- **[Risk] App token has `contents: write` on target repos** — Broader permissions than
  the fork-based approach. Mitigation: branch protection on `main` prevents direct
  pushes; script enforces branch name prefix and no force push; App has no admin or
  workflow write permissions.

- **[Risk] Branch protection not configured on a target repo** — The App could
  theoretically push directly to `main`. Mitigation: all target repos are confirmed to
  have branch protection. The compliance policies in `compliance/` enforce this
  org-wide. Consider adding a pre-flight check in the script that verifies branch
  protection before pushing.

- **[Risk] Stale sync branches accumulate** — Timestamped branch names mean old
  branches persist if PRs are closed without merging. Mitigation: GitHub auto-deletes
  branches on PR merge (if configured). For closed-without-merge, periodic cleanup
  or a separate workflow can address this. Low priority since branches are lightweight.

- **[Trade-off] Managed ecosystems fully owned by org-infra** — Repos cannot customize
  fields like `ignore` within a managed ecosystem without updating `sync-config.yml`.
  This is intentional (Single Source of Truth) but adds friction for repo-specific
  needs. Acceptable because Dependabot config changes are infrequent.

## Open Questions

- Should the script verify branch protection status on each target repo as a pre-flight
  check before pushing? This would add safety but also an extra API call per repo.
