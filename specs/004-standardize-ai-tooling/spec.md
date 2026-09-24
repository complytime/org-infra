# Feature Specification: Standardize AI Tooling

**Feature Branch**: `004-standardize-ai-tooling` | **Created**: 2026-04-08 | **Status**: Draft

**Input**: User description: "create a feature to standardize the use of AI tools in this repository so contributors can clone and already start coding or reviewing PRs with their AI tools using commands, skills, and agent definitions defined by the repository maintainers. While these files should be as generic as possible regarding tooling so users can quickly reuse them with different agents, it should also be opinionated about OpenCode as the standardized agent tool. All the projects can also use SpecKit and OpenSpec but ideally both should have the same source of truth (constitution.md) so there is no duplication. Also new features, created with SpecKit or OpenSpec should be standardized in the specs directory so we keep a clear history of changes. No skill is necessary initially but the definition of how to create new skills must be present. Finally, the same approach should be flexible and scalable enough to be easily replicated in multiple repositories within the same organization."

## Clarifications

### Session 2026-04-08

- Q: What is the relationship between OpenSpec and SpecKit? → A: OpenSpec and SpecKit are both agent-agnostic spec-driven development frameworks. Both share the constitution but use different output directories: SpecKit outputs to `specs/` and OpenSpec outputs to `openspec/`. They are not tied to specific AI agents — either can be used with OpenCode, Claude Code, or any other supported tool.
- Q: Which tool-specific configurations should be committed to the repository? → A: OpenCode configurations (`.opencode/`) and agent-agnostic content (`.agents/`) are committed. Tool-specific directories (e.g., `.claude/`, `.cursor/`) are local-only and not committed. The `.agents/` directory contains cross-tool content (skills) discoverable by OpenCode and other compatible agents. The committed setup serves as the canonical reference.
- Q: Which specification framework is recommended? → A: OpenSpec is the recommended spec-driven framework for the organization. SpecKit remains available as an alternative. Both are agent-agnostic.
- Q: Should spec framework commands (OpenSpec/SpecKit) be committed to the repository? → A: No. Spec framework commands are managed by each tool's plugin/package system and not committed. The repository commits only project-specific content (constitution, agent configuration, spec outputs). This eliminates the maintenance burden of manually updating commands across repos when new framework versions are released.
- Q: What parts of `.specify/` should be committed vs. tool-managed? → A: Only project-specific content is committed (constitution, extension configuration). Framework-provided content (`.specify/scripts`, `.specify/templates`) is tool-managed and gitignored, following the established pattern in complyctl. A standardized `.gitignore` file enforces these boundaries.
- Q: How can OpenSpec know about `.specify/memory/constitution.md` since that path is a SpecKit convention? → A: The constitution is a project-specific file committed at `.specify/memory/constitution.md` — SpecKit's standard path. This is not framework infrastructure (like scripts or templates); it is project content that both frameworks consume. OpenSpec discovers it at this well-known path by convention. Moving it would break SpecKit's hardcoded references without benefit, since the file is project-owned, not framework-owned.

### Session 2026-04-09

- Q: Can a feature started with one framework be seamlessly continued by a contributor using a different framework? → A: Spec-level portability only. The spec file (in each framework's respective output directory) is the shared contract. Plans and tasks are framework-specific but human-readable. Mid-feature handoff between frameworks is not a guaranteed workflow.
- Q: How should the two spec directories (`specs/` for SpecKit, `openspec/` for OpenSpec) relate so each framework benefits from the other's history? → A: Both directories coexist and are committed. Each framework uses its native output directory. Cross-reference and shared naming conventions (sequential numbering, descriptive names) bridge history across directories. Each framework reads from the other's directory when it needs historical context (e.g., sequential numbering, prior decisions).
- Q: How should sequential numbering collisions be prevented when contributors create features concurrently with different frameworks? → A: Branch-based coordination. Each feature branch picks the next available number at creation time by scanning both directories. Collisions are resolved at PR merge by renumbering the later-merged feature.
- Q: Should both frameworks enforce a minimal shared section structure in their spec output for cross-directory readability? → A: No. Each framework uses its native template without custom enforcement. Cross-directory reading relies on specs being human-readable as-is, not on mandated structural alignment.
- Q: Should existing SpecKit specs in `specs/` be migrated to `openspec/` now that OpenSpec is recommended? → A: No migration. Existing specs remain in `specs/`. New OpenSpec features go to `openspec/`. Unified sequential numbering across both directories bridges historical continuity without moving files.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Clone and Immediately Use AI Tools (Priority: P1)

A contributor clones the repository and wants to start coding or reviewing PRs using their preferred AI agent. They install the recommended spec framework plugin for their tool, and the tool automatically picks up the repository's project-specific configuration — including the constitution and agent context — while the framework plugin provides scripts, templates, and commands.

**Why this priority**: This is the core value proposition — low-friction onboarding for AI-assisted development. If contributors cannot quickly start using AI tools after cloning and installing the recommended framework, the feature fails its primary goal.

**Independent Test**: Can be fully tested by cloning the repository into a fresh environment, installing the OpenSpec plugin in OpenCode, and verifying that all commands work against the repository's committed project-specific content without additional configuration.

**Acceptance Scenarios**:

1. **Given** a freshly cloned repository and a contributor with the OpenSpec plugin installed, **When** the contributor opens it in OpenCode, **Then** all framework commands are available and the agent has access to the repository's constitution and coding standards.
2. **Given** a freshly cloned repository, **When** a contributor opens it in a different AI agent (e.g., Claude Code), **Then** the contributor can install their preferred spec framework (OpenSpec or SpecKit) and reference the committed project-specific content and documentation to start working.
3. **Given** a freshly cloned repository, **When** the contributor runs a framework command (e.g., to specify a feature), **Then** the command executes correctly, with the framework plugin providing scripts and templates while the repository provides the constitution and project-specific configuration.

---

### User Story 2 - Maintain Single Source of Truth for AI Context (Priority: P1)

A repository maintainer wants to ensure that all AI tools — whether using OpenSpec or SpecKit — reference the same constitution.md for their understanding of organizational standards. Since framework commands, scripts, and templates are tool-managed (not committed), the constitution serves as the single source of truth that all tools consume. When the constitution is updated, all tools automatically see the updated version.

**Why this priority**: Without a single source of truth, configurations drift apart, leading to inconsistent AI behavior and conflicting guidance. This is foundational to all other stories.

**Independent Test**: Can be fully tested by modifying the constitution and verifying that framework commands (provided by the tool plugin) reference the updated content without any additional file changes.

**Acceptance Scenarios**:

1. **Given** a repository with the constitution at its canonical location, **When** an OpenSpec command runs (provided by the plugin), **Then** it references the constitution from the committed location and not from a duplicated copy.
2. **Given** a repository with the constitution at its canonical location, **When** a contributor uses SpecKit, **Then** it references the same committed constitution file as OpenSpec.
3. **Given** a maintainer updates the constitution, **When** any framework command runs afterward, **Then** the command uses the updated constitution without requiring changes to tool-specific configuration files or command definitions.

---

### User Story 3 - Define and Manage Agent Configurations (Priority: P2)

A repository maintainer wants to define AI agent configurations — including commands, agent context, and skill definitions — in a standard directory structure. The structure must be clear enough that new maintainers can understand where configurations live and how to modify them.

**Why this priority**: Maintainers need a predictable structure to manage AI tool configurations. This is essential for long-term maintenance but depends on the foundational single-source-of-truth (P1) being in place first.

**Independent Test**: Can be fully tested by having a new maintainer (unfamiliar with the repository) locate and modify an agent command by following the documented directory structure.

**Acceptance Scenarios**:

1. **Given** a repository with the standardized AI tooling structure, **When** a maintainer wants to add a new project-specific command, **Then** there is a documented location and format for creating the command, distinct from the framework-provided commands.
2. **Given** a contributor using a non-OpenCode AI tool, **When** they need equivalent framework commands, **Then** they can install the corresponding framework plugin for their tool and reference the committed project-specific content (constitution, agent context) and documentation.
3. **Given** a repository with agent context files, **When** a maintainer needs to update agent instructions, **Then** the changes propagate to the agent context without requiring updates in multiple places.

---

### User Story 4 - Standardize Feature Specs Across Spec Directories (Priority: P2)

A contributor uses either SpecKit or OpenSpec to create a new feature specification. Each tool outputs to its native directory (`specs/` for SpecKit, `openspec/` for OpenSpec), but both use the same sequential numbering convention coordinated across directories, maintaining a clear and auditable chronological history of all feature changes.

**Why this priority**: Consistent spec location and naming is critical for project governance and change tracking, but it requires the AI tooling infrastructure (P1) to be functional first.

**Independent Test**: Can be fully tested by creating a feature spec using each supported tool and verifying that SpecKit outputs to `specs/` and OpenSpec outputs to `openspec/`, both using coordinated sequential numbering with no duplicate numbers across directories.

**Acceptance Scenarios**:

1. **Given** a contributor creates a feature using OpenSpec (recommended), **When** the feature creation completes, **Then** the specification is stored in the `openspec/` directory with a sequential number prefix and descriptive name, using the next available number across both `specs/` and `openspec/` directories.
2. **Given** a contributor creates a feature using SpecKit, **When** the feature creation completes, **Then** the specification is stored in the `specs/` directory with the same sequential numbering convention, coordinated across both directories.
3. **Given** multiple features have been created by different tools over time, **When** a maintainer reviews both the `specs/` and `openspec/` directories, **Then** the sequential numbering across both directories forms a unified chronological timeline with no duplicate numbers.

---

### User Story 5 - Document Skill Creation Process (Priority: P3)

A contributor wants to extend the AI tooling by creating a new skill for a specific workflow (e.g., security review, compliance checking). While no skills exist initially, there is clear documentation on how to create, structure, and register new skills so the tooling can grow organically.

**Why this priority**: Skills are an extensibility mechanism that becomes important as the team matures its AI-assisted workflows, but they are not required for initial adoption.

**Independent Test**: Can be fully tested by following the skill creation documentation to create a sample skill at `.agents/skills/<name>/SKILL.md` and verifying the skill appears in OpenCode's available skills list.

**Acceptance Scenarios**:

1. **Given** the repository has skill creation documentation, **When** a contributor follows the documented process to create a new skill, **Then** the resulting skill follows the defined structure and is placed in the correct directory.
2. **Given** a skill has been created following the documentation, **When** a contributor invokes the skill in their AI tool, **Then** the skill loads and provides the expected specialized instructions.

---

### User Story 6 - Replicate AI Tooling Across Organization Repositories (Priority: P3)

An organization administrator wants to establish the same AI tooling standardization in other repositories within the organization. The configuration from the central repository (org-infra) can be replicated to other repositories through the existing sync mechanism, so each repository inherits the organization's AI tooling standards.

**Why this priority**: Organization-wide adoption multiplies the value of this feature but requires the pattern to be proven in org-infra first.

**Independent Test**: Can be fully tested by adding AI tooling configuration files to the sync configuration and running a dry-run sync to verify the correct files would be distributed to target repositories.

**Acceptance Scenarios**:

1. **Given** the AI tooling configuration is defined in org-infra, **When** the sync mechanism runs, **Then** target repositories receive the AI tooling configuration files appropriate for their type.
2. **Given** a target repository has received synced AI tooling files, **When** a contributor clones that repository, **Then** they have a working AI tooling setup that follows organization standards.
3. **Given** the organization updates its constitution or AI tooling standards in org-infra, **When** the sync mechanism runs, **Then** all target repositories are updated with the new standards.

---

### Edge Cases

- What happens when a contributor uses an AI tool other than OpenCode? The contributor installs the corresponding spec framework plugin for their tool and references the committed project-specific content (constitution at `.specify/memory/constitution.md`, agent context) and documentation. The constitution is accessible to all tools regardless of which framework provides the commands, scripts, and templates.
- What happens when SpecKit and OpenSpec have conflicting commands or behaviors? The constitution.md serves as the arbiter; both frameworks must conform to the constitution's directives. Since commands, scripts, and templates are tool-managed, conflicts are resolved at the framework level, not in the repository.
- What happens when a new version of the spec framework is released? Contributors update their local framework plugin/package. No repository changes are needed since commands, scripts, and templates are not committed.
- What happens when a contributor accidentally commits tool-managed files? The standardized `.gitignore` prevents this by explicitly excluding framework-provided files (commands, scripts, templates) and tool-specific directories.
- What happens when the sync mechanism distributes AI configuration to a repository that has its own customizations? The repository's local customizations take precedence per the constitution's principle that repositories may tighten (but not relax) organizational standards.
- What happens when a skill references a constitution section that has been amended? Skills reference the constitution dynamically (by path), so they always reflect the current version.
- What happens when CI checks are still pending during a PR review? The review command informs the user that checks are pending and asks whether to wait or proceed with the available results. Pending checks are not treated as failures.
- What happens when the base branch has no CI history for a failing check? The review command treats the failure as "unknown causality" and conservatively classifies it as PR-caused, noting the lack of base branch data.
- What happens when the proposed fix-branch does not resolve the pre-existing CI failure? The review command creates the branch with the best-effort fix and notes that the fix is proposed, not guaranteed. If the failure is non-trivial, the command informs the user instead of attempting an automated fix.
- What happens when a skill is created outside the supported discovery paths? OpenCode discovers skills from `.agents/skills/`, `.opencode/skills/`, and `.claude/skills/` (project-local) or their global equivalents. The committed, agent-agnostic path is `.agents/skills/`. Skills placed elsewhere (e.g., `ai/skills/`) will not be loaded. The documentation MUST direct contributors to `.agents/skills/`.
- What happens when a contributor wants to continue a feature started by another contributor using a different spec framework? The spec file (in the originating framework's output directory) is the shared contract. The continuing contributor can read the spec and any framework-specific plans/tasks (which are human-readable) but starts their own framework's planning workflow from the existing spec. Seamless mid-feature handoff between frameworks is not guaranteed.
- What happens when two contributors concurrently create features with different frameworks and pick the same sequential number? The collision is detected at PR merge time. The later-merged feature is renumbered to the next available number across both `specs/` and `openspec/` directories. This is a lightweight resolution that requires no centralized registry.
- What happens to existing SpecKit specs when OpenSpec is adopted as the recommended framework? Existing specs remain in `specs/` and are not migrated. New features created with OpenSpec go to `openspec/`. The unified sequential numbering across both directories preserves chronological continuity without file moves that would break branch references and internal links.
- What happens when the constitution is moved away from `.specify/memory/constitution.md`? SpecKit hardcodes this path in its commands. Moving the constitution breaks SpecKit. The constitution MUST remain at `.specify/memory/constitution.md` — it is project-specific content, not framework infrastructure.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The repository MUST include a standardized directory structure for AI tool configurations that is documented and discoverable by contributors.
- **FR-002**: The repository MUST designate OpenCode as the standardized AI agent tool and OpenSpec as the recommended spec-driven framework.
- **FR-003**: Spec framework commands, scripts, and templates (OpenSpec, SpecKit) MUST NOT be committed to the repository. They are managed by each tool's plugin/package system. The repository MUST commit only project-specific content: the constitution (at `.specify/memory/constitution.md`), extension configuration, project-specific commands, and spec outputs (`specs/` and `openspec/`). Framework-provided commands within `.opencode/command/` MUST be excluded via `.gitignore` patterns (e.g., `speckit.*`, `opsx-*`), while project-specific commands (e.g., `review_pr.md`) MAY be committed. Tool-specific directories (`.claude/`, `.cursor`, etc.) and framework infrastructure (`.specify/scripts`, `.specify/templates`) MUST be excluded via `.gitignore`.
- **FR-004**: All specification tools (SpecKit, OpenSpec, and any future tools) MUST reference the same constitution.md file as their single source of truth for organizational standards, with no duplicated copies. In org-infra, the canonical path is `.specify/memory/constitution.md` (SpecKit's standard location). This file is project-specific content, not framework infrastructure — it is committed to the repository and consumed by all spec frameworks at this well-known path. OpenSpec and any future tools MUST discover the constitution at this location.
- **FR-005**: Features created by SpecKit MUST be stored in the `specs/` directory and features created by OpenSpec MUST be stored in the `openspec/` directory, each following the same naming convention (sequential numbering prefix and descriptive short name). Both directories MUST be committed. Sequential numbering MUST be coordinated across both directories to maintain a unified chronological history (e.g., if `specs/003-*` exists, the next feature in either directory is `004-*`). Each feature branch picks the next available number by scanning both directories at creation time; if concurrent branches produce duplicate numbers, the later-merged feature MUST be renumbered at PR merge. Accompanying artifacts (plans, tasks, checklists) are framework-specific but MUST be human-readable so contributors using a different framework can understand the feature's history.
- **FR-006**: The repository MUST include documentation on how to create new skills at `.agents/skills/<name>/SKILL.md` (agent-agnostic discovery path, supported by OpenCode and other compatible tools), covering the expected directory structure, SKILL.md frontmatter schema (required: `name`, `description`; optional: `license`, `compatibility`, `metadata`), and discovery mechanism, even though no skills are shipped initially.
- **FR-007**: The agent context file MUST be automatically derivable from the constitution and feature plans, avoiding manual duplication of organizational standards.
- **FR-008**: The committed project-specific AI tooling content (constitution, agent context, `.gitignore`) MUST be structured so that it can be distributed to other repositories in the organization through the existing sync mechanism.
- **FR-009**: The repository MUST include documentation that describes the committed project-specific content, how to install the recommended spec framework (OpenSpec), and how contributors using other tools can set up their equivalent framework plugin.
- **FR-010**: The committed project-specific content (constitution, extension configuration) MUST be tool-agnostic, enabling any spec framework (OpenSpec, SpecKit, or future frameworks) to consume it without modification. Spec output format is framework-native — each framework uses its own template without custom structural enforcement.
- **FR-011**: The repository MUST include a standardized `.gitignore` file that enforces the boundary between committed project-specific content and tool-managed files. This `.gitignore` MUST exclude framework-provided files (commands, scripts, templates), tool-specific directories, and agent-specific local files, following the established organizational pattern.
- **FR-012**: Project-specific AI commands that perform code analysis MUST delegate deterministic checks (linting, formatting, testing, coverage) to locally available tools before applying AI judgment. The deterministic tools available in the project are informed by the Coding Standards section of the constitution. AI tokens MUST only be spent on judgment-based analysis that tools cannot perform (intent alignment, security pattern recognition, architectural concerns).
- **FR-013**: The PR review command MUST offer the option to post in-line comments on the PR after presenting findings, so the author can see feedback in context. All in-line comments MUST be shown to and explicitly confirmed by a human before being posted to the PR.
- **FR-014**: The PR review command MUST fetch and analyze CI check suite results for the PR. For each failing check, the command MUST determine causality: whether the failure is caused by the PR's changes or is a pre-existing issue on the base branch. PR-caused failures MUST be reported to the author as review findings. Pre-existing failures MUST be clearly distinguished from PR-caused failures in the review output.
- **FR-015**: When the PR review command identifies a CI failure that is NOT caused by the PR's changes (pre-existing or independent issue), it MUST offer to create a separate fix branch with a proposed resolution. The fix branch MUST follow the project's branching conventions and use Conventional Commits. The agent MUST NOT file a PR automatically — it creates the branch and commits locally so a human reviewer can inspect the changes and file a PR when ready.

### Key Entities

- **Constitution**: The organizational governance document (constitution.md) that defines principles, standards, and workflows. Serves as the single source of truth for all AI tools.
- **Agent Context File**: A configuration file that provides the AI agent with repository-specific instructions, derived from the constitution and feature plans. The committed version is tool-agnostic where possible; tool-specific agent context files (e.g., CLAUDE.md) are maintained locally by each contributor.
- **Command**: A reusable prompt template that AI tools execute. Framework commands (OpenSpec, SpecKit) are provided by the tool's plugin/package system and NOT committed. Project-specific custom commands may be committed separately.
- **Skill**: A specialized instruction set that provides domain-specific workflows and guidance to an AI agent, defined as a `SKILL.md` file with YAML frontmatter (required: `name`, `description`) inside `.agents/skills/<name>/`. OpenCode and other agent-compatible tools discover skills automatically from this path. Skills are optional extensions to the base configuration.
- **Project-Specific Content**: The committed, tool-agnostic content in the repository — specifically the constitution (at `.specify/memory/constitution.md`), extension configuration, agent context, and spec outputs. Consumed by all spec frameworks. Distinguished from framework-provided files (scripts, templates, commands) which are tool-managed.
- **OpenSpec**: The recommended specification framework for the organization. Agent-agnostic — works with OpenCode, Claude Code, and other supported AI tools. Provides commands, scripts, and templates for spec-driven development (specify, plan, implement, etc.) via its plugin/package system (not committed). Consumes the committed project-specific content and outputs specs to the `openspec/` directory.
- **SpecKit**: An alternative spec-driven development framework. Agent-agnostic — works with any supported AI tool, not tied to a specific agent. Provides equivalent commands, scripts, and templates via its own distribution mechanism (not committed). Consumes the same committed project-specific content as OpenSpec and outputs specs to the `specs/` directory.
- **Spec**: A feature specification document created by either SpecKit (stored in `specs/`) or OpenSpec (stored in `openspec/`), following a numbered naming convention with sequential numbers coordinated across both directories.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: A new contributor can clone the repository and execute a spec framework command within 5 minutes of setup, with no manual configuration beyond installing the AI tool and its spec framework plugin.
- **SC-002**: 100% of specification tool commands reference the constitution from a single canonical location, with zero duplicated copies of the constitution across tool configurations.
- **SC-003**: All features created by any specification tool are stored in their framework's native directory (`specs/` for SpecKit, `openspec/` for OpenSpec) following the same naming convention with coordinated sequential numbering across both directories, verifiable by listing both directories and confirming no duplicate numbers exist.
- **SC-004**: The skill creation documentation enables a contributor to create a functional skill at `.agents/skills/<name>/SKILL.md` by following the documented steps, and the skill appears in OpenCode's available skills list without requiring additional configuration.
- **SC-005**: The project-specific AI tooling content (constitution, agent context, `.gitignore`) can be replicated to a new repository in the organization by adding it to the sync configuration, requiring no manual file copying or custom setup in the target repository. Framework commands, scripts, and templates are not part of the sync — they are provided by each contributor's tool plugin.
- **SC-006**: The PR review command runs locally available deterministic tools (linters, tests) before AI analysis, and skips AI review of categories where tools or CI already passed, verifiable by the "Local Tool Results" section in the review output.
- **SC-007**: The PR review command correctly classifies CI failures as PR-caused or pre-existing by comparing against the base branch, verifiable by running the command on a PR with a known pre-existing failure and confirming it is not attributed to the PR author.
- **SC-008**: When a pre-existing CI failure is identified, the review command can create a local fix branch with a Conventional Commit that does not get pushed or filed as a PR automatically, verifiable by inspecting the local git branch after the command completes.

## Assumptions

- Contributors have access to at least one supported AI tool (OpenCode being the primary recommendation) and install a spec framework plugin (OpenSpec recommended, SpecKit as alternative — both are agent-agnostic).
- The `.specify/` directory contains both framework infrastructure and project-specific content. Framework-provided files (`.specify/scripts`, `.specify/templates`) are tool-managed and gitignored. Project-specific files (`.specify/memory/constitution.md`, `.specify/extensions/` configuration) are committed. The constitution at `.specify/memory/constitution.md` is project content consumed by all spec frameworks, not framework infrastructure.
- OpenSpec is the recommended specification framework for the organization. SpecKit is an alternative. Both are agent-agnostic (not tied to specific AI tools) and share the same constitution. SpecKit outputs to `specs/` and OpenSpec outputs to `openspec/`; sequential numbering is coordinated across both directories. Neither framework's commands are committed — they are managed by each tool's plugin/package system.
- The existing `sync-config.yml` and sync mechanism in org-infra is the established method for distributing configuration files across organization repositories.
- The constitution.md resides at `.specify/memory/constitution.md` — SpecKit's standard path. Both OpenSpec and SpecKit discover it at this well-known location by convention. This path is a project convention, not a framework dependency, since the file is committed project content.
- Individual repositories may extend the AI tooling configuration with repository-specific commands (in `.opencode/command/`) and skills (in `.agents/skills/`), following the constitution's principle that repositories may tighten but not relax organizational standards.
