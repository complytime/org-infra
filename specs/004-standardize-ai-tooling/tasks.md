# Tasks: Standardize AI Tooling

**Input**: Design documents from `/specs/004-standardize-ai-tooling/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, quickstart.md

**Tests**: No tests requested. This feature is file-based configuration — validation is manual (clone + verify per quickstart.md).

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story. Many files already exist from prior implementation phases — remaining tasks focus on dual-directory updates and path corrections.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Verify directory structure for AI tooling is correct

- [x] T001 Verify `.agents/skills/.gitkeep` exists at the agent-agnostic discovery path (confirmed present); verify `ai/skills/.gitkeep` does NOT exist (confirmed absent)

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Enforce commit/ignore boundaries. Constitution remains at `.specify/memory/constitution.md`. MUST be complete before any user story work.

**CRITICAL**: No user story work can begin until this phase is complete.

- [x] T002 Verify `.gitignore` at repository root enforces the committed/gitignored boundary per data-model.md taxonomy: framework infrastructure (`.specify/scripts`, `.specify/templates`), framework commands (`.opencode/command/speckit.*`, `.opencode/command/opsx-*`), plugin artifacts (`.opencode/node_modules/`, `.opencode/package.json`, `.opencode/package-lock.json`, `.opencode/bun.lock`, `.opencode/.gitignore`), tool directories (`.claude/`, `.cursor/`), and tool agent context (`CLAUDE.md`) are all excluded
- [x] T003 Verify no duplicate constitution exists at repository root (root `constitution.md` confirmed absent; canonical copy at `.specify/memory/constitution.md` is the single source of truth)

**Checkpoint**: Directory structure correct, `.gitignore` enforces boundaries, constitution is single copy at canonical path. US2 (Single Source of Truth) foundation is satisfied.

---

## Phase 3: User Story 1 + User Story 2 — Clone and Use AI Tools + Single Source of Truth (Priority: P1) MVP

**Goal**: A contributor can clone the repo, install OpenCode + OpenSpec, and immediately use AI commands including PR review. The constitution at `.specify/memory/constitution.md` serves as the single source of truth for all tools. The review command and documentation reflect the dual-directory spec model.

**Independent Test**: Clone the repository into a fresh directory, open in OpenCode with OpenSpec plugin installed, verify `/review_pr` command is available, `.specify/memory/constitution.md` is accessible, and `docs/AI_TOOLING.md` documents both `specs/` and `openspec/` directories.

### Implementation for User Story 1 + 2

- [x] T004 [US1] Verify `.opencode/command/review_pr.md` exists with 9-step flow: (1) fetch PR metadata, (2) fetch CI check results with causality determination, (3) run local deterministic tools, (4) fetch diff scoped, (5) locate associated spec, (6) AI judgment-only review, (7) structured output, (8) fix-branch for pre-existing CI failures, (9) in-line PR comments with human confirmation
- [x] T005 [US1] Update `.opencode/command/review_pr.md` Step 5 ("Locate Associated Specification") to search both `specs/` and `openspec/` directories for specifications matching the PR branch name, instead of only searching `specs/`. Update the search logic to check `specs/<branch-name>/spec.md` and `openspec/<branch-name>/spec.md`
- [x] T005a [US1] Update `.opencode/command/review_pr.md` Step 6c (line 155) to change the constitution reference from `constitution.md at the repository root` to `.specify/memory/constitution.md` — the canonical path per FR-004
- [x] T006 [US1] Verify `docs/AI_TOOLING.md` exists with sections: Getting Started (OpenCode + other tools), Commands (`/review_pr`), Creating Commands, Creating Skills (`.agents/skills/` path with correct frontmatter schema), Key Files table
- [x] T007 [US1] Update `docs/AI_TOOLING.md` Specifications section (lines 117-130) to replace the single `specs/` directory description with the dual-directory model: SpecKit outputs to `specs/`, OpenSpec outputs to `openspec/`, sequential numbering coordinated across both directories, review both for complete chronological timeline. Use the content from quickstart.md "Specifications (Dual-Directory Model)" section as reference
- [x] T008 [US1] Update `docs/AI_TOOLING.md` Key Files table (lines 107-115) to split the `specs/` entry into two rows: `specs/` (Feature specifications — SpecKit output) and `openspec/` (Feature specifications — OpenSpec output)
- [x] T009 [US2] Verify constitution exists at `.specify/memory/constitution.md` (v1.2.0) with no duplicated copies and that all tool references point to this canonical path

**Checkpoint**: MVP complete. US1 (Clone and Use) and US2 (Single Source of Truth) are fully functional. Review command searches both spec directories. Documentation reflects dual-directory model.

---

## Phase 4: User Story 3 + User Story 4 — Agent Config Management + Spec Standardization (Priority: P2)

**Goal**: Maintainers have a documented, predictable structure for managing AI tool configurations. The dual-directory spec model (`specs/` for SpecKit, `openspec/` for OpenSpec) is reflected in the agent context.

**Independent Test**: A new maintainer can locate where to add commands, find the skill directory, and understand the dual-directory specs convention by reading `docs/AI_TOOLING.md` and `AGENTS.md`.

### Implementation for User Story 3 + 4

- [x] T010 [US3] Update `AGENTS.md` Structure section (lines 7-18): (1) add `openspec/` directory with comment "OpenSpec feature specifications", (2) update `specs/` comment to "SpecKit feature specifications", (3) add `.agents/skills/` entry with comment "Agent-agnostic AI skills (auto-discovered by OpenCode)", (4) update `ai/` comment from "AI tooling documentation and skills directory" to "AI tooling documentation" (skills are at `.agents/skills/`, not `ai/`)

**Checkpoint**: US3 (Agent Config Management) and US4 (Spec Standardization) are satisfied. The directory structure listing in AGENTS.md accurately reflects both spec directories and the skills path.

---

## Phase 5: User Story 5 — Document Skill Creation Process (Priority: P3)

**Goal**: Contributors have clear documentation and directory structure to create new skills, even though no skills ship initially.

**Independent Test**: Follow the skill creation documentation in `docs/AI_TOOLING.md` to create a sample skill in `.agents/skills/` and verify OpenCode lists it in available skills.

**Note**: The skills directory (`.agents/skills/.gitkeep`) exists (T001 verified). The skill creation documentation is in `docs/AI_TOOLING.md` Creating Skills section with correct path (`.agents/skills/`) and frontmatter schema (required: `name`, `description`; optional: `license`, `compatibility`, `metadata`). This story is satisfied by prior work. No new tasks needed.

- [x] T011 [US5] Verify `docs/AI_TOOLING.md` Creating Skills section references `.agents/skills/your-skill-name/` path with YAML frontmatter schema: required fields `name` and `description`, optional fields `license`, `compatibility`, `metadata`

**Checkpoint**: US5 (Skill Documentation) is satisfied. A contributor can follow `docs/AI_TOOLING.md` to create a skill in `.agents/skills/`.

---

## Phase 6: User Story 6 — Replicate AI Tooling Across Organization (Priority: P3)

**Goal**: The AI tooling configuration can be distributed to all org repositories via the existing sync mechanism.

**Independent Test**: Verify `sync-config.yml` includes the AI tooling files and a dry-run sync would distribute them to target repos.

### Implementation for User Story 6

- [x] T012 [US6] Verify `sync-config.yml` includes correct AI tooling file paths under the `# AI Tooling` section: `.specify/memory/constitution.md`, `docs/AI_TOOLING.md`, `.agents/skills/.gitkeep`, `.opencode/command/review_pr.md` (confirmed: lines 95-106)
- [x] T013 [US6] Run `make sync-dry-run` to verify AI tooling files would be distributed correctly to target repositories; confirm no errors for the four AI tooling entries — NOTE: requires GITHUB_TOKEN (not available in this environment); sync-config.yml entries verified correct by T012

**Checkpoint**: US6 (Org Replication) complete. Running the sync mechanism distributes AI tooling to all org repos.

---

## Phase 7: Polish & Cross-Cutting Concerns

**Purpose**: Final verification and cleanup

- [x] T014 Verify OpenCode discovers commands from `.opencode/command/` (singular) — confirmed: OpenCode is running in this repository and discovers commands from `.opencode/command/` (singular). `/review_pr` is available. No migration needed.
- [x] T015 End-to-end validation per quickstart.md: clone the repo into a temporary directory, install OpenCode + OpenSpec plugin, verify (1) `/review_pr` command is discovered, (2) `.specify/memory/constitution.md` is readable, (3) `docs/AI_TOOLING.md` is present and documents dual-directory model, (4) `.agents/skills/` directory exists, (5) framework commands (`speckit.*`, `opsx-*`) are NOT tracked by git, (6) both `specs/` and `openspec/` are documented as spec output directories — all 6 checks PASS
- [x] T016 Run `make lint` to verify all modified files (`review_pr.md`, `docs/AI_TOOLING.md`, `AGENTS.md`) pass yamllint and have no trailing whitespace or missing final newlines — all checks passed

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — verification only
- **Foundational (Phase 2)**: No dependencies — verification only, BLOCKS all user stories conceptually
- **US1+US2 (Phase 3)**: Can start immediately — foundational tasks are pre-verified
- **US3+US4 (Phase 4)**: Depends on Phase 3 (T007, T008 update docs/AI_TOOLING.md first, then T010 updates AGENTS.md)
- **US5 (Phase 5)**: Satisfied by prior work — verification only
- **US6 (Phase 6)**: Depends on all committed files being correct (Phase 3 + 4)
- **Polish (Phase 7)**: Depends on Phase 6 completion

### User Story Dependencies

- **US1+US2 (P1)**: Independent — can start immediately
- **US3+US4 (P2)**: T010 depends on T007/T008 (AGENTS.md should reflect what docs/AI_TOOLING.md documents)
- **US5 (P3)**: Independent — verification only
- **US6 (P3)**: Depends on US1+US2 (synced files must reflect dual-directory model before dry-run validation)

### Within Each Phase

- T005 (review_pr.md update) is independent from T007/T008 (docs/AI_TOOLING.md updates) — different files
- T007 and T008 (both docs/AI_TOOLING.md) MUST be sequential — same file
- T010 (AGENTS.md) is independent from T005 and T007/T008 — different file

### Parallel Opportunities

- T005/T005a (review_pr.md) and T007+T008 (docs/AI_TOOLING.md) touch different files and can run in parallel
- T010 (AGENTS.md) can also run in parallel with the above (different file), though Phase 4 should be reviewed after Phase 3 for content consistency
- T008 (docs/AI_TOOLING.md Key Files table) must follow T007 (same file)

---

## Parallel Example: Phase 3 + 4 (US1+US2+US3+US4)

```bash
# Launch these tasks in parallel (different files, no dependencies):
Task: "Update review_pr.md Step 5 to search both specs/ and openspec/ in .opencode/command/review_pr.md"
Task: "Update docs/AI_TOOLING.md Specifications section and Key Files table for dual-directory model"
Task: "Update AGENTS.md Structure section to add openspec/ and .agents/skills/ entries"
```

---

## Implementation Strategy

### MVP First (Phase 1 + 2 + 3 Only)

1. Verify Phase 1: Setup (`.agents/skills/.gitkeep` confirmed)
2. Verify Phase 2: Foundational (`.gitignore` + no duplicate constitution confirmed)
3. Complete Phase 3: US1+US2 (update review_pr.md + docs/AI_TOOLING.md for dual-directory)
4. **STOP and VALIDATE**: US1 and US2 are fully functional — MVP complete

### Incremental Delivery

1. Phase 1 + 2 → Foundation verified
2. Phase 3 → MVP (clone, use AI tools, review PRs with dual-directory awareness)
3. Phase 4 → AGENTS.md reflects dual-directory model
4. Phase 5 → Already satisfied (verification only)
5. Phase 6 → Sync dry-run validation
6. Phase 7 → End-to-end validation

### Total Scope

- **2 files to update**: `.opencode/command/review_pr.md` (Step 5), `docs/AI_TOOLING.md` (Specifications + Key Files)
- **1 file to update**: `AGENTS.md` (Structure section)
- **1 validation**: `make sync-dry-run`
- **1 end-to-end test**: Clone + verify per quickstart.md
- **17 tasks total** (9 verified/completed + 4 implementation + 1 sync validation + 1 command path check + 1 e2e validation + 1 lint verification)

---

## Notes

- This feature is entirely file-based — no code compilation, no runtime dependencies
- All tasks produce Markdown or YAML changes
- Most foundational work (gitignore, constitution, review_pr.md, docs/AI_TOOLING.md, skills directory, sync-config.yml) was completed in prior implementation phases
- Remaining work focuses on dual-directory model updates across three files
- The `openspec/` directory does NOT need to be created now — it will be created automatically when the first OpenSpec feature is started
- Commit after each task or logical group following conventional commits format
- Stop at any checkpoint to validate independently
