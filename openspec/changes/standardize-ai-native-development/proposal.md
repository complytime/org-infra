## Why

The ComplyTime organization has agreed on an AI-native development workflow (spec-driven,
council-reviewed, convention-pack-enforced) but lacks the documentation and CI
infrastructure to adopt it consistently. The per-repo `docs/AI_TOOLING.md` covers
tooling setup but not the workflow, philosophy, or convention pack system. There is no
formal org-wide standard, and no CI mechanism to run the review council on PRs --
council review is local-only, requiring each contributor to run it manually.

This change establishes a single source of truth for AI-native development standards
in the community repository, restructures the per-repo AI guide for clarity and
flexibility, and creates a reusable CI workflow that runs the Divisor review council
automatically on every PR via an AI API.

## What Changes

- **New org-wide standard**: `community/AI_NATIVE_DEVELOPMENT.md` -- philosophy,
  workflow, file classification, convention packs, disclosure standards, continuous
  improvement. Derived from the team's agreed AI-native development workflow.
- **Community STYLE_GUIDE.md alignment**: Update to align with constitution v1.2.0
  (RFC 2119 keywords, `ruff` over `flake8`, Principle IV title, `Assisted-by` trailer,
  constitution reference, Lint Configuration Awareness section, branch model fix).
- **Per-repo AI guide rename and restructure**: `docs/AI_TOOLING.md` → `docs/AI.md`.
  Add convention packs section, link to community standard, update key files table.
  Designed to work when manually copied to repos excluded from sync.
- **CI council review workflow**: `reusable_council_review.yml` (reusable) +
  `ci_council_review.yml` (consumer, synced). Reads committed Divisor agent files
  (`.opencode/agents/divisor-*.md`) as prompt context, authenticates to an AI API
  using credentials from GitHub Secrets, calls 5 personas in parallel, posts
  structured PR comment. The specific AI provider is a placeholder — determined
  during the AI integration phase. Detects spec vs code review mode. Gate checks
  skip dependabot, draft, binary-only, and fork PRs (secrets not available to fork
  `pull_request` events). Fails gracefully if Divisor files or credentials are
  missing.
- **Divisor agent files in sync**: Add the 5 core Divisor persona files
  (`divisor-guard.md`, `divisor-architect.md`, `divisor-adversary.md`,
  `divisor-testing.md`, `divisor-sre.md`) to `sync-config.yml`. Files are initially
  created by `uf init` (separate prerequisite), then maintained in org-infra and
  replicated via sync. Some repos may be excluded for custom personas.
- **Sync config updates**: Rename `AI_TOOLING.md` → `AI.md` path, add Divisor agent
  files, add `ci_council_review.yml`.

## Non-goals

- Changes to [unbound-force](https://github.com/unbound-force/unbound-force) (tool-side changes are independent).
- Running `uf init` in repositories (separate prerequisite, done by maintainers).
- Selecting and provisioning the AI API provider (determined during AI integration).
- Future capabilities: `/unleash`, Dewey knowledge layer, `uf analyze`.
- Updating historical spec files (`specs/004-standardize-ai-tooling/`).

## Capabilities

### New Capabilities

- `ai-native-standards`: Org-wide AI-native development standard in the community
  repository (`AI_NATIVE_DEVELOPMENT.md`) and alignment of `STYLE_GUIDE.md` with the
  constitution. Defines philosophy, workflow, file classification, convention pack
  system, disclosure requirements, and continuous improvement loop.
- `per-repo-ai-guide`: Per-repository AI guide (`docs/AI.md`) renamed and restructured
  from `docs/AI_TOOLING.md`. Adds convention packs section, references community
  standard, designed for both sync and manual copy. Includes sync-config and AGENTS.md
  updates.
- `ci-council-review`: Automated CI council review workflow using an AI API.
  Reusable workflow reads Divisor agent files as prompt context, runs 5 personas in
  parallel (Guard, Architect, Adversary, Tester, SRE), detects spec vs code review
  mode, posts structured PR comment. Consumer workflow synced to all repos. Includes
  Divisor agent file sync configuration.

### Modified Capabilities

(none)

## Impact

- **community repository**: 2 files (1 new, 1 updated). Establishes org-wide AI
  standards. No CI or tooling impact.
- **org-infra repository**: 6-8 files (3-5 new, 3 updated). New reusable
  and consumer workflows. Sync config changes affect all downstream repos on next sync.
- **All synced repositories**: Receive renamed `docs/AI.md`, new
  `ci_council_review.yml`, and 5 Divisor agent files on next sync. Requires AI API
  credentials configured in GitHub Secrets at org level for council review to function.
- **Excluded repositories** (complyscribe, .github): Must manually copy `docs/AI.md`
  if desired. Council review consumer workflow must be manually added.
- **Prerequisites**: `uf init --divisor` must have been run in org-infra before Divisor
  files can be added to sync. AI API credentials must be configured in GitHub Secrets
  before CI council review functions.
