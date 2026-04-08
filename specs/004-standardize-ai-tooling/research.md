# Research: Standardize AI Tooling

**Branch**: `004-standardize-ai-tooling` | **Date**: 2026-04-08

## R1: Constitution Location

**Decision**: Root-level `constitution.md`

**Rationale**: The constitution is the organizational governance document — not AI-specific. Placing it at root makes it maximally discoverable (alongside README.md, CONTRIBUTING.md, etc.) and avoids coupling to any framework directory. Both OpenSpec and SpecKit discover it by convention at this well-known path.

**Alternatives considered**:
- `ai/constitution.md` — neutral but implies the constitution is AI-specific; it governs all development
- `.specify/memory/constitution.md` — current location; creates coupling between OpenSpec and SpecKit's directory convention
- `.project/constitution.md` — adds a new non-standard directory

**Migration**: The existing constitution at `.specify/memory/constitution.md` will be moved to `constitution.md` at root. The `.specify/memory/` path will be gitignored as part of the framework territory.

## R2: Project-Specific Command Location

**Decision**: `.opencode/command/` with selective gitignore patterns

**Rationale**: OpenCode auto-discovers commands from `.opencode/command/`. Placing project-specific commands there ensures zero-configuration discovery. Framework commands (speckit.\*, opsx-\*) are excluded via gitignore patterns, while project-specific commands (like `review_pr.md`) are committed.

**Alternatives considered**:
- `ai/commands/` — tool-neutral but OpenCode can't auto-discover commands from non-standard directories
- Symlinks from `ai/commands/` to `.opencode/command/` — fragile, platform-dependent
- Commit all commands — creates maintenance burden when framework updates

**Gitignore pattern**:
```
.opencode/command/speckit.*
.opencode/command/opsx-*
```
This excludes framework commands by name prefix while allowing project-specific commands.

## R3: Skills Directory Structure

**Decision**: `ai/skills/` with `.gitkeep` and documentation in `ai/README.md`

**Rationale**: Skills are currently tool-agnostic concept (specialized instruction sets). Placing the structure in `ai/` keeps it neutral. The `.gitkeep` ensures the directory is preserved in git. The documentation in `ai/README.md` explains how to create skills without shipping any initially.

**Alternatives considered**:
- `.opencode/skills/` — OpenCode-specific; wouldn't be discoverable by other tools
- No directory at all — user explicitly requested the structure be created

## R4: Documentation Strategy

**Decision**: Single `ai/README.md` covering setup, commands, skills, and multi-tool guidance

**Rationale**: The user requested "clear, short, and objective documentation for users so they can quickly read and understand how to take the best of AI tools." A single README in the `ai/` directory serves as the entry point. It covers all audience levels — from first-time contributors to maintainers creating new commands and skills.

**Alternatives considered**:
- Multiple docs (SETUP.md, SKILLS.md, COMMANDS.md) — splits information, harder to discover
- Root-level AI_TOOLING.md — clutters root with another file
- Only inline comments in files — insufficient for onboarding

## R5: Review PR Command Design

**Decision**: Single-pass review command in `.opencode/command/review_pr.md` inspired by unbound-force's review-council but simplified

**Rationale**: The unbound-force reference uses a multi-agent review council (5+ sub-agents, parallel execution, 3-iteration fix loops). This is too complex for the initial minimalist approach. A single-pass review command that covers alignment checking, security review, and constitution compliance provides the core value without the orchestration complexity.

**Key capabilities**:
1. Accepts PR number as argument
2. Fetches PR metadata and diff via `gh` CLI
3. Locates associated specification in `specs/` (if exists)
4. Checks alignment between PR intent/spec and code changes
5. Reviews for security issues (non-sanitized inputs, unexpected workflows, injection risks)
6. Checks constitution compliance (coding standards, naming, testing)
7. Outputs structured findings with severity levels

**Alternatives considered**:
- Multi-agent review council (unbound-force style) — too complex for initial adoption
- Minimal linting-only review — doesn't address alignment or security per user request
- External review tool integration — adds dependencies, contradicts "do not reinvent the wheel" when OpenCode can do this natively

## R6: Agent Context File Strategy

**Decision**: No committed agent context file initially. CLAUDE.md is gitignored (local-only).

**Rationale**: The constitution at root-level provides organizational standards. The `ai/README.md` provides tooling documentation. Tool-specific agent context files (CLAUDE.md for Claude Code, future OpenCode equivalents) are generated locally by each contributor's tool setup. This avoids committing tool-specific files while keeping the essential project-specific content (constitution) tool-neutral.

**Alternatives considered**:
- `AGENTS.md` at root (unbound-force pattern) — adds complexity; the constitution already serves this purpose for org-infra's scope
- Auto-generated CLAUDE.md committed — tool-specific, contradicts the "only commit tool-neutral content" principle

## R7: Sync Strategy for Organization Replication

**Decision**: Add `constitution.md`, `ai/` directory, `.gitignore`, and `.opencode/command/review_pr.md` to `sync-config.yml`

**Rationale**: The existing sync mechanism in org-infra distributes configuration files across org repositories. Adding the AI tooling files to this configuration enables automatic replication. Each target repo gets the same constitution, documentation, command, and gitignore without manual setup.

**Considerations**:
- Constitution may need per-repo increments (the constitution itself allows this)
- Some repos may need different review_pr behavior — the synced version serves as a baseline
- The `.gitignore` patterns may need per-repo adjustments for non-standard setups
