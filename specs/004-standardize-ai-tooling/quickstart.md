# Quick Start: AI Tooling in ComplyTime Projects

**Branch**: `004-standardize-ai-tooling` | **Date**: 2026-04-09 (updated)

This document previews the contributor experience after implementation. It serves as the basis for the `ai/README.md` content.

## For Contributors (OpenCode - Recommended)

```bash
# 1. Clone the repository
git clone https://github.com/complytime/org-infra.git
cd org-infra

# 2. Open in OpenCode (install OpenSpec or SpecKit plugin if not already installed)
opencode .

# 3. Start working
#    - Use /review_pr <number> to review a pull request
#    - Use framework commands to create feature specifications
#    - Read .specify/memory/constitution.md for coding standards
```

**Time to first command**: Under 5 minutes (including tool installation).

## For Contributors (Other Tools)

Both OpenSpec and SpecKit are agent-agnostic — they work with any supported AI tool.

```bash
# 1. Clone the repository
git clone https://github.com/complytime/org-infra.git
cd org-infra

# 2. Install OpenSpec or SpecKit plugin for your AI tool
# 3. Open in your AI agent — it will use .specify/memory/constitution.md for standards
```

If your tool does not support plugin-based commands, reference `.opencode/command/` for command definitions you can adapt.

## Key Files

| File | Purpose |
|------|---------|
| `.specify/memory/constitution.md` | Organizational governance and coding standards |
| `docs/AI_TOOLING.md` | AI tooling setup, commands, skills documentation |
| `.agents/skills/` | Directory for AI skills — agent-agnostic, auto-discovered by OpenCode |
| `.opencode/command/review_pr.md` | PR review command (OpenCode) |
| `specs/` | Feature specifications (SpecKit output) |
| `openspec/` | Feature specifications (OpenSpec output) |

## Specifications (Dual-Directory Model)

Features are managed via spec-driven development. SpecKit and OpenSpec use separate output directories with coordinated sequential numbering:

```
specs/                        # SpecKit output
├── 001-first-feature/
│   └── spec.md
├── 002-second-feature/
│   └── spec.md
└── ...

openspec/                     # OpenSpec output
├── 005-next-feature/
│   └── spec.md
└── ...
```

**Numbering**: Sequential numbers are coordinated across both directories. The next feature (in either directory) uses the next available number by scanning both. If `specs/004-*` is the highest, the next feature is `005-*` regardless of which framework creates it.

**History**: Review both directories for a complete chronological timeline of all features.

## Creating a Skill

1. Create a new directory: `.agents/skills/your-skill-name/`
2. Add a `SKILL.md` file with YAML frontmatter:
   ```yaml
   ---
   name: your-skill-name
   description: Brief description of what this skill does
   license: MIT
   compatibility: opencode
   ---
   # Skill instructions here
   ```
3. Submit a PR for review

## Creating a Project-Specific Command

1. Create a new file: `.opencode/command/your-command.md`
2. Add YAML frontmatter with `description`
3. Write the command instructions in Markdown
4. Submit a PR for review

## Validation Steps

After setup, verify the following:

1. `/review_pr` command is available in OpenCode
2. `.specify/memory/constitution.md` is readable and contains organizational standards
3. `ai/README.md` is present and documents the tooling setup
4. `.agents/skills/` directory exists (empty initially)
5. Framework commands (speckit.\*, opsx-\*) are NOT tracked by git
6. Both `specs/` and `openspec/` directories are recognized for spec output
