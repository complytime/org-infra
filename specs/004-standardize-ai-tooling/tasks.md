# Tasks: Standardize AI Tooling

**Input**: Design documents from `/specs/004-standardize-ai-tooling/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, quickstart.md

**Tests**: No tests requested. This feature is file-based configuration — validation is manual (clone + verify).

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Create the directory structure for AI tooling

- [ ] ~~T001 Create directory structure with empty skills placeholder in ai/skills/.gitkeep~~ REVERTED — `ai/skills/` is not in OpenCode's skill discovery paths. Replaced by T023.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Enforce commit/ignore boundaries. Constitution remains at `.specify/memory/constitution.md`. MUST be complete before any user story work.

**CRITICAL**: No user story work can begin until this phase is complete.

- [x] T002 Create root .gitignore based on complyctl pattern (see research.md R2) enforcing: framework infrastructure exclusion (.specify/scripts, .specify/templates), framework command exclusion (.opencode/command/speckit.*, .opencode/command/opsx-*), tool directory exclusion (.claude/, .cursor/), agent file exclusion (CLAUDE.md), and plugin artifact exclusion (.opencode/node_modules, .opencode/package.json, .opencode/package-lock.json, .opencode/bun.lock, .opencode/.gitignore) in .gitignore
- [ ] ~~T003 Copy constitution from .specify/memory/constitution.md to root constitution.md (preserve content, change only location)~~ REVERTED — constitution stays at `.specify/memory/constitution.md` (SpecKit standard path). Moving breaks SpecKit hardcoded references. See analysis finding F5.
- [ ] ~~T004 Update the "Incrementing This Constitution" section in constitution.md to replace the `.specify/memory/constitution.md` path reference with the new root-level `constitution.md` canonical path~~ REVERTED — no path change needed since constitution is not moved. See analysis finding F5.

**Checkpoint**: Constitution remains at `.specify/memory/constitution.md`, .gitignore enforces boundaries. US2 (Single Source of Truth) is satisfied.

---

## Phase 3: User Story 1 + User Story 2 — Clone and Use AI Tools + Single Source of Truth (Priority: P1) MVP

**Goal**: A contributor can clone the repo, install OpenCode + OpenSpec, and immediately use AI commands including PR review. The constitution at `.specify/memory/constitution.md` serves as the single source of truth for all tools.

**Independent Test**: Clone the repository into a fresh directory, open in OpenCode with OpenSpec plugin installed, verify `/review_pr` command is available and `.specify/memory/constitution.md` is accessible.

### Implementation for User Story 1 + 2

- [x] T005 [P] [US1] Create PR review command in .opencode/command/review_pr.md with YAML frontmatter (description field), accepting PR number as argument, implementing a 9-step token-efficient review flow: (1) fetch PR metadata via gh CLI, (2) fetch CI check results and determine causality for failures (PR-caused vs pre-existing by comparing against base branch), (3) run local deterministic tools as pre-flight (linters, tests per constitution Coding Standards — skip if CI already passed), (4) fetch diff scoped (skip binary/lock files, file-by-file for large PRs), (5) locate associated specification in specs/, (6) AI judgment-only review: alignment check, security review, constitution compliance, CI failure analysis — skip categories covered by tools/CI, (7) structured output with CI status table, local tool results, and severity levels CRITICAL/HIGH/MEDIUM/LOW, (8) offer fix-branch for pre-existing CI failures (create branch, commit locally with Conventional Commits, never push/file PR automatically), (9) offer in-line PR comments for HIGH+ findings with mandatory human confirmation before posting. See plan.md File Details section 4 for full requirements.
- [x] T006 [P] [US1] Create AI tooling documentation in ai/README.md covering: (1) what AI tooling is available and why (2-3 sentences), (2) getting started with OpenCode + OpenSpec (step-by-step, <1 min read), (3) getting started with other tools — Claude Code and Cursor (brief guidance), (4) how to use the review_pr command with examples, (5) how to create new skills (directory structure .agents/skills/your-skill-name/SKILL.md, YAML frontmatter with required name/description and optional license/compatibility/metadata per OpenCode docs, discovery mechanism), (6) how to create new project-specific commands (.opencode/command/ location, YAML frontmatter format), (7) link to .specify/memory/constitution.md for coding standards. Target: contributor reads in under 3 minutes. See quickstart.md for content basis.

**Checkpoint**: MVP complete. US1 (Clone and Use) and US2 (Single Source of Truth) are fully functional and testable independently. A contributor can clone, install OpenCode, and immediately use /review_pr and framework commands.

---

## Phase 4: User Story 3 + User Story 4 — Agent Config Management + Spec Standardization (Priority: P2)

**Goal**: Maintainers have a documented, predictable structure for managing AI tool configurations and all specs follow a consistent directory convention.

**Independent Test**: A new maintainer can locate where to add commands, find the skill directory, and understand the specs/ naming convention by reading ai/README.md.

**Note**: These stories are satisfied by artifacts created in Phase 2 (.gitignore) and Phase 3 (ai/README.md with management docs). The specs/ directory and naming convention already exist from prior features (satisfies FR-005). Agent context derivation (FR-007) is handled by the existing `update-agent-context.sh` script triggered during `/speckit.plan` workflows (see plan.md Design Notes). No new files are needed — only verification that existing documentation covers these requirements.

**Checkpoint**: US3 (Agent Config Management) and US4 (Spec Standardization) are satisfied by the directory structure and documentation created in prior phases.

---

## Phase 5: User Story 5 — Document Skill Creation Process (Priority: P3)

**Goal**: Contributors have clear documentation and directory structure to create new skills, even though no skills ship initially.

**Independent Test**: Follow the skill creation documentation in ai/README.md to create a sample skill in .agents/skills/ and verify OpenCode lists it in available skills.

**Note**: The skills directory (.agents/skills/.gitkeep) is created in Phase 1 (T023). The skill creation documentation is included in ai/README.md in Phase 3 (T006, section 5). This story is satisfied by prior work. No new tasks needed.

**Checkpoint**: US5 (Skill Documentation) is satisfied. A contributor can follow ai/README.md to create a skill in .agents/skills/.

---

## Phase 6: User Story 6 — Replicate AI Tooling Across Organization (Priority: P3)

**Goal**: The AI tooling configuration can be distributed to all org repositories via the existing sync mechanism.

**Independent Test**: Verify sync-config.yml includes the AI tooling files and a dry-run sync would distribute them to target repos.

### Implementation for User Story 6

- [ ] ~~T007 [US6] Update sync-config.yml to add AI tooling files for organization-wide distribution: constitution.md, ai/README.md, ai/skills/.gitkeep, .opencode/command/review_pr.md, and .gitignore entries (appended/merged, not overwritten).~~ REVERTED — sync paths need correction. Replaced by T028. See analysis findings F5, F8, F12.

**Checkpoint**: US6 (Org Replication) complete. Running the sync mechanism distributes AI tooling to all org repos.

---

## Phase 7: Remediation — review_pr Enhancements (Post-Analysis)

**Purpose**: Address gaps identified by `/speckit.analyze` — FR-012 through FR-015 were added to spec.md during iterative clarification and remediation after initial implementation. These tasks track the review_pr.md updates that implement them.

- [x] T010 [US1] Update .opencode/command/review_pr.md to add token-efficiency strategy: delegate deterministic checks (lint, tests, coverage) to locally available tools before AI analysis, skip AI categories where local tools or CI already passed (FR-012). Updated in .opencode/command/review_pr.md Steps 3 and 6.
- [x] T011 [US1] Update .opencode/command/review_pr.md to add in-line PR comment capability with mandatory human confirmation: prepare comments, show for review, wait for explicit yes/no/edit before posting via gh API (FR-013). Updated in .opencode/command/review_pr.md Step 9.
- [x] T012 [US1] Update .opencode/command/review_pr.md to add CI check results fetching and causality determination: fetch via gh pr checks, compare failing checks against base branch status to classify as PR-caused or pre-existing (FR-014). Updated in .opencode/command/review_pr.md Steps 2 and 2a.
- [x] T013 [US1] Update .opencode/command/review_pr.md to add fix-branch workflow for pre-existing CI failures: create branch from base, propose minimal fix, commit locally with Conventional Commits, never push or file PR automatically (FR-015). Updated in .opencode/command/review_pr.md Step 8.
- [x] T014 [US1] Update ai/README.md to reflect review_pr command's CI-aware 5-step flow, fix-branch capability, and in-line comments feature. Updated in ai/README.md Commands section.
- [x] T015 Update spec.md to add FR-012 (token efficiency), FR-013 (in-line comments), FR-014 (CI triage), FR-015 (fix-branch). Reword FR-003 for selective gitignore accuracy.
- [x] T016 Update plan.md File Details section 4 to reflect review_pr.md's 9-step strategy including CI triage, fix-branch, and in-line comments.

---

## Phase 8a: Remediation — Skills Path + Constitution Revert (Post-Analysis)

**Purpose**: Fix two critical issues: (1) skills directory at wrong location — OpenCode discovers skills from `.agents/skills/`, not `ai/skills/`; (2) revert constitution move from `.specify/memory/` to root — SpecKit hardcodes `.specify/memory/constitution.md`.

### Skills Path Correction (F1-F4, F8)

- [ ] T023 Remove `ai/skills/.gitkeep` and create `.agents/skills/.gitkeep` — agent-agnostic skill discovery path (discovered by OpenCode and other compatible tools). Replaces T001.
- [ ] T024 [P] Update `ai/README.md` skill creation docs: change path to `.agents/skills/your-skill-name/`, replace `tags` frontmatter field with valid OpenCode fields (`license`, `compatibility`, `metadata`), update Key Files table to reference `.agents/skills/`.
- [ ] T025 [P] Update `spec.md`: FR-006 (skills path), US5 acceptance scenarios, SC-004, Key Entity: Skill, edge cases, and assumptions to reference `.agents/skills/`.
- [ ] T026 [P] Update `plan.md`: summary, project structure, file details section 3, and sync entries to reference `.agents/skills/`.

### Constitution Revert (F5, F9-F12)

- [ ] T027 Delete root `constitution.md` (the copy created by T003). The canonical file at `.specify/memory/constitution.md` is unchanged.
- [ ] T028 [P] Update `sync-config.yml`: change constitution source from `constitution.md` to `.specify/memory/constitution.md`, change skills source from `ai/skills/.gitkeep` to `.agents/skills/.gitkeep` (agent-agnostic path). Replaces T007.
- [ ] T029 [P] Update `AGENTS.md`: change `constitution.md` references to `.specify/memory/constitution.md` in Structure listing and Constraints section.
- [ ] T030 [P] Update `ai/README.md`: change `constitution.md` references to `.specify/memory/constitution.md` in Getting Started, command docs, command writing guidance, and Key Files table.
- [ ] T031 [P] Update `spec.md`: rewrite FR-004, Q6 clarification, FR-003 parenthetical, Key Entity: Project-Specific Content, Assumptions, and edge cases to reference `.specify/memory/constitution.md`.
- [ ] T032 [P] Update `plan.md`: revert summary, key decisions, constitution check table, file details section 1, and design notes to reference `.specify/memory/constitution.md`.

### Commands Path Investigation (F6)

- [ ] T033 Verify whether OpenCode discovers commands from `.opencode/command/` (singular) in addition to `.opencode/commands/` (plural). If only plural is supported, plan migration of review_pr.md and coordinate with SpecKit plugin expectations.

**Checkpoint**: Skills at correct OpenCode path. Constitution duplication resolved. All references consistent.

---

## Phase 8: Polish & Cross-Cutting Concerns

**Purpose**: Final verification and cleanup

- [x] T008 Verify .gitignore correctly excludes framework commands (speckit.*, opsx-*) while preserving project-specific command review_pr.md — test by running git status after framework plugin install
- [ ] T009 End-to-end validation: clone the repo into a temporary directory, install OpenCode + OpenSpec plugin, verify /review_pr command is discovered, verify .specify/memory/constitution.md is readable, verify ai/README.md is present, verify .agents/skills/ directory exists, verify framework commands are not tracked by git — per quickstart.md validation steps

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — can start immediately
- **Foundational (Phase 2)**: Depends on Setup — BLOCKS all user stories
- **US1+US2 (Phase 3)**: Depends on Foundational phase completion
- **US3+US4 (Phase 4)**: Satisfied by Phase 2 + Phase 3 artifacts — no new work
- **US5 (Phase 5)**: Satisfied by Phase 1 + Phase 3 artifacts — no new work
- **US6 (Phase 6)**: Depends on all committed files existing (Phase 1-3)
- **Remediation (Phase 7)**: Post-analysis updates to review_pr.md, spec.md, plan.md, ai/README.md
- **Polish (Phase 8)**: Depends on Phase 7 completion

### User Story Dependencies

- **US1+US2 (P1)**: Can start after Foundational (Phase 2) — No dependencies on other stories
- **US3+US4 (P2)**: Satisfied by US1+US2 artifacts — no additional implementation
- **US5 (P3)**: Satisfied by Setup + US1 artifacts — no additional implementation
- **US6 (P3)**: Can start after US1+US2 — independent from US3-US5

### Within Each Phase

- T005 and T006 can run in parallel (different files, no dependencies)
- T002, T003, T004 must be sequential (T003 depends on T002 being ready, T004 depends on T003)

### Parallel Opportunities

- Phase 1 (T001) can overlap with Phase 2 (T002) since they touch different files
- In Phase 3, T005 (review_pr.md) and T006 (ai/README.md) are fully parallel
- Phase 6 (T007) is independent once prior phases complete

---

## Parallel Example: Phase 3 (US1+US2)

```bash
# Launch both tasks in parallel (different files, no dependencies):
Task: "Create PR review command in .opencode/command/review_pr.md"
Task: "Create AI tooling documentation in ai/README.md"
```

---

## Implementation Strategy

### MVP First (Phase 1 + 2 + 3 Only)

1. Complete Phase 1: Setup (create .agents/skills/.gitkeep)
2. Complete Phase 2: Foundational (.gitignore enforcement)
3. Complete Phase 3: US1+US2 (review_pr command + documentation)
4. **STOP and VALIDATE**: Clone test per quickstart.md
5. US1 and US2 are fully functional — MVP complete

### Incremental Delivery

1. Phase 1 + 2 → Foundation ready
2. Phase 3 → MVP (clone, use AI tools, review PRs)
3. Phase 4 + 5 → Already satisfied (no new work)
4. Phase 6 → Org-wide distribution
5. Phase 7 → Final verification

### Total Scope

- **5 new files**: ai/README.md, .agents/skills/.gitkeep (agent-agnostic), .opencode/command/review_pr.md, .gitignore
- **1 modified file**: sync-config.yml
- **27 tasks total** (7 implementation + 7 review_pr remediation + 11 path remediation + 2 verification)

---

## Notes

- This feature is entirely file-based — no code compilation, no runtime dependencies
- All tasks produce Markdown, YAML, or gitignore files
- The minimalist approach means most user stories (US3, US4, US5) are satisfied by the foundational work + documentation created for US1+US2
- Commit after each task or logical group following conventional commits format
- Stop at any checkpoint to validate independently
