# Implementation Plan: Standardize AI Tooling

**Branch**: `004-standardize-ai-tooling` | **Date**: 2026-04-08 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `/specs/004-standardize-ai-tooling/spec.md`

## Summary

Establish a minimalist, tool-agnostic AI tooling standardization for the org-infra repository. The implementation keeps the constitution at its canonical SpecKit path (`.specify/memory/constitution.md`), creates a project-specific PR review command, sets up an empty skills directory at `.agents/skills/` (agent-agnostic discovery path, supported by OpenCode and other compatible tools), adds clear documentation, and enforces commit/ignore boundaries via a root `.gitignore`. The approach is designed to be replicated across all organization repositories through the existing sync mechanism.

**Key decisions** (from [research.md](research.md)):
- Constitution at `.specify/memory/constitution.md` (SpecKit standard path, consumed by all frameworks)
- Project-specific commands in `.opencode/command/` with selective gitignore
- Single `ai/README.md` for all documentation (setup, commands, skills)
- Single-pass `review_pr` command (simplified from unbound-force's multi-agent council)
- No committed agent context files — CLAUDE.md is local-only

## Technical Context

**Language/Version**: Markdown (documentation, commands), YAML (gitignore patterns, sync config)
**Primary Dependencies**: OpenCode (AI agent tool, recommended), OpenSpec (spec framework, recommended — agent-agnostic)
**Storage**: File-based (Markdown, YAML)
**Testing**: Manual validation (clone repo, install plugin, verify commands)
**Target Platform**: Any platform supporting OpenCode; tool-neutral files work with any AI agent
**Project Type**: Configuration/infrastructure repository
**Performance Goals**: N/A (static configuration files)
**Constraints**: Minimalist — only essential files. Tool-neutral where possible. Scalable across org.
**Scale/Scope**: Proven in org-infra first, then replicated to ~20+ org repos via sync

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Notes |
|-----------|--------|-------|
| I. Single Source of Truth | PASS | Constitution at `.specify/memory/constitution.md` is the centralized reference. No duplication. |
| II. Simplicity & Isolation | PASS | Each file has one purpose. Only essential files included. |
| III. Incremental Improvement | PASS | Single-concern feature branch. |
| IV. Readability First | PASS | Documentation must be clear, short, objective. Command uses explicit naming. |
| V. Do Not Reinvent the Wheel | PASS | Leverages OpenCode/OpenSpec, existing sync mechanism, `gh` CLI for PR review. |
| VI. Composability | PASS | Commands are modular. Constitution is independent of commands. |
| VII. Convention Over Configuration | PASS | Standard directories, sensible defaults, minimal setup. |
| Repository Structure | PASS | Standard files exist. New files follow established conventions. |
| Contribution Workflow | PASS | Feature branch, PR-based, conventional commits. |
| Makefile | N/A | No code-specific commands needed for configuration files. |

**Post-design re-check**: All gates still pass. No violations introduced.

## Project Structure

### Documentation (this feature)

```text
specs/004-standardize-ai-tooling/
├── plan.md              # This file
├── spec.md              # Feature specification
├── research.md          # Phase 0 research decisions
├── data-model.md        # Phase 1 file structure model
├── quickstart.md        # Phase 1 contributor quick-start guide
├── checklists/
│   └── requirements.md  # Specification quality checklist
└── tasks.md             # Phase 2 output (created by /speckit.tasks)
```

### Source Code (repository root)

```text
# New files (5 total — committed, project-specific)
# constitution.md stays at .specify/memory/constitution.md (not moved)
ai/
└── README.md                       # AI tooling docs: setup, commands, skills, multi-tool guide
.opencode/
└── command/
    └── review_pr.md                # Project-specific PR review command
.agents/
└── skills/
    └── .gitkeep                    # Preserves empty skills directory (agent-agnostic path)
.gitignore                          # Root-level gitignore (new file)

# Modified files (1 total)
sync-config.yml                     # Updated to sync AI tooling files to org repos

# Gitignored (tool-managed, NOT committed)
.specify/scripts/                   # Framework scripts
.specify/templates/                 # Framework templates
.specify/extensions/.cache/         # Extension cache
.specify/extensions/.backup/        # Extension backups
.opencode/command/speckit.*         # Framework commands (SpecKit/OpenSpec)
.opencode/command/opsx-*            # Framework commands (OpenSpec tactical)
.opencode/node_modules/             # Plugin runtime
.opencode/package.json              # Plugin declaration
.opencode/package-lock.json         # Plugin lockfile
.opencode/bun.lock                  # Plugin lockfile (bun)
.claude/                            # Claude Code (local-only)
.cursor/                            # Cursor (local-only)
CLAUDE.md                           # Claude agent context (local-only)
```

**Structure Decision**: Minimalist flat structure with 5 new files and 1 modified file. The `ai/` directory serves as the documented home for AI tooling information. Skills live in `.agents/skills/` — an agent-agnostic path discovered by OpenCode and other compatible tools. Project-specific commands live in `.opencode/command/` for auto-discovery by OpenCode. The constitution stays at `.specify/memory/constitution.md` (SpecKit standard path), ensuring compatibility with all spec frameworks.

## File Details

### 1. `constitution.md` (`.specify/memory/`)

The constitution remains at `.specify/memory/constitution.md` — SpecKit's standard path. No move is performed. This file is project-specific content (not framework infrastructure) and is committed to the repository. All spec frameworks (OpenSpec, SpecKit) discover it at this well-known location by convention.

### 2. `ai/README.md`

Clear, short, objective documentation covering:
- What AI tooling is available and why (2-3 sentences)
- How to get started with OpenCode and a spec framework (step-by-step, <1 min read)
- How to get started with other tools (Claude Code, Cursor — brief guidance)
- How to use the `review_pr` command
- How to create new skills (directory structure, file format, registration)
- How to create new project-specific commands
- Link to the constitution for coding standards

Target: a contributor reads this in under 3 minutes and understands the complete AI tooling setup.

### 3. `.agents/skills/.gitkeep`

Empty file preserving the skills directory at the agent-agnostic discovery path (`.agents/skills/<name>/SKILL.md`). No skills shipped initially. OpenCode and other compatible agents auto-discover skills from this location — no configuration needed. This path is agent-neutral (not tied to `.opencode/` or `.claude/`), aligning with FR-010 (tool-agnostic content).

### 4. `.opencode/command/review_pr.md`

Token-efficient, project-specific command accepting a PR number as argument. Uses a **tools-first** strategy with CI-aware failure triage:

1. Fetches PR metadata (minimal — no full diff upfront) via `gh` CLI
2. **Fetches CI check results** via `gh pr checks` — classifies each failing check as PR-caused or pre-existing by comparing against the base branch CI status
3. **Runs local deterministic tools** as pre-flight — detects and executes linters, test runners, and coverage tools available in the project (per constitution Coding Standards: `.golangci.yml`, `ruff`, `yamllint`, `make lint`, `go test`, `pytest`, etc.). Skips checks that CI already ran and passed.
4. Fetches diff (scoped — skips binary/lock/generated files; processes file-by-file for large PRs)
5. Searches `specs/` for associated specifications (loads only FRs and User Stories, not full spec)
6. **AI judgment only** — focuses on what tools and CI cannot check:
   - **Alignment check**: Intent/spec vs code changes (scope, coverage, drift)
   - **Security review**: Input sanitization, unexpected workflows, privilege escalation, secrets
   - **Constitution compliance**: Architectural principles, readability, composability (skips lint/style already covered by tools/CI)
   - **CI failure analysis**: Maps PR-caused failures to specific changes; identifies pre-existing failures
7. Outputs structured findings with severity (CRITICAL / HIGH / MEDIUM / LOW), CI status table, and local tool results
8. **Offers fix-branch for pre-existing CI failures** — creates a separate branch with a proposed fix, commits locally using Conventional Commits, and lets the reviewer inspect and file a PR when ready. Never pushes or files PRs automatically.
9. **Offers in-line PR comments** — for HIGH+ findings, offers to post in-line comments on the PR via `gh` API. All comments are shown to the user and require explicit human confirmation before posting.

Inspired by unbound-force's review-council but simplified to a single-pass command. Optimized for token efficiency by delegating deterministic checks to local tools and CI.

### 5. `.gitignore` (root)

Based on the established complyctl pattern, enforcing:
- Framework infrastructure exclusion (`.specify/scripts`, `.specify/templates`)
- Framework command exclusion (`speckit.*`, `opsx-*`)
- Tool-specific directory exclusion (`.claude/`, `.cursor/`)
- Agent-specific file exclusion (`CLAUDE.md`)
- Plugin artifact exclusion (`node_modules`, `package.json`, lockfiles)

### 6. `sync-config.yml` (modified)

Add entries to sync AI tooling files to organization repositories:
- `.specify/memory/constitution.md`
- `ai/README.md`
- `.agents/skills/.gitkeep`
- `.opencode/command/review_pr.md`
- `.gitignore` (appended or merged, not overwritten)

## Design Notes

**Agent context derivation (FR-007)**: The agent context file (AGENTS.md) is derived from the constitution and feature plans via the `update-agent-context.sh` script, which runs during the `/speckit.plan` workflow. This is a workflow-triggered derivation, not a continuous process. The agent context stays in sync because it is regenerated each time a new feature is planned. For repositories without spec-driven workflows, the constitution at `.specify/memory/constitution.md` serves as the direct agent context.

## Complexity Tracking

No constitution violations detected. No complexity justifications needed.
