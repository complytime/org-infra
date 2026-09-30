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

  Spec traceability tags:
  [PC] = pinact-config spec
  [SV] = sha-verification spec
  [VF] = version-freshness spec

  Target action version: suzuki-shunsuke/pinact-action v3.0.0
  Commit SHA: 896d595f299e71d65b9d28349d6956abe144390a
-->

## 1. Configuration

- [x] 1.1 [P] [PC] Create `.pinact.yaml` in repo root with `min_age: { value: 3 }` and schema version
- [x] 1.2 [P] [PC] Add `.pinact.yaml` sync entry to `sync-config.yml` under `files_to_sync` (after existing config files section, before AI Tooling section)

## 2. Workflow Integration

- [x] 2.1 [SV] Add `pinact` job to `.github/workflows/reusable_ci.yml` with job-level permissions (`contents: read`) and `runs-on: ubuntu-latest`. Add an optional input `skip_pinact` (type: boolean, default: false) to `reusable_ci.yml` workflow inputs, and gate the pinact job with `if: ${{ !inputs.skip_pinact }}`
- [x] 2.2 [SV] Add checkout step to the `pinact` job (SHA-pinned `actions/checkout@3d3c42e5aac5ba805825da76410c181273ba90b1 # v7.0.1`, `persist-credentials: false`)
- [x] 2.3 [SV] Add verify step (hard gate): `suzuki-shunsuke/pinact-action@896d595f299e71d65b9d28349d6956abe144390a # v3.0.0` with `fix: "false"`, `verify: "true"`, `verify_min_age: "true"`, and `github_token: ${{ github.token }}`. The `min_age` threshold is read from `.pinact.yaml` (single source of truth)
- [x] 2.4 [VF] Add freshness step (warning): `suzuki-shunsuke/pinact-action@896d595f299e71d65b9d28349d6956abe144390a # v3.0.0` with `update: "true"`, `skip_push: "true"`, `github_token: ${{ github.token }}`, and `continue-on-error: true`. Note: this step runs only when the verify step passes (default `if: success()` condition), ensuring developers fix SHA integrity issues before receiving version staleness feedback
- [x] 2.5 [VF] Add diff-check step after freshness: `git diff` to detect outdated actions, emit `::warning` annotations with file path, current version, and latest version, restore workspace with `git checkout -- .`; set `if: always()`

## 3. Fix Existing Mismatches

- [x] 3.1 [SV] Run `pinact run --verify-comment` locally against all workflow files in `.github/workflows/` to identify existing version comment mismatches
- [x] 3.2 [SV] Fix any identified mismatches by running `pinact run --verify-comment` (auto-corrects comments) and commit the fixes

## 4. Testing

- [x] 4.1 [SV] [VF] Create `ci_test_pinact.yml` test workflow following the `ci_test_stale_reviews.yml` self-test pattern. Include at minimum: (a) a positive scenario with valid SHA-pinned actions that should pass verification, (b) a negative scenario with an invalid/mismatched version comment that should fail verification, (c) a freshness scenario with a non-latest action version that should produce a warning annotation without failing CI
- [x] 4.2 [SV] Verify the test workflow correctly fails on invalid SHAs and passes on valid SHAs by running locally or via CI

## 5. Validation

- [x] 5.1 Run `make lint` to verify `yamllint` passes on modified workflow and config files (covered by existing CI)
- [x] 5.2 Run `pinact run --check --verify-comment --min-age 3` locally to verify the hard gate passes on all current workflows
- [x] 5.3 Verify the freshness step produces warnings (not failures) for any actions that are behind latest
- [x] 5.4 Run `make sync-dry-run` to verify `.pinact.yaml` appears in the sync output for downstream repos

## 6. Documentation

- [x] 6.1 [P] Update `AGENTS.md` Active Technologies section to list `suzuki-shunsuke/pinact-action@v3.0.0` and pinact CLI
- [x] 6.2 [P] Update `AGENTS.md` Recent Changes section with an entry for this change
- [x] 6.3 [P] Add `CHANGELOG.md` entry documenting the new pinact CI hard gate and `.pinact.yaml` org-wide configuration (if `CHANGELOG.md` exists in repo root)
<!-- spec-review: passed -->
<!-- code-review: passed -->
