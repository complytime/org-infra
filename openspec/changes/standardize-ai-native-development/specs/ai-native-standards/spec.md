## ADDED Requirements

### Requirement: Org-wide AI-native development standard document

The organization SHALL maintain a single authoritative document
(`AI_NATIVE_DEVELOPMENT.md`) in the community repository that defines the AI-native
development philosophy, workflow, file classification, convention pack system,
disclosure standards, and continuous improvement loop for all ComplyTime repositories.

#### Scenario: New contributor discovers AI workflow

- **WHEN** a contributor joins a ComplyTime repository and looks for AI development
  guidance
- **THEN** the per-repo `docs/AI.md` links to `community/AI_NATIVE_DEVELOPMENT.md`
  as the org-wide standard

#### Scenario: Document covers the 6-step workflow

- **WHEN** a contributor reads the AI-native development standard
- **THEN** the document describes the full workflow: specify → spec review
  (council + humans) → implement → code review (council + humans) → merge

#### Scenario: File classification is documented

- **WHEN** a contributor needs to determine whether a file should be committed or
  gitignored
- **THEN** the document provides a classification table distinguishing committed
  files (constitution, convention packs, AGENTS.md, review command, AI guide, specs)
  from local-only files (plugin commands, agent-specific configs, review agents,
  MCP configs)

#### Scenario: Convention pack system is explained

- **WHEN** a contributor wants to understand the convention pack hierarchy
- **THEN** the document explains the three-tier system: project custom pack extends
  generic language pack, which must not contradict the constitution

#### Scenario: Disclosure standards are defined

- **WHEN** a contributor makes an AI-assisted commit
- **THEN** the document requires an `Assisted-by` trailer identifying the tool and
  model used

#### Scenario: Agent-agnostic principle is stated

- **WHEN** a contributor uses a non-OpenCode agent (Claude Code, Cursor, etc.)
- **THEN** the document confirms that agent choice is personal and committed files
  ensure consistent outcomes regardless of agent

#### Scenario: Continuous improvement loop is documented

- **WHEN** the review council identifies a recurring pattern across PRs
- **THEN** the document describes where to capture improvements: project custom pack
  for repo-specific rules, generic pack for org-wide rules, constitution for governance
  gaps

#### Scenario: Future capabilities are excluded

- **WHEN** a reader looks for information about unleash, Dewey, or uf analyze
- **THEN** the document does not cover these capabilities (they are out of scope for
  the current standard)

### Requirement: STYLE_GUIDE.md aligned with constitution

The community `STYLE_GUIDE.md` SHALL be updated to align with constitution v1.2.0
and SHALL explicitly reference the constitution as the authoritative source for
coding standards in repositories that adopt AI-native development.

#### Scenario: RFC 2119 language alignment

- **WHEN** a reader compares STYLE_GUIDE.md directives with the constitution
- **THEN** STYLE_GUIDE.md uses RFC 2119 keywords (MUST, SHOULD, MAY) consistently
  with the constitution

#### Scenario: Python linter alignment

- **WHEN** a contributor looks for Python linting guidance
- **THEN** STYLE_GUIDE.md references `ruff` as the standard linter, not `flake8`

#### Scenario: Readability principle title alignment

- **WHEN** a contributor reads Principle IV
- **THEN** STYLE_GUIDE.md uses the title "Readability First" matching the
  constitution

#### Scenario: Constitution reference

- **WHEN** a contributor reads STYLE_GUIDE.md
- **THEN** the document states that `.specify/memory/constitution.md` in each
  repository is the authoritative source for coding standards and is managed in
  org-infra

#### Scenario: Assisted-by trailer documented

- **WHEN** a contributor reads the commit standards section
- **THEN** STYLE_GUIDE.md includes the `Assisted-by` trailer requirement for
  AI-assisted commits

#### Scenario: Lint Configuration Awareness section added

- **WHEN** a contributor looks for lint configuration guidance
- **THEN** STYLE_GUIDE.md includes a section listing standard configuration files
  (`.golangci.yml`, `ruff.toml`, `.yamllint.yml`, etc.) that agents MUST read before
  making changes

#### Scenario: Branch model consistency

- **WHEN** a contributor reads the contribution workflow
- **THEN** STYLE_GUIDE.md describes a `main` branch + feature branches model,
  consistent with the constitution

#### Scenario: AI standards cross-reference

- **WHEN** a contributor reads STYLE_GUIDE.md
- **THEN** the document links to `AI_NATIVE_DEVELOPMENT.md` for AI-specific
  development standards
