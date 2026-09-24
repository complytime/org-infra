## 1. Permissions Fix

- [x] 1.1 Remove `packages: write` and `id-token: write` from the `call_reusable_vuln_scan` job
  permissions in `.github/workflows/ci_security.yml`

## 2. Sync Config Schema

- [x] 2.1 Add `vars` key to the `ci_security.yml` entry in `sync-config.yml` with
  `enable_trivy_source` variable: `default: "false"`, `repos` map for complyctl, complytime,
  complytime-providers, complytime-collector-components, gemara-content-service, complyscribe

## 3. Sync Script Implementation

- [x] 3.1 Add `resolve_file_vars` function in `scripts/sync-org-repositories.py` that takes
  a file config dict and repo name, returns a dict of `{var_name: resolved_value}` pairs
- [x] 3.2 Add `apply_file_vars` function in `scripts/sync-org-repositories.py` that takes
  file content string and resolved vars dict, applies regex substitution for each var, logs
  a warning if a var pattern is not found, and returns the modified content
- [x] 3.3 Integrate var resolution into the `sync_repository` function's file processing loop:
  read source content, apply vars, use resolved content for comparison and writing
- [x] 3.4 Update dry-run output path to show resolved var values when vars are configured

## 4. Tests

- [x] 4.1 Add `TestResolveFileVars` class in `tests/test_sync_org_repositories.py`:
  test repo in overrides returns override value, test repo not in overrides returns default,
  test file config with no vars returns empty dict
- [x] 4.2 Add `TestApplyFileVars` class in `tests/test_sync_org_repositories.py`:
  test value substitution in workflow content, test no-match logs warning, test multiple vars,
  test content preservation (comments, SHA pins, indentation)
- [x] 4.3 Add integration test for var-aware file comparison: resolved content matches destination
  (no update), resolved content differs from destination (update needed)

## 5. Validation

- [x] 5.1 Run `make lint` and fix any issues in modified files
- [x] 5.2 Run `make test` and verify all tests pass (existing + new)
- [x] 5.3 Run `make sync-dry-run` to verify resolved values in output (if environment allows)
  _Note: Requires GITHUB_TOKEN — skipped in local environment (no token available)._
