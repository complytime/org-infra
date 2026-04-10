# Data Model: Standardize AI Tooling

**Branch**: `004-standardize-ai-tooling` | **Date**: 2026-04-09 (updated)

This feature is file-based (no database entities). The "data model" describes the file structure, ownership, and relationships.

## File Taxonomy

All files fall into one of two categories:

```
┌─────────────────────────────────────────────────────┐
│                  COMMITTED                          │
│  (project-specific, tool-neutral, version-controlled)│
│                                                     │
│  .specify/memory/          │                        │
│    constitution.md ────────┐                        │
│  docs/AI_TOOLING.md        │ consumed by            │
│  .agents/skills/           │ all frameworks         │
│    .gitkeep                │                        │
│  .opencode/command/        │                        │
│    review_pr.md            │                        │
│  specs/        ────────────┤ SpecKit output         │
│  openspec/     ────────────┤ OpenSpec output        │
│  AGENTS.md     ────────────┤ agent context          │
│  .gitignore ───────────────┴── enforces boundary    │
│  sync-config.yml ──────── distributes committed     │
│                           files across org          │
└─────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────┐
│                  GITIGNORED                         │
│  (tool-managed, local-only, not version-controlled) │
│                                                     │
│  .specify/scripts/     ── framework scripts         │
│  .specify/templates/   ── framework templates       │
│  .opencode/command/    ── framework commands         │
│    speckit.*, opsx-*      (by name pattern)         │
│  .opencode/node_modules/                            │
│  .opencode/package.json                             │
│  .opencode/package-lock.json                        │
│  .opencode/bun.lock                                 │
│  .opencode/.gitignore                               │
│  .claude/              ── tool directory             │
│  .cursor/              ── tool directory             │
│  CLAUDE.md             ── tool agent context         │
└─────────────────────────────────────────────────────┘
```

## Entity Descriptions

### Constitution (`.specify/memory/constitution.md`)

| Attribute | Value |
|-----------|-------|
| Location | `.specify/memory/constitution.md` |
| Format | Markdown with RFC 2119 language |
| Ownership | Org-infra maintainers (canonical); other repos reference or increment |
| Consumers | OpenSpec, SpecKit, any future spec framework, human contributors |
| Versioned | Yes (semver in document footer: v1.2.0) |
| Synced | Yes (distributed to all org repos) |

**Relationships**:
- Referenced by framework commands (OpenSpec, SpecKit) at runtime
- Referenced by `review_pr.md` for compliance checking (Step 6c)
- Referenced by skills dynamically (by path)
- Incrementable by repository-specific constitutions (tighten SHOULD → MUST, never relax MUST)

### Project-Specific Command (`review_pr.md`)

| Attribute | Value |
|-----------|-------|
| Location | `.opencode/command/review_pr.md` |
| Format | Markdown with YAML frontmatter (`description` field) |
| Ownership | Org-infra maintainers |
| Consumers | OpenCode (auto-discovered from `.opencode/command/`) |
| Arguments | PR number (required) |
| Synced | Yes (distributed to all org repos) |

**Relationships**:
- References `.specify/memory/constitution.md` for compliance standards
- References both `specs/` and `openspec/` directories for specification alignment (Step 5)
- Uses `gh` CLI for PR metadata, CI checks, and in-line comments

### Skills Directory (`.agents/skills/`)

| Attribute | Value |
|-----------|-------|
| Location | `.agents/skills/` (agent-agnostic discovery path) |
| Format | Directory with `.gitkeep` (empty initially) |
| Ownership | Contributors (create skills), maintainers (review) |
| Consumers | OpenCode and other compatible AI tools (auto-discovered) |
| Synced | Yes (directory structure only) |

**Skill schema** (for future skills at `.agents/skills/<name>/SKILL.md`):
- Required frontmatter: `name`, `description`
- Optional frontmatter: `license`, `compatibility`, `metadata`
- Body: Markdown instructions

**Relationships**:
- Skills reference `.specify/memory/constitution.md` dynamically
- Skill creation process documented in `ai/README.md`
- Discovery paths: `.agents/skills/`, `.opencode/skills/`, `.claude/skills/` (project-local)

### Documentation (`docs/AI_TOOLING.md`)

| Attribute | Value |
|-----------|-------|
| Location | `docs/AI_TOOLING.md` |
| Format | Markdown |
| Ownership | Org-infra maintainers |
| Consumers | All contributors |
| Synced | Yes (distributed to all org repos) |

**Relationships**:
- Links to `.specify/memory/constitution.md`
- Documents skill creation process (references `.agents/skills/`)
- Documents command usage (references `.opencode/command/`)
- Documents dual-directory spec model (`specs/` + `openspec/`)

### Spec Directories (`specs/` and `openspec/`)

| Attribute | `specs/` | `openspec/` |
|-----------|----------|-------------|
| Framework | SpecKit | OpenSpec |
| Status | Exists (features 001-004) | Created when first OpenSpec feature is made |
| Format | Framework-native template | Framework-native template |
| Naming | `NNN-descriptive-name/` | `NNN-descriptive-name/` |
| Numbering | Coordinated across both directories | Coordinated across both directories |

**Numbering rules**:
- Next number = max(all numbers across `specs/` + `openspec/`) + 1
- Branch-based coordination: each feature branch picks next number at creation time
- Collision resolution: later-merged feature is renumbered at PR merge

**Relationships**:
- `review_pr.md` searches both directories for associated specifications (Step 5)
- Each spec references `.specify/memory/constitution.md` for standards
- Plans and tasks within each spec directory are framework-specific but human-readable

### Gitignore (`.gitignore`)

| Attribute | Value |
|-----------|-------|
| Location | Repository root |
| Format | Gitignore pattern syntax |
| Ownership | Org-infra maintainers |
| Consumers | Git |
| Synced | Yes (merged into target repo gitignore, not overwritten) |

**Relationships**:
- Enforces the committed/gitignored boundary for all other files
- Patterns reference framework directories and command name prefixes

### Agent Context (`AGENTS.md`)

| Attribute | Value |
|-----------|-------|
| Location | Repository root |
| Format | Markdown |
| Ownership | Auto-derived via `update-agent-context.sh` |
| Consumers | OpenCode and other AI agents |
| Synced | No (repo-specific content) |

**Relationships**:
- Derived from `.specify/memory/constitution.md` and feature plans
- References repo structure, `make` commands, constraints
- Updated during `/speckit.plan` workflows

## Lifecycle

```
1. Initial setup (this feature):
   constitution.md stays at .specify/memory/ (not moved)
   .agents/skills/.gitkeep created (agent-agnostic path)
   .opencode/command/review_pr.md created
   docs/AI_TOOLING.md created
   .gitignore created
   sync-config.yml updated
   AGENTS.md updated

2. Ongoing usage:
   Contributors clone → install AI agent + spec framework → ready to code/review
   SpecKit features → specs/NNN-name/
   OpenSpec features → openspec/NNN-name/
   Next number scans both directories
   Maintainers update constitution → all tools see updated version
   Contributors create skills → placed in .agents/skills/ → reviewed via PR

3. Collision handling:
   Two concurrent branches pick same number →
   Detected at PR merge → later-merged feature renumbered

4. Org replication:
   sync mechanism distributes files to org repos
   Each repo inherits AI tooling setup
   Each repo may add repo-specific commands/skills
```
