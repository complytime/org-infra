# Tasks

## T1: Delete `scripts/compare-crapload.sh`
- [x] Remove the file entirely (315 lines)
- Files: `scripts/compare-crapload.sh`

## T2: Modify `reusable_crapload_analysis.yml`
- [x] Add step to write temporary `.gaze.yaml` from workflow inputs
      (only when consumer repo has no `.gaze.yaml`)
- [x] Keep "Run Gaze analysis" step (gaze report) for quality data
- [x] Remove jq path normalization (gaze emits relative paths)
- [x] Replace "Compare against baseline" step with gaze crap
      --baseline invocation and inline jq output extraction
- [x] Handle no-baseline case: generate quickstart comment inline
- [x] Build PR comment body via jq + heredoc — implemented in external
      script (`generate-crapload-comment.sh`) to avoid actionlint hang
      on large inline bash blocks
- [x] Preserve `<!-- crapload-analysis-marker -->` in comment body
- [x] Verify all 5 workflow outputs are correctly emitted
- Files: `.github/workflows/reusable_crapload_analysis.yml`

## T3: Modify `tests/test_crapload_package_resolution.py`
- [x] Delete `TestCompareCrapload` class (lines 273-475, 5 tests)
- [x] Delete `_MINIMAL_SUMMARY` constant if only used by that class
- [x] Keep `TestCrapLoadPackageResolution` and
      `TestWorkflowInputValidation` unchanged
- Files: `tests/test_crapload_package_resolution.py`

## T4: Modify `ci_test_crapload.yml`
- [x] Remove `scripts/compare-crapload.sh` from `pull_request.paths`
- [x] Remove `scripts/compare-crapload.sh` from `push.paths`
- Files: `.github/workflows/ci_test_crapload.yml`

## T5: Update `specs/001-crapload-workflow/quickstart.md`
- [x] Update baseline generation instructions to use `gaze crap`
- [x] Remove stale `post-comment: false` input reference
- Files: `specs/001-crapload-workflow/quickstart.md`

## T6: Update `specs/001-crapload-workflow/data-model.md`
- [x] Remove `baseline-lookup.tsv` from Intermediate Artifacts
- [x] Remove stale `post-comment` input from Workflow Inputs table
- [x] Update `crapload-current.json` description to reference
      `gaze crap` output
- Files: `specs/001-crapload-workflow/data-model.md`

## T7: Documentation gate
- [x] Add entry to `CHANGELOG.md`
- [x] Verify `AGENTS.md` needs no updates
- Files: `CHANGELOG.md`, `AGENTS.md`

## T8: Validation
- [x] Run `make lint` (yamllint + ruff)
- [x] Run `make test` (pytest -- verify remaining tests pass)
- [x] Run `/review-council` before PR submission
