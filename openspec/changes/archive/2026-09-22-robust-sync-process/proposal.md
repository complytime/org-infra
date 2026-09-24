## Why

The organization's repository sync process has two operational problems that make it
unreliable and maintenance-heavy:

1. **Broken CI workflow**: The `sync_org_repositories.yml` workflow fails in GitHub Actions
   due to an authentication bug — the script calls the `/app` API endpoint with an
   installation access token instead of the required JWT, making it impossible to detect
   the authenticated actor. This forces maintainers to run the sync manually from their
   local machines.

2. **Hard-coded Dependabot directories**: The two static Dependabot template files
   (`dependabot.yml` and `dependabot_python.yml`) contain repository-specific directories
   (e.g., `/compass`, `/.github/actions/setup-complyctl`) that are pushed to all repos
   regardless of their actual structure. Additionally, the repository inventory in
   `sync-config.yml` is stale — several repos have been moved to `complytime-labs`,
   renamed, or deleted.

## What Changes

- **Replace fork-based sync with direct push**: Drop the fork workflow entirely. The sync
  script will clone target repos directly using the GitHub App token, create a feature
  branch, push changes, and open a PR. This eliminates actor detection, fork management,
  and the JWT/installation-token mismatch.
- **Add security guardrails for direct push**: Enforce branch name prefix restrictions,
  API endpoint allowlisting, no force push, and rely on branch protection on `main` as
  the primary security boundary.
- **Add duplicate PR detection**: Before creating a sync PR, check for existing open sync
  PRs to avoid duplicates.
- **Dynamic Dependabot generation**: Replace static template files with a `dependabot`
  section in `sync-config.yml` that defines common entries and per-repo overrides. The
  sync script generates a tailored `dependabot.yml` per repo, preserving unmanaged
  entries (ecosystems not managed by org-infra).
- **Clean up repository inventory**: Update `sync-config.yml` to reflect the current org
  structure — remove repos moved to `complytime-labs` or deleted, add new repos
  (`gemara-content-service`, `complytime`, `complytime-providers`), and correct the
  `complybeacon` → `complytime-collector-components` rename.
- **Clean up template files**: Remove `.github/dependabot_python.yml` (obsolete template).
  Rewrite `.github/dependabot.yml` to be org-infra's own config (not a sync template).
- **Fix workflow deprecation warning**: Update `actions/create-github-app-token` to use
  `client-id` instead of deprecated `app-id`.

## Non-goals

- Supporting multiple organizations in a single sync run. The script targets one org per
  invocation.
- Adding automated triggers (e.g., on push to `main`). The workflow remains manual
  (`workflow_dispatch`) only.
- Deep-merging Dependabot entry fields (e.g., preserving per-repo `ignore` blocks within
  managed ecosystems). Org-infra fully owns managed ecosystem entries.

## Capabilities

### New Capabilities

- `dynamic-dependabot`: Dynamic generation of per-repo `dependabot.yml` from common
  entries and per-repo overrides in `sync-config.yml`, with preservation of unmanaged
  ecosystem entries in target repos.
- `direct-push-sync`: Direct-push sync workflow replacing the fork-based approach, with
  security guardrails (branch name enforcement, API allowlist, duplicate PR detection).

### Modified Capabilities

_None. No existing spec-level requirements are changing._

## Impact

- **sync-config.yml**: Restructured — static dependabot entries removed from
  `files_to_sync`, new `dependabot` section added, repository inventory updated.
- **scripts/sync-org-repositories.py**: Major refactor — fork functions removed, direct
  push flow added, Dependabot generation logic added, duplicate PR detection added,
  API allowlist updated.
- **.github/workflows/sync_org_repositories.yml**: Simplified — fork-related comments
  and summary text updated, `client-id` replaces `app-id`.
- **.github/dependabot.yml**: Rewritten for org-infra's own use (github-actions,
  pre-commit, pip).
- **.github/dependabot_python.yml**: Deleted.
- **tests/test_sync_org_repositories.py**: Updated — fork-related tests removed, new
  tests for Dependabot generation, merge logic, branch validation, and duplicate PR
  detection.
- **GitHub App permissions**: Requires `contents: write` and `pull_requests: write` on
  target repos (currently only needs read). Branch protection on `main` in all target
  repos is the critical security boundary.
