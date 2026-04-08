# Tasks: Robust Dependabot Auto-Approval

**Input**: Design documents from `/specs/005-robust-dependabot-approval/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, quickstart.md

**Tests**: Not requested in the feature specification. Validation is via `make lint` and manual workflow runs.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing. US4 (extraction robustness) is foundational because it produces outputs consumed by all other stories. US3 (release age) must complete before US1 (auto-approval) since the approval condition depends on `release_age_hours`.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3, US4)
- Include exact file paths in descriptions

---

## Phase 1: Foundational - US4 Robust Dependency Information Extraction (Priority: P1)

**Goal**: Replace the fragile 112-line diff-parsing extraction step with a robust ~30-line metadata-first approach. Produce reliable outputs (`risk_level`, `updates_count`, `dep_name`, `dep_version`, `release_age_hours`) for all downstream jobs.

**Independent Test**: Trigger the workflow on a dependabot PR that changes a composite action file (e.g., in `.github/actions/`). Verify that dependency name, version, and risk level are correctly extracted and all downstream jobs execute successfully.

### Implementation for US4

- [x] T001 [US4] Rewrite the "Get Dependency Information" step in .github/workflows/reusable_dependabot_reviewer.yml — remove `set -e` (line 46), replace the 112-line bash script (lines 46-157) with a ~30-line implementation: (1) parse `dependency-name`, `dependency-version`, `update-type` from the commit body `updated-dependencies` block using `grep`/`sed`, (2) simplified diff enrichment to extract SHA-pinned `uses:` refs for `USES_QUERY` (single grep, no nested loops, no temp files), (3) keep title/body fallback for `dep_name` and versions when metadata is absent. All operations must use `|| true` to prevent crashes. Export `DEP_NAME`, `DEP_VERSION`, `FROM_VERSION`, `TO_VERSION`, `UPDATE_TYPE`, `USES_QUERY` to `$GITHUB_ENV`.
- [x] T002 [US4] Rewrite the "Classify Risk Based on Semantic Version" step in .github/workflows/reusable_dependabot_reviewer.yml — when `UPDATE_TYPE` env var is set (from commit metadata), use a `case` statement to map directly (`*semver-major*` → `high`, `*semver-minor*` → `medium`, `*semver-patch*` → `low`). Fall back to the existing semver comparison of `FROM_VERSION`/`TO_VERSION` only when `UPDATE_TYPE` is empty. Default to `high` when neither method yields a result.
- [x] T003 [US4] Update the job `outputs` section and `workflow_call.outputs` in .github/workflows/reusable_dependabot_reviewer.yml — add `dep_name`, `dep_version`, and `release_age_hours` outputs alongside existing `risk_level` and `updates_count`. Wire each to the corresponding step output. Note: `release_age_hours` output is wired here but the step that populates it is created in T005 (Phase 2).
- [x] T004 [US4] Simplify the "Search GitHub for Dependency Usage" step in .github/workflows/reusable_dependabot_reviewer.yml — wrap the `gh search code` call and `jq` parsing with `|| true` guards so failures produce `updates_count=0` instead of crashing. Remove reliance on `USES_QUERY` being non-empty for the step to succeed.

**Checkpoint**: The reusable_dependabot_reviewer.yml extraction and risk classification are robust. All outputs are populated (with safe defaults on failure). The workflow completes with exit code 0 on every dependabot PR.

---

## Phase 2: US3 - Release Age Verification (Priority: P3, but dependency of US1)

**Goal**: Add a release age check that looks up when the dependency version was published and outputs the age in hours. This output is consumed by the auto-approval condition in US1.

**Independent Test**: Trigger a dependabot PR for a dependency version released less than 24 hours ago and verify `release_age_hours` output is less than 24. Trigger for a version released more than 24 hours ago and verify `release_age_hours >= 24`. Trigger for an unknown ecosystem and verify `release_age_hours=-1`.

### Implementation for US3

- [x] T005 [US3] Add a new "Check Release Age" step in .github/workflows/reusable_dependabot_reviewer.yml after the "Detect Ecosystem" step — implement ecosystem-specific release date lookups: (1) `github_actions`: use `gh api repos/${DEP_NAME}/releases/tags/v${DEP_VERSION} --jq '.published_at'`, fall back to tag date via `gh api repos/${DEP_NAME}/git/ref/tags/v${DEP_VERSION}`, (2) `go`: use `curl -sL "https://proxy.golang.org/${DEP_NAME}/@v/v${DEP_VERSION}.info" | jq -r '.Time'`, (3) `python`: use `curl -sL "https://pypi.org/pypi/${DEP_NAME}/${DEP_VERSION}/json" | jq -r '.urls[0].upload_time_iso_8601'`, (4) `unknown`/failure: set `release_age_hours=-1`. Compute age as `(now_epoch - release_epoch) / 3600`. Output `release_age_hours` via `$GITHUB_OUTPUT`. All API calls must use `2>/dev/null || true` to prevent crashes.

**Checkpoint**: The reusable_dependabot_reviewer.yml now outputs `release_age_hours` alongside `risk_level`, `updates_count`, `dep_name`, and `dep_version`. The release age step never crashes.

---

## Phase 3: US1 - Reliable Auto-Approval for Safe Dependency Updates (Priority: P1) MVP

**Goal**: Replace the fragile usage-count-based auto-approval gate with the new criteria: risk is not high, dependency review passed, and release is at least 24 hours old.

**Independent Test**: Submit a dependabot PR with a patch update for a dependency released more than 24 hours ago, with no vulnerabilities. Verify auto-approval fires even if dependency usage data is unavailable.

### Implementation for US1

- [x] T006 [US1] Rewrite the `approve_dependabot_prs` job in .github/workflows/ci_dependencies.yml — replace the step-level `if:` condition (line 71) with direct `needs.*` output references: `needs.call_dependabot_reviewer.outputs.risk_level != 'high' && needs.call_deps_reviewer.outputs.review_conclusion == 'success' && needs.call_dependabot_reviewer.outputs.release_age_hours != '-1' && needs.call_dependabot_reviewer.outputs.release_age_hours >= 24`. Remove the step-level `env:` block (lines 72-75). Update the approval body message to include the rationale (risk level, review conclusion, release age). Note: the 24-hour threshold is used in a single condition; extract to a workflow-level `env:` constant if it is ever referenced in a second location.

**Checkpoint**: Auto-approval fires for patch/minor updates with 24h+ release age, passing review, and passing CI. Major updates and recent releases are never auto-approved.

---

## Phase 4: US2 - Dependency Usage as Informational Context (Priority: P2)

**Goal**: Update the PR comment to include release age, auto-approval rationale, and dependency usage as informational context (not a gate).

**Independent Test**: Trigger a dependabot PR and verify the PR comment includes release age, dependency usage (or "unavailable"), and a clear auto-approval rationale section.

### Implementation for US2

- [x] T007 [US2] Update the `comment_on_dependabot_prs` job in .github/workflows/ci_dependencies.yml — add `RELEASE_AGE_HOURS`, `DEP_NAME`, and `DEP_VERSION` to the step `env:` block from `needs.call_dependabot_reviewer.outputs.*`. Update the comment body template to include: (1) release age display (show hours if known, "unknown — manual review required" if -1), (2) auto-approval rationale section listing each criterion with pass/fail status, (3) dependency usage as informational context ("At least N repositories" when available, "unavailable" when `UPDATES_COUNT` is 0 or empty). Keep the existing maintainer checklist.

**Checkpoint**: PR comments on all dependabot PRs show release age, approval rationale, and informational usage data.

---

## Phase 5: Polish & Validation

**Purpose**: Verify all changes pass linting and assess sync impact.

- [x] T008 Run `make lint` to verify yamllint passes on all modified YAML files in .github/workflows/
- [x] T009 Run `make sync-dry-run` to confirm ci_dependencies.yml is in the sync list and will propagate to all org repos
- [x] T010 Review the final reusable_dependabot_reviewer.yml for net complexity reduction — verify the total line count is lower than the original 278 lines and that no `set -e`, nested while loops, or temp file I/O remain

---

## Dependencies & Execution Order

### Phase Dependencies

- **Foundational US4 (Phase 1)**: No dependencies — can start immediately. Modifies reusable_dependabot_reviewer.yml.
- **US3 (Phase 2)**: Depends on Phase 1 completion (needs `DEP_NAME`, `DEP_VERSION` env vars from extraction step). Modifies same file as Phase 1.
- **US1 (Phase 3)**: Depends on Phase 2 completion (needs `release_age_hours` output). Modifies ci_dependencies.yml.
- **US2 (Phase 4)**: Depends on Phase 2 completion (needs `release_age_hours` output). Modifies ci_dependencies.yml (different job than US1).
- **Polish (Phase 5)**: Depends on Phases 1-4 completion.

### User Story Dependencies

- **US4 (P1)**: Foundational — no dependencies on other stories. BLOCKS US1, US2, US3.
- **US3 (P3)**: Depends on US4 (extraction produces dep_name, dep_version needed for release date lookup). BLOCKS US1.
- **US1 (P1)**: Depends on US4 and US3 (needs risk_level and release_age_hours outputs).
- **US2 (P2)**: Depends on US4 and US3 (needs all outputs for PR comment). Can run in parallel with US1.

### Parallel Opportunities

- **T001, T002**: Sequential (both modify the same step area in the same file)
- **T003, T004**: Can run after T001/T002. T003 and T004 modify different sections of the same file, so sequential is safer.
- **T006, T007**: Can run in parallel (different jobs in ci_dependencies.yml), but sequential is simpler for a single implementer.
- **T008, T009, T010**: Can all run in parallel.

---

## Parallel Example: Phase 3 + Phase 4

```bash
# After Phase 2 (US3) completes, these can run in parallel:
Task: T006 [US1] Rewrite approve_dependabot_prs job in ci_dependencies.yml
Task: T007 [US2] Update comment_on_dependabot_prs job in ci_dependencies.yml
```

---

## Implementation Strategy

### MVP First (US4 + US3 + US1)

1. Complete Phase 1: US4 extraction robustness (reusable_dependabot_reviewer.yml)
2. Complete Phase 2: US3 release age check (reusable_dependabot_reviewer.yml)
3. Complete Phase 3: US1 auto-approval criteria update (ci_dependencies.yml)
4. **STOP and VALIDATE**: Run `make lint`, verify workflows on a test PR
5. At this point, the core feature works: safe updates are auto-approved with robust criteria

### Incremental Delivery

1. US4 + US3 + US1 → Core auto-approval works (MVP)
2. Add US2 → PR comments enriched with approval rationale
3. Polish → Lint, sync verification, complexity audit

---

## Notes

- Only 2 files are modified: `reusable_dependabot_reviewer.yml` and `ci_dependencies.yml`
- No new files are created, no files are deleted
- Net complexity target: ~51 fewer lines across both files
- All bash operations use `|| true` instead of `set -e` for crash prevention
- Commit after each phase with Conventional Commits format (`feat:` or `refactor:`)
