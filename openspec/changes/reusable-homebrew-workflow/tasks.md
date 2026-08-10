## 1. Scaffold Reusable Workflow

- [x] 1.1 Create `.github/workflows/reusable_release_homebrew.yml` with `on: workflow_call` trigger, header comment block, and `workflow_call` inputs (`tag`, `project_name`, `description`, `binary_name`, `tap_repo`, `go_main_path`, `ldflags_module`, `homepage`)
- [x] 1.2 Add `secrets:` block for `app_client_id` and `app_private_key` (both required)
- [x] 1.3 Set top-level `permissions: {}` and job-level `permissions: { contents: read }`

## 2. Core Implementation Steps

- [x] 2.1 Add tag format validation step in `.github/workflows/reusable_release_homebrew.yml` with defense-in-depth regex check (`^v[0-9]+\.[0-9]+\.[0-9]+(-[a-zA-Z0-9.]+)?$`)
- [x] 2.2 Add source tarball download step with curl retry logic and HTTP status validation in `.github/workflows/reusable_release_homebrew.yml`
- [x] 2.3 Add SHA256 computation step with 64-char hex validation in `.github/workflows/reusable_release_homebrew.yml`
- [x] 2.4 Add formula generation step via bash heredoc with direct variable interpolation (no sed) in `.github/workflows/reusable_release_homebrew.yml`
- [x] 2.5 Add GitHub App token generation step using `actions/create-github-app-token` (SHA-pinned) with scoped `repositories:` and `permission-contents: write` in `.github/workflows/reusable_release_homebrew.yml`

## 3. Quality Gate and Push

- [x] 3.1 Add Homebrew installation step and `brew audit --strict --formula` validation in `.github/workflows/reusable_release_homebrew.yml`
- [x] 3.2 Add tap clone, formula copy, commit, and push step using `gh` CLI with env-var token (never persisted in git config) in `.github/workflows/reusable_release_homebrew.yml`
- [x] 3.3 Add idempotent re-run handling (exit 0 with message when no changes to commit) in `.github/workflows/reusable_release_homebrew.yml`

## 4. CI Test Workflow

- [x] 4.1 Create `.github/workflows/ci_test_homebrew.yml` with PR trigger filtered to `.github/workflows/*homebrew*` path changes
- [x] 4.2 Add test job that generates a formula with test inputs and validates it with `brew audit --strict` on macOS runner

## 5. Validation

- [x] 5.1 Run `yamllint` on both new workflow files and verify no errors
- [x] 5.2 Verify all action `uses:` references are SHA-pinned with `# vX.Y.Z` comments
- [x] 5.3 Run `make lint` to confirm full lint suite passes
