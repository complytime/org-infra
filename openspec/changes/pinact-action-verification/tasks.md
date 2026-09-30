<!--
  [P] marks tasks eligible for parallel execution.
  Add [P] when a task: (a) touches different files from
  other [P] tasks in the group, (b) has no dependency
  on prior tasks in the group, (c) can safely execute
  without ordering constraints.
  Do NOT add [P] when tasks modify the same file —
  parallel workers will cause merge conflicts.
  Tasks without [P] run sequentially first, then [P]
  tasks run in parallel.
-->

## 1. Configuration

- [ ] 1.1 [P] Create `.pinact.yaml` in repo root with `min_age: { value: 3 }` and schema version
- [ ] 1.2 [P] Add `.pinact.yaml` sync entry to `sync-config.yml` under `files_to_sync` (after existing config files section, before AI Tooling section)

## 2. Workflow Integration

- [ ] 2.1 Add `pinact` job to `.github/workflows/reusable_ci.yml` with job-level permissions (`contents: read`) and `runs-on: ubuntu-latest`
- [ ] 2.2 Add checkout step to the `pinact` job (SHA-pinned `actions/checkout`, `persist-credentials: true`)
- [ ] 2.3 Add verify step (hard gate): `suzuki-shunsuke/pinact-action` with `fix: "false"`, `verify: "true"`, `min_age: "3"`, `verify_min_age: "true"`, and `github_token: ${{ github.token }}`
- [ ] 2.4 Add freshness step (warning): `suzuki-shunsuke/pinact-action` with `update: "true"`, `skip_push: "true"`, and `continue-on-error: true`
- [ ] 2.5 Add diff-check step after freshness: `git diff` to detect outdated actions, emit `::warning` annotations, restore workspace with `git checkout -- .`; set `if: always()`

## 3. Fix Existing Mismatches

- [ ] 3.1 Run `pinact run --verify-comment` locally against all workflow files in `.github/workflows/` to identify existing version comment mismatches
- [ ] 3.2 Fix any identified mismatches by running `pinact run --verify-comment` (auto-corrects comments) and commit the fixes

## 4. Validation

- [ ] 4.1 Run `make lint` to verify `yamllint` passes on modified workflow and config files
- [ ] 4.2 Run `pinact run --check --verify-comment --min-age 3` locally to verify the hard gate passes on all current workflows
- [ ] 4.3 Verify the freshness step produces warnings (not failures) for any actions that are behind latest
- [ ] 4.4 Run `make sync-dry-run` to verify `.pinact.yaml` appears in the sync output for downstream repos
