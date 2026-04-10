# Implementation Plan: Standardize AI Tooling

**Branch**: `004-standardize-ai-tooling` | **Date**: 2026-04-09 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `/specs/004-standardize-ai-tooling/spec.md`

## Summary

Standardize AI tooling in org-infra so contributors can clone the repository and immediately use AI-assisted development with OpenCode (recommended agent) and OpenSpec or SpecKit (spec-driven frameworks). The implementation creates a minimal set of committed project-specific files — constitution, documentation, PR review command, skills directory, and gitignore — that define the AI tooling contract. Both spec frameworks coexist: SpecKit outputs to `specs/` and OpenSpec outputs to `openspec/`, sharing a coordinated sequential numbering scheme and a single constitution at `.specify/memory/constitution.md`. Framework commands, scripts, and templates are tool-managed (gitignored), not committed. The sync mechanism distributes AI tooling files to all organization repositories.

## Technical Context

**Language/Version**: YAML (GitHub Actions syntax), Markdown, Python 3.x (sync scripts only)
**Primary Dependencies**: OpenCode (agent), OpenSpec/SpecKit (spec frameworks — plugin-managed), `gh` CLI (PR review command), GitPython + PyYAML + requests (sync script — existing)
**Storage**: N/A (filesystem-only; no database or persistent storage)
**Testing**: Manual clone-and-verify (file-based configuration); existing `pytest` for sync script
**Target Platform**: GitHub (CI/CD), local development environments (Linux, macOS)
**Project Type**: Infrastructure/configuration repository
**Performance Goals**: N/A (no runtime service; SC-001 targets <5 min onboarding)
**Constraints**: sync-config.yml governs distribution scope; constitution is the authoritative reference for all standards
**Scale/Scope**: Organization-wide (all ComplyTime repositories)

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| # | Principle | Status | Assessment |
|---|-----------|--------|------------|
| I | Single Source of Truth | PASS | Constitution at `.specify/memory/constitution.md` — single canonical copy consumed by all tools. No duplication. Synced to org repos. |
| II | Simplicity & Isolation | PASS | Each file has a single responsibility: constitution (standards), gitignore (boundaries), docs/AI_TOOLING.md (AI docs), review_pr.md (PR review), skills/.gitkeep (extensibility placeholder). Documentation lives in `docs/` alongside existing project docs. |
| III | Incremental Improvement | PASS | Feature is focused on AI tooling standardization. No unrelated changes. |
| IV | Readability First | PASS | All deliverables are Markdown with explicit naming. Documentation targets <3 min read. Skill and command creation have documented structures. |
| V | Do Not Reinvent the Wheel | PASS | Uses existing sync mechanism (sync-config.yml), existing frameworks (OpenSpec, SpecKit), existing agent (OpenCode). No custom implementations where established tools exist. |
| VI | Composability | PASS | Modular files in standard formats (YAML, Markdown). Skills are self-contained in `.agents/skills/<name>/SKILL.md`. Constitution is a standalone document referenced by all tools. |
| VII | Convention Over Configuration | PASS | OpenCode is the default agent, OpenSpec is the recommended framework. Standard paths (`.agents/skills/`, `.opencode/command/`) follow tool conventions. Contributors only configure if deviating. |
| — | Repository Structure | PASS | README.md, LICENSE, CONTRIBUTING.md, CODE_OF_CONDUCT.md, SECURITY.md, .github/ all present. |
| — | Commit Standards | PASS | Conventional Commits, Signed-off-by, Assisted-by trailers all required per constitution. |
| — | Lint/Format | PASS | YAML linted with yamllint (.yamllint.yml), Python linted with ruff (ruff.toml). Feature produces Markdown/YAML — both covered by existing lint. |

**Gate result: PASS** — No violations. Proceed to Phase 0.

## Project Structure

### Documentation (this feature)

```text
specs/004-standardize-ai-tooling/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
└── tasks.md             # Phase 2 output (created by /speckit.tasks, NOT by this plan)
```

### Source Code (repository root)

```text
# Committed project-specific content
.agents/
  skills/
    .gitkeep                     # Agent-agnostic skill discovery path (empty initially)

.opencode/
  command/
    review_pr.md                 # Project-specific PR review command

.specify/
  memory/
    constitution.md              # Single source of truth — org-wide governance

docs/
  AI_TOOLING.md                  # AI tooling documentation (setup, commands, skills)

specs/                           # SpecKit spec output (existing features 001-004)
openspec/                        # OpenSpec spec output (created when first OpenSpec feature exists)

.gitignore                       # Enforces committed/gitignored boundary
sync-config.yml                  # Distributes AI tooling files to org repos
AGENTS.md                        # Agent context file (auto-derived)
```

**Structure Decision**: No traditional `src/` or `tests/` applies to this feature. All deliverables are configuration/documentation files at known paths within the repository root. The project structure above reflects the dual-directory spec model (`specs/` + `openspec/`) with coordinated sequential numbering, as decided in the spec clarifications.

## Key Design Decisions

### D1: Dual Spec Directory Model

SpecKit outputs to `specs/`, OpenSpec outputs to `openspec/`. Both directories are committed. Sequential numbering is coordinated across both directories — the next feature scans both directories to pick the next available number. Collisions (from concurrent branches) are resolved at PR merge by renumbering the later-merged feature.

**Rationale**: Respects each framework's native directory convention. Cross-referencing via shared naming conventions (sequential numbers, descriptive names) bridges history without coupling the frameworks.

### D2: Constitution at `.specify/memory/constitution.md`

The constitution remains at SpecKit's standard path. This is project-specific content (not framework infrastructure) committed to the repository and consumed by all spec frameworks. OpenSpec discovers it at this well-known path by convention. Moving it would break SpecKit's hardcoded references without benefit.

### D3: Spec-Level Portability Only

The spec file (in each framework's output directory) is the shared contract between frameworks. Plans and tasks are framework-specific but human-readable. Mid-feature handoff between frameworks is not a guaranteed workflow — contributors read the existing spec and restart their own framework's planning workflow.

### D4: Framework-Native Templates

Each framework uses its own spec template without custom structural enforcement. Cross-directory readability relies on specs being human-readable as-is, not on mandated structural alignment.

### D5: No Migration of Existing Specs

Existing SpecKit specs (001-004) remain in `specs/`. New OpenSpec features go to `openspec/`. Unified sequential numbering preserves chronological continuity without file moves.

### D6: Selective Gitignore for Commands

Framework commands (prefixed `speckit.*`, `opsx-*`) are excluded via `.gitignore` patterns. Project-specific commands (e.g., `review_pr.md`) are committed. This allows OpenCode auto-discovery while keeping framework-managed commands out of version control.

### D7: Agent Context Derivation

AGENTS.md is committed and auto-derived from the constitution and feature plans via `update-agent-context.sh`. CLAUDE.md is gitignored (local-only). This keeps the committed agent context tool-neutral.

## File Details

### 1. Constitution (`.specify/memory/constitution.md`) — EXISTS

No changes needed. The constitution is already in place at its canonical location (v1.2.0). All frameworks consume it at this path. Synced to org repos via sync-config.yml.

### 2. Gitignore (`.gitignore`) — EXISTS

Already created (T002, completed). Enforces boundaries:
- Framework infrastructure: `.specify/scripts`, `.specify/templates`
- Framework commands: `.opencode/command/speckit.*`, `.opencode/command/opsx-*`
- Plugin artifacts: `.opencode/node_modules/`, `.opencode/package.json`, etc.
- Tool directories: `.claude/`, `.cursor/`
- Tool agent context: `CLAUDE.md`

### 3. Skills Directory (`.agents/skills/.gitkeep`) — EXISTS

The skills directory is at `.agents/skills/` (agent-agnostic discovery path). Confirmed present (T001 verified). The old `ai/skills/.gitkeep` has been removed.

### 4. PR Review Command (`.opencode/command/review_pr.md`) — EXISTS

Already created (T005, completed) with full 9-step flow: fetch metadata, CI triage, local tools, scoped diff, spec alignment, AI-only review, structured output, fix-branch for pre-existing failures, in-line PR comments with human confirmation. Remediation tasks T010-T013 (completed) added FR-012 through FR-015 capabilities.

**Updates needed**:
- Step 5 currently searches only `specs/` for associated specifications. Must also search `openspec/` (T005).
- Step 6c references `constitution.md` at repository root instead of `.specify/memory/constitution.md` (T005a — fixed).

### 5. AI Documentation (`docs/AI_TOOLING.md`) — EXISTS

Moved from `ai/README.md` to `docs/AI_TOOLING.md` to align with existing documentation convention (`docs/` already contains `LOCAL_TESTING.md`, `SYNC_REPOSITORIES_SETUP.md`). Covers getting started, commands, creating commands, creating skills, key files, specifications. Dual-directory model and Key Files table already updated.

### 6. Sync Configuration (`sync-config.yml`) — EXISTS

AI tooling entries updated: `.specify/memory/constitution.md`, `docs/AI_TOOLING.md`, `.agents/skills/.gitkeep`, `.opencode/command/review_pr.md`.

### 7. Agent Context (`AGENTS.md`) — EXISTS, UPDATE NEEDED

Currently references the repository structure. Needs update (T010) to:
- Add `openspec/` to the directory structure listing
- Add `.agents/skills/` entry
- Fix stale `ai/` comment ("skills directory" — skills are at `.agents/skills/`)

## Design Notes

### Dual-Directory Sequential Numbering

When creating a new feature, the framework must scan both directories to determine the next number:

```
# Pseudocode for next-number determination
max_specs = max(number_prefix(d) for d in ls("specs/"))      # e.g., 004
max_openspec = max(number_prefix(d) for d in ls("openspec/")) # e.g., 0 (empty)
next_number = max(max_specs, max_openspec) + 1                # → 005
```

If `openspec/` doesn't exist yet, only `specs/` is scanned. The first OpenSpec feature creates the `openspec/` directory.

### Collision Resolution

Concurrent branches may pick the same number. This is detected at PR merge time:
1. CI or reviewer notices duplicate number across `specs/` and `openspec/`
2. The later-merged feature is renumbered (directory rename + branch reference update)
3. No centralized registry needed — Git merge conflict on directory names serves as the detection mechanism

### Review Command Cross-Directory Search

The `review_pr.md` command (Step 5) must search both `specs/` and `openspec/` for associated specifications:
```
# Check both directories for branch-name match
specs/<branch-name>/spec.md
openspec/<branch-name>/spec.md
```

### Agent Context Derivation

The `update-agent-context.sh` script generates AGENTS.md (and optionally CLAUDE.md) from the constitution and feature plans. This runs during `/speckit.plan` workflows. The script is tool-managed (gitignored) — it reads committed content and updates agent context files.

## Complexity Tracking

No constitution violations detected. No complexity justification needed.
