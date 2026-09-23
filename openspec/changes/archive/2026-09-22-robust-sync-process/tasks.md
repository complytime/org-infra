## 1. Configuration Cleanup

- [x] 1.1 Update `sync-config.yml` — remove repos no longer in `complytime` org from global `exclude_repos` (`cac-content`, `compliance-to-policy-go`, `complytime-collector-distro`, `creme-brulee`, `oscal-content`, `oscal-sdk-go`). Add new exclusions (`website`, `nunya`, `roadmap`). Update per-file `exclude_repos` to remove stale references (`complybeacon`, `vagrant-boxes`, `compliance-to-policy-plugins`, `gemara2oscal`).
- [x] 1.2 Add `dependabot` section to `sync-config.yml` — define `common` entries (github-actions, pre-commit), `overrides` per repo (complyctl, complytime-collector-components, complytime, complytime-providers, gemara-content-service, complyscribe, complytime-demos, complytime-policies), and `exclude_repos` for dependabot.
- [x] 1.3 Remove both static dependabot entries from `files_to_sync` in `sync-config.yml` (the `dependabot.yml` and `dependabot_python.yml` source/destination pairs).
- [x] 1.4 Delete `.github/dependabot_python.yml` (obsolete template file).
- [x] 1.5 Rewrite `.github/dependabot.yml` for org-infra's own use — three ecosystems: github-actions at `/`, pre-commit at `/`, pip at `/`.

## 2. Script — Remove Fork-Based Logic

- [x] 2.1 Remove `get_authenticated_actor()` function from `scripts/sync-org-repositories.py`.
- [x] 2.2 Remove `check_fork_exists()` function from `scripts/sync-org-repositories.py`.
- [x] 2.3 Remove `create_fork()` function from `scripts/sync-org-repositories.py`.
- [x] 2.4 Remove `delete_fork_branch()` function from `scripts/sync-org-repositories.py`.
- [x] 2.5 Update `main()` in `scripts/sync-org-repositories.py` — remove actor detection flow, pass token-based auth directly to `sync_repository()`.

## 3. Script — Implement Direct Push Flow

- [x] 3.1 Update `validate_github_api_request()` in `scripts/sync-org-repositories.py` — new allowlist: `GET /repos/{owner}/{repo}`, `GET /repos/{owner}/{repo}/pulls`, `POST /repos/{owner}/{repo}/pulls`, `GET /repos/{owner}/{repo}/contents/{path}`.
- [x] 3.2 Add `validate_branch_name()` function to `scripts/sync-org-repositories.py` — enforce `sync-repo-standards-` prefix.
- [x] 3.3 Add `check_existing_sync_pr()` function to `scripts/sync-org-repositories.py` — query `GET /pulls?state=open`, match by PR title `chore: sync repository standards`.
- [x] 3.4 Update `setup_git_credentials()` in `scripts/sync-org-repositories.py` — set remote URL with token directly for the target repo (no fork remote).
- [x] 3.5 Update `create_branch_and_commit()` in `scripts/sync-org-repositories.py` — add branch name validation before push, ensure no force flags.
- [x] 3.6 Rewrite `sync_repository()` in `scripts/sync-org-repositories.py` — implement direct clone, branch, sync files, generate dependabot, commit, push, check for existing PR, create PR flow.

## 4. Script — Dynamic Dependabot Generation

- [x] 4.1 Add `generate_dependabot_config()` function to `scripts/sync-org-repositories.py` — build managed set from common entries + repo-specific overrides.
- [x] 4.2 Add `merge_dependabot_entries()` function to `scripts/sync-org-repositories.py` — read existing `dependabot.yml` from cloned target repo, identify unmanaged entries (by `package-ecosystem`), combine managed + unmanaged, render final YAML.
- [x] 4.3 Integrate Dependabot generation into `sync_repository()` — call after static file sync, write generated file to `.github/dependabot.yml` in the cloned repo, include in changeset if different from existing.

## 5. Workflow Update

- [x] 5.1 Update `.github/workflows/sync_org_repositories.yml` — replace `app-id` with `client-id` in `actions/create-github-app-token` step. Update summary text to remove fork-related references.

## 6. Tests

- [x] 6.1 Update `TestValidateGithubApiRequest` in `tests/test_sync_org_repositories.py` — remove fork-related tests (`test_allowed_get_user`, `test_allowed_get_app`, `test_allowed_post_forks`, `test_allowed_delete_branch_ref`), add tests for new allowlist (`GET /pulls`, `GET /contents`).
- [x] 6.2 Add `TestValidateBranchName` class to `tests/test_sync_org_repositories.py` — test valid prefix accepted, invalid prefix rejected, edge cases (empty string, `main`).
- [x] 6.3 Add `TestGenerateDependabotConfig` class to `tests/test_sync_org_repositories.py` — test common-only output, common + override output, override replacing common for same ecosystem.
- [x] 6.4 Add `TestMergeDependabotEntries` class to `tests/test_sync_org_repositories.py` — test unmanaged entries preserved, no existing file produces managed-only output, managed entry replaces existing entry for same ecosystem.
- [x] 6.5 Add `TestCheckExistingSyncPr` class to `tests/test_sync_org_repositories.py` — test no existing PR returns false, existing PR with matching title returns true and URL.
- [x] 6.6 Update `TestLoadSyncConfig` in `tests/test_sync_org_repositories.py` — add test verifying `dependabot` section is present in config.

## 7. Validation

- [x] 7.1 Run `make lint` — verify zero yamllint and ruff issues across all modified files.
- [x] 7.2 Run `make test` — verify all tests pass including new test classes.
- [x] 7.3 Run `make sync-dry-run` or equivalent dry-run — verify script runs end-to-end without errors, reports expected file changes for target repos, and generates correct Dependabot configs.
