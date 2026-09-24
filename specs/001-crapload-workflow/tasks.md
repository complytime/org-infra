# Tasks: Centralize CRAP Load Analysis Workflow

**Input**: Design documents from `/specs/001-crapload-workflow/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Phase 1: Setup

**Purpose**: No project initialization needed — org-infra already exists. This phase reads lint configuration per constitution requirements.

- [x] T001 Read lint configuration files (.yamllint.yml, .mega-linter.yml) to understand enforced rules before making changes

---

## Phase 2: Foundational (Reusable Workflow Migration)

**Purpose**: Move the reusable workflow from complyctl to org-infra. This MUST be complete before any consumer workflow or sync config can reference it.

**CRITICAL**: No user story work can begin until this phase is complete.

- [x] T002 Copy reusable_crapload_analysis.yml from complyctl (local path: /home/maburgha/GIT/ProdSec/complyctl/.github/workflows/reusable_crapload_analysis.yml) to .github/workflows/reusable_crapload_analysis.yml
- [x] T003 Normalize indentation from 4-space to 2-space throughout .github/workflows/reusable_crapload_analysis.yml
- [x] T004 Add SPDX license header comment and workflow purpose description header to .github/workflows/reusable_crapload_analysis.yml (verify header comment block exists per constitution YAML Formatting standards)
- [x] T005 Validate .github/workflows/reusable_crapload_analysis.yml passes yamllint with .yamllint.yml configuration

**Checkpoint**: Reusable workflow is in org-infra, properly formatted, and passes linting.

---

## Phase 3: User Story 1 - Adopt CRAP Load Analysis in a Go Repository (Priority: P1)

**Goal**: Enable any Go repository to adopt CRAP load analysis by adding a consumer workflow that references the org-infra reusable workflow.

**Independent Test**: Create the consumer workflow, verify it references the org-infra reusable workflow correctly, and passes yamllint.

### Implementation for User Story 1

- [x] T006 [US1] Create consumer workflow template at .github/workflows/ci_crapload.yml that calls complytime/org-infra/.github/workflows/reusable_crapload_analysis.yml@main on pull_request targeting main, with contents:read and pull-requests:write permissions
- [x] T007 [US1] Validate .github/workflows/ci_crapload.yml passes yamllint with .yamllint.yml configuration

**Checkpoint**: Consumer workflow template exists and can be used by any Go repository to invoke CRAP load analysis.

---

## Phase 4: User Story 2 - Detect CRAP Score Regressions (Priority: P1)

**Goal**: The reusable workflow detects regressions and fails the check when CRAP scores increase or new functions exceed the threshold.

**Independent Test**: This functionality is already implemented in the reusable workflow logic (baseline comparison, threshold enforcement). Verify the workflow outputs include status, regressions-count, and improvements-count.

### Implementation for User Story 2

- [x] T008 [US2] Verify the reusable workflow in .github/workflows/reusable_crapload_analysis.yml correctly outputs status (pass/fail), crapload-count, gaze-crapload-count, regressions-count, and improvements-count
- [x] T009 [US2] Verify the Enforce threshold step in .github/workflows/reusable_crapload_analysis.yml exits with code 1 on status=fail

**Checkpoint**: Regression detection logic is verified in the migrated workflow. No code changes expected — this is validation of existing functionality after migration.

---

## Phase 5: User Story 3 - Sync Consumer Workflow to Go Repositories (Priority: P2)

**Goal**: Add the consumer workflow to the org-infra sync configuration so it is automatically distributed to Go repositories across the organization.

**Independent Test**: Run `make sync-dry-run` or `python3 scripts/sync-org-repositories.py --org complytime --dry-run` and verify ci_crapload.yml is listed for Go repos and excluded from non-Go repos.

### Implementation for User Story 3

- [x] T010 [US3] Add ci_crapload.yml sync entry to sync-config.yml with source .github/workflows/ci_crapload.yml, destination .github/workflows/ci_crapload.yml, and exclude_repos list for non-Go repositories (complyscribe, complytime-demos, complytime-policies, vagrant-boxes, community)

**Checkpoint**: Sync configuration is updated. Running a dry-run sync confirms the consumer workflow targets only Go repositories.

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Documentation and final validation.

- [x] T011 [P] Update README.md to add ci_crapload.yml and reusable_crapload_analysis.yml to the directory structure table and workflow descriptions
- [x] T012 Run make lint-yaml to verify all new and modified files pass linting
- [x] T013 Verify quickstart.md adoption instructions in specs/001-crapload-workflow/quickstart.md match the actual consumer workflow created in T006

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — read-only lint config review
- **Foundational (Phase 2)**: Depends on Phase 1 — BLOCKS all user stories
- **User Story 1 (Phase 3)**: Depends on Phase 2 (reusable workflow must exist)
- **User Story 2 (Phase 4)**: Depends on Phase 2 (validates migrated workflow)
- **User Story 3 (Phase 5)**: Depends on Phase 3 (consumer workflow must exist to sync)
- **Polish (Phase 6)**: Depends on Phases 3 and 5

### User Story Dependencies

- **User Story 1 (P1)**: Depends on Foundational — reusable workflow must be in org-infra
- **User Story 2 (P1)**: Depends on Foundational — validates the migrated workflow, can run in parallel with US1
- **User Story 3 (P2)**: Depends on US1 — consumer workflow must exist before adding to sync config

### Parallel Opportunities

- T008 and T009 (US2 validation) can run in parallel with T006-T007 (US1 consumer workflow creation) since they operate on different files
- T011 (README update) can run in parallel with T012 (lint validation)

---

## Parallel Example: User Stories 1 and 2

```text
# After Phase 2 (Foundational) completes, these can run in parallel:

# Stream A - User Story 1 (consumer workflow):
Task T006: Create consumer workflow at .github/workflows/ci_crapload.yml
Task T007: Validate ci_crapload.yml passes yamllint

# Stream B - User Story 2 (regression detection validation):
Task T008: Verify workflow outputs in reusable_crapload_analysis.yml
Task T009: Verify threshold enforcement step
```

---

## Implementation Strategy

### MVP First (User Stories 1 + 2)

1. Complete Phase 1: Read lint config
2. Complete Phase 2: Migrate reusable workflow (T002-T005)
3. Complete Phase 3: Create consumer workflow (T006-T007)
4. Complete Phase 4: Validate regression detection (T008-T009)
5. **STOP and VALIDATE**: Consumer workflow works, regression detection verified
6. Can be merged and used immediately by repositories adding the consumer workflow manually

### Full Delivery (Add Sync)

7. Complete Phase 5: Add sync configuration (T010)
8. Complete Phase 6: Documentation and final lint check (T011-T013)
9. **VALIDATE**: Dry-run sync confirms correct targeting

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- US2 is primarily validation — the regression detection logic already exists in the source workflow
- Commit after each phase completion
- The reusable workflow is copied as-is (with indentation normalization) — no logic changes
