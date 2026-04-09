# Research: Standardize AI Tooling

**Branch**: `004-standardize-ai-tooling` | **Date**: 2026-04-09 (updated)

## R1: Constitution Location

**Decision**: `.specify/memory/constitution.md` (SpecKit's standard path)

**Rationale**: The constitution is project-specific content committed to the repository and consumed by all spec frameworks at this well-known path. SpecKit hardcodes this path in its commands. Moving it to root was attempted (T003) and reverted — it broke SpecKit's references without functional benefit. OpenSpec discovers the constitution at this path by convention. The file is project-owned, not framework-owned.

**Alternatives considered**:
- Root-level `constitution.md` — initially chosen, reverted. Breaks SpecKit hardcoded references. No discoverability improvement since `ai/README.md` links to the canonical path.
- `ai/constitution.md` — implies constitution is AI-specific; it governs all development
- `.project/constitution.md` — adds a non-standard directory

## R2: Project-Specific Command Location

**Decision**: `.opencode/command/` with selective gitignore patterns

**Rationale**: OpenCode auto-discovers commands from `.opencode/command/`. Framework commands (speckit.\*, opsx-\*) are excluded via gitignore patterns, while project-specific commands (like `review_pr.md`) are committed. This achieves zero-configuration discovery for project commands while keeping framework-managed commands out of version control.

**Gitignore patterns**:
```
.opencode/command/speckit.*
.opencode/command/opsx-*
```

**Alternatives considered**:
- `ai/commands/` — tool-neutral but OpenCode cannot auto-discover from non-standard paths
- Commit all commands — creates maintenance burden when framework updates
- Symlinks — fragile, platform-dependent

## R3: Skills Directory Structure

**Decision**: `.agents/skills/` with `.gitkeep` (agent-agnostic discovery path)

**Rationale**: OpenCode discovers skills from `.agents/skills/`, `.opencode/skills/`, and `.claude/skills/` (project-local) or their global equivalents. The committed, agent-agnostic path is `.agents/skills/`. This is discoverable by OpenCode and other compatible tools without coupling to any specific agent directory. Skills placed elsewhere (e.g., `ai/skills/`) are not loaded by OpenCode.

**Alternatives considered**:
- `ai/skills/` — initially chosen (T001), reverted. Not in OpenCode's discovery paths. Skills would not be auto-loaded.
- `.opencode/skills/` — OpenCode-specific; less discoverable by other tools
- No directory at all — user requested the structure be created for organic growth

## R4: Documentation Strategy

**Decision**: Single `docs/AI_TOOLING.md` covering setup, commands, skills, and multi-tool guidance

**Rationale**: A single README serves as the entry point for all AI tooling. Covers all audience levels: first-time contributors (getting started), regular users (command usage), and maintainers (creating commands and skills). Target: under 3 minutes to read.

**Alternatives considered**:
- Multiple docs (SETUP.md, SKILLS.md, COMMANDS.md) — splits information, harder to discover
- Root-level AI_TOOLING.md — clutters root alongside README.md
- Dedicated `ai/` directory — adds a directory for a single file when `docs/` already exists
- Only inline comments — insufficient for onboarding

## R5: Review PR Command Design

**Decision**: Single-pass, token-efficient review command with CI-aware triage and fix-branch capability

**Rationale**: A 9-step flow that delegates deterministic checks (lint, tests) to local tools and CI before applying AI judgment. Key capabilities: (1) CI failure causality determination (PR-caused vs. pre-existing), (2) local tool pre-flight, (3) AI-only review for alignment/security/compliance, (4) fix-branch for pre-existing failures, (5) in-line PR comments with mandatory human confirmation.

**Alternatives considered**:
- Multi-agent review council — too complex for initial adoption
- Minimal linting-only review — does not address alignment or security
- External review tool integration — adds dependencies unnecessarily

## R6: Agent Context File Strategy

**Decision**: AGENTS.md committed (auto-derived), CLAUDE.md gitignored (local-only)

**Rationale**: AGENTS.md provides repository-specific instructions derived from the constitution and feature plans via `update-agent-context.sh`. It is tool-neutral and committed. CLAUDE.md is Claude-specific and maintained locally by contributors who use Claude Code. This keeps committed content tool-neutral while allowing tool-specific local context.

**Alternatives considered**:
- No committed agent context — insufficient; AGENTS.md provides essential repo structure and constraints for AI agents
- CLAUDE.md committed — tool-specific, contradicts the "only commit tool-neutral content" principle

## R7: Sync Strategy for Organization Replication

**Decision**: Add AI tooling files to `sync-config.yml` for distribution via existing sync mechanism

**Rationale**: The sync mechanism distributes configuration files across org repositories. Adding the AI tooling files enables automatic replication without manual setup in target repos.

**Synced files**:
- `.specify/memory/constitution.md` — governance standards
- `docs/AI_TOOLING.md` — AI tooling documentation
- `.agents/skills/.gitkeep` — skill directory structure
- `.opencode/command/review_pr.md` — PR review command

**Considerations**:
- Constitution allows per-repo increments (tighten SHOULD → MUST, never relax MUST)
- Review command serves as baseline; repos may add repo-specific commands
- `.gitignore` patterns may need per-repo adjustments for non-standard setups

## R8: Dual-Directory Spec Model

**Decision**: `specs/` for SpecKit, `openspec/` for OpenSpec — both coexist with coordinated sequential numbering

**Rationale**: Each framework uses its native output directory. Cross-referencing via shared naming conventions (sequential numbering, descriptive short names) bridges history across directories. Each framework reads from the other's directory when it needs historical context (e.g., to assign the next sequential number or review prior decisions).

**Numbering coordination**: Branch-based. Each feature branch picks the next available number by scanning both directories at creation time. Collisions (from concurrent branches picking the same number) are detected at PR merge and resolved by renumbering the later-merged feature.

**Spec format**: Framework-native. Each framework uses its own template without custom structural enforcement. Cross-directory reading relies on specs being human-readable as-is.

**Migration**: No migration. Existing SpecKit specs (001-004) remain in `specs/`. New OpenSpec features go to `openspec/`. Unified sequential numbering preserves chronological continuity.

**Alternatives considered**:
- Single directory for both — overrides one framework's native convention
- Mirror/symlink strategy — adds complexity for marginal discoverability benefit
- Centralized registry for numbering — unnecessary overhead; branch-based coordination is sufficient
- Standardized template across frameworks — over-constrains frameworks, adds maintenance burden

## R9: Cross-Framework Portability

**Decision**: Spec-level portability only

**Rationale**: The spec file (in each framework's output directory) is the shared contract between frameworks. Plans and tasks are framework-specific but human-readable. A contributor using a different framework than the one that started the feature can read the spec and restart their own framework's planning workflow. Seamless mid-feature handoff is not guaranteed — this avoids coupling the two frameworks' internal formats.

**Alternatives considered**:
- Full portability (identical plan/task formats) — impractical; couples framework internals
- No portability (each feature owned by one framework) — too restrictive; spec-level sharing is valuable
