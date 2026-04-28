## ADDED Requirements

### Requirement: Per-repo AI guide renamed and restructured

Each repository SHALL contain a `docs/AI.md` file (renamed from `docs/AI_TOOLING.md`)
that serves as the operational guide for AI-assisted development in that repository.
The file SHALL be synced from org-infra to all repositories included in the sync
configuration and SHALL be designed to also work when manually copied to excluded
repositories.

#### Scenario: File renamed from AI_TOOLING.md to AI.md

- **WHEN** the sync runs after this change
- **THEN** repositories receive `docs/AI.md` instead of `docs/AI_TOOLING.md`

#### Scenario: Document references community standard

- **WHEN** a contributor reads `docs/AI.md`
- **THEN** the document links to `community/AI_NATIVE_DEVELOPMENT.md` for the
  org-wide AI development philosophy and workflow

#### Scenario: Convention packs section included

- **WHEN** a contributor looks for convention pack information in the per-repo guide
- **THEN** `docs/AI.md` explains which convention packs are present, the pack
  hierarchy (custom extends generic, generic must not contradict constitution), and
  how to customize packs

#### Scenario: Commands section covers available commands

- **WHEN** a contributor opens the per-repo guide
- **THEN** the document lists available commands (`/review_pr`, speckit pipeline,
  openspec commands) with brief descriptions and invocation examples

#### Scenario: Key files table is updated

- **WHEN** a contributor needs to understand which files are relevant for AI
  development
- **THEN** the key files table includes: constitution, convention packs, AGENTS.md,
  Divisor agents, review command, spec directories

#### Scenario: Document works when manually copied

- **WHEN** a repository excluded from sync (e.g., complyscribe) manually copies
  `docs/AI.md`
- **THEN** the document functions correctly without any org-infra-specific
  assumptions or broken references

#### Scenario: Creating commands and skills guidance preserved

- **WHEN** a contributor wants to create a new command or skill
- **THEN** `docs/AI.md` retains the existing guidance on file structure, frontmatter,
  and writing effective commands and skills

### Requirement: Sync configuration updated for renamed file

The `sync-config.yml` SHALL be updated to reflect the rename from
`docs/AI_TOOLING.md` to `docs/AI.md` and SHALL add the 5 Divisor agent files and
the council review consumer workflow to the sync list.

#### Scenario: AI guide path updated in sync config

- **WHEN** the sync script runs
- **THEN** it syncs `docs/AI.md` (not `docs/AI_TOOLING.md`) to all target
  repositories

#### Scenario: Divisor agent files added to sync config

- **WHEN** the sync script runs
- **THEN** it syncs `.opencode/agents/divisor-guard.md`,
  `.opencode/agents/divisor-architect.md`,
  `.opencode/agents/divisor-adversary.md`,
  `.opencode/agents/divisor-testing.md`, and
  `.opencode/agents/divisor-sre.md` to target repositories, with repo-specific
  exclusions for repositories that maintain custom persona definitions

#### Scenario: Council review consumer workflow added to sync config

- **WHEN** the sync script runs
- **THEN** it syncs `.github/workflows/ci_council_review.yml` to all target
  repositories

### Requirement: AGENTS.md references updated

The org-infra `AGENTS.md` SHALL be updated to reference `docs/AI.md` instead of
`docs/AI_TOOLING.md` and SHALL document the Divisor agent files and council review
workflow.

#### Scenario: AGENTS.md references new file name

- **WHEN** a contributor or agent reads `AGENTS.md`
- **THEN** all references point to `docs/AI.md`, not `docs/AI_TOOLING.md`

#### Scenario: AGENTS.md documents Divisor agents

- **WHEN** a contributor looks for information about the review council in AGENTS.md
- **THEN** AGENTS.md describes the 5 Divisor agent files in
  `.opencode/agents/divisor-*.md` and their role in the CI council review

