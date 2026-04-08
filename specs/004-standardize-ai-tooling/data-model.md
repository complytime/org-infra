# Data Model: Standardize AI Tooling

**Branch**: `004-standardize-ai-tooling` | **Date**: 2026-04-08

This feature is file-based (no database entities). The "data model" describes the file structure, ownership, and relationships.

## File Taxonomy

All files fall into one of two categories:

```
┌─────────────────────────────────────────────────────┐
│                  COMMITTED                          │
│  (project-specific, tool-neutral, version-controlled)│
│                                                     │
│  .specify/memory/      │                            │
│    constitution.md ────┐                            │
│  ai/README.md          │ consumed by                │
│  .agents/skills/     │ all frameworks             │
│    .gitkeep            │                            │
│  .opencode/command/    │                            │
│    review_pr.md        │                            │
│  specs/                │                            │
│  .gitignore ───────────┴── enforces boundary        │
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
│  .claude/              ── tool directory             │
│  .cursor/              ── tool directory             │
│  CLAUDE.md             ── tool agent context         │
└─────────────────────────────────────────────────────┘
```

## Entity Descriptions

### Constitution (`constitution.md`)

| Attribute | Value |
|-----------|-------|
| Location | `.specify/memory/constitution.md` |
| Format | Markdown with RFC 2119 language |
| Ownership | Org-infra maintainers (canonical); other repos reference or increment |
| Consumers | OpenSpec, SpecKit, any future spec framework, human contributors |
| Versioned | Yes (semver in document footer) |
| Synced | Yes (distributed to all org repos) |

**Relationships**:
- Referenced by framework commands (OpenSpec, SpecKit) at runtime
- Referenced by `review_pr.md` for compliance checking
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
- References `specs/` directory for specification alignment
- Uses `gh` CLI for PR data retrieval

### Skills Directory (`.agents/skills/`)

| Attribute | Value |
|-----------|-------|
| Location | `.agents/skills/` |
| Format | Directory with `.gitkeep` (empty initially) |
| Ownership | Contributors (create skills), maintainers (review) |
| Consumers | AI tools that support skill loading |
| Synced | Yes (directory structure only) |

**Relationships**:
- Skills reference `.specify/memory/constitution.md` dynamically
- Skill creation process documented in `ai/README.md`

### Documentation (`ai/README.md`)

| Attribute | Value |
|-----------|-------|
| Location | `ai/README.md` |
| Format | Markdown |
| Ownership | Org-infra maintainers |
| Consumers | All contributors |
| Synced | Yes (distributed to all org repos) |

**Relationships**:
- Links to `.specify/memory/constitution.md`
- Documents skill creation process (references `.agents/skills/`)
- Documents command usage (references `.opencode/command/`)

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

## Lifecycle

```
1. Initial setup (this feature):
   constitution.md stays at .specify/memory/ (not moved)
   ai/ directory created with README; .agents/skills/ created
   .opencode/command/review_pr.md created
   .gitignore created
   sync-config.yml updated

2. Ongoing usage:
   Contributors clone → install AI agent + spec framework → ready to code/review
   Maintainers update constitution → all tools see updated version
   Contributors create skills → placed in .agents/skills/ → reviewed via PR

3. Org replication:
   sync mechanism distributes files to org repos
   Each repo inherits the standardized AI tooling setup
```
