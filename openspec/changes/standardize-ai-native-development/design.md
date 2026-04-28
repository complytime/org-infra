## Context

The ComplyTime organization has agreed on an AI-native development workflow: a 6-step
process (specify → spec review → implement → code review → merge) with convention
packs, Divisor review council, and spec-driven development. However, this workflow
lacks formal org-wide documentation, the per-repo AI guide is narrowly scoped, and
there is no CI infrastructure to run the review council automatically.

The [unbound-force](https://github.com/unbound-force/unbound-force) repository has mature implementations of Divisor agents,
convention packs, and the review-council command. These patterns inform the design
but are distributed via `uf init`, not org-infra sync.

The `community` repository serves as the single source of truth for community
documentation (contributing guidelines, governance, style guide) but has zero AI
content. Its `STYLE_GUIDE.md` is outdated relative to the constitution v1.2.0.

Three repositories are involved: `community` (standards), `org-infra` (tooling +
distribution), and every downstream repo (consumers). Changes span documentation,
CI workflows, and sync configuration.

## Goals / Non-Goals

**Goals:**

- Establish `community/AI_NATIVE_DEVELOPMENT.md` as the org-wide AI development
  standard, derived from the team's agreed AI-native development workflow.
- Align `community/STYLE_GUIDE.md` with constitution v1.2.0 and reference the
  constitution as the authoritative source for coding standards.
- Rename and restructure `docs/AI_TOOLING.md` → `docs/AI.md` as the per-repo
  operational guide, referencing the community standard.
- Create a reusable CI workflow that runs the Divisor review council on every PR
  via an AI API, with spec vs code review auto-detection.
- Add Divisor agent files and the consumer workflow to sync-config for org-wide
  distribution.

**Non-Goals:**

- Modifying [unbound-force](https://github.com/unbound-force/unbound-force) or its distribution mechanism.
- Running `uf init` in repositories (prerequisite, done separately).
- Selecting and provisioning the AI API provider (determined during AI integration).
- Implementing future capabilities (unleash, Dewey, uf analyze).
- Updating historical spec files (specs/004-standardize-ai-tooling).

## Decisions

### D1: Community doc named `AI_NATIVE_DEVELOPMENT.md` at root level

The org-wide standard lives in `community/AI_NATIVE_DEVELOPMENT.md` at the repository
root, matching the community repo's flat documentation structure (all standards are
root-level: `STYLE_GUIDE.md`, `CONTRIBUTING.md`, `GOVERNANCE.md`).

**Alternatives considered:**
- `AI_GUIDE.md` — too generic, doesn't convey the paradigm shift.
- `AI_STANDARDS.md` — emphasizes rules over workflow; the document covers philosophy
  and process, not just standards.
- `AI.md` — too terse for a foundational document; better suited for the per-repo
  operational guide.

### D2: Per-repo guide named `docs/AI.md` in docs/ directory

The per-repo operational guide is renamed from `docs/AI_TOOLING.md` to `docs/AI.md`.
Stays in `docs/` for consistency with existing documentation (`docs/LOCAL_TESTING.md`,
`docs/SYNC_REPOSITORIES_SETUP.md`).

**Alternatives considered:**
- Root-level `AI.md` — maximum discoverability but clutters root alongside README.md,
  CONTRIBUTING.md, etc. Root is reserved for governance-level files.
- `docs/AI_GUIDE.md` — redundant with the community doc naming. `AI.md` is cleaner.
- `docs/AI_WORKFLOW.md` — too narrow, the doc also covers setup and commands.

### D3: Three-layer document architecture

```
community/AI_NATIVE_DEVELOPMENT.md    →  Philosophy, workflow, standards
org-infra/docs/AI.md (synced)         →  Setup, commands, packs, repo-specific
.specify/memory/constitution.md       →  Governance authority (unchanged)
```

The community doc defines WHAT and WHY. The per-repo doc defines HOW. The constitution
defines MUST/SHOULD rules. Each layer has a distinct audience and update cadence.

**Alternatives considered:**
- Single document in community covering everything — too long, mixes operational
  details with philosophy. Per-repo needs differ (Go vs Python vs YAML repos).
- Constitution absorbs AI standards — overloads the constitution, which is governance
  not workflow guidance.

### D4: STYLE_GUIDE.md references constitution, does not duplicate it

The community `STYLE_GUIDE.md` is updated to align with constitution v1.2.0 and
explicitly references it as the authoritative source. The constitution is not
replicated to the community repository — it lives in org-infra and is synced to
repositories that use AI-native development.

**Alternatives considered:**
- Copy constitution to community — creates a second source of truth, violating
  Principle I. The constitution's amendment procedure is tied to org-infra.
- Merge STYLE_GUIDE into constitution — different audiences. STYLE_GUIDE is for
  human newcomers; constitution is for governance and agent enforcement.
- Keep both separate, manually aligned — fragile, already proven to drift.

### D5: CI council review via AI API with credentials in GitHub Secrets

The CI workflow calls an AI API to run the review council. Each review invokes 5
parallel API calls (one per Divisor persona). The workflow reads committed
`.opencode/agents/divisor-*.md` files as prompt context. API credentials are stored
as GitHub Secrets at the organization level.

The specific AI provider (e.g., Google Vertex AI, Anthropic API) is a placeholder
in this design and will be determined during the AI integration phase. The workflow
architecture is provider-agnostic — it constructs prompts and parses responses,
with the API endpoint and authentication method configurable via workflow inputs
and secrets.

**Alternatives considered:**
- Hardcoding a specific AI provider now — premature; the team may change providers
  as the ecosystem evolves. Keeping the workflow provider-agnostic avoids rework.
- GitHub App / webhook service — external infrastructure, higher complexity, harder
  to maintain.

### D6: Divisor agent files fully aligned with uf standards

The 5 core Divisor persona files follow the exact structure, naming, and location
used in [unbound-force](https://github.com/unbound-force/unbound-force): `.opencode/agents/divisor-{guard,architect,adversary,
testing,sre}.md`. Files are initially created by `uf init` (prerequisite), then
maintained in org-infra and replicated via sync-config. `uf init --divisor` overwrites
the synced versions locally with potentially enhanced versions for interactive review.

**Alternatives considered:**
- Dedicated CI prompt templates in `.github/council/` — splits maintenance between
  two sets of persona definitions. Divergence inevitable.
- Embedded prompts in workflow YAML — unmaintainable, unreviewable, hard to customize.
- Content-only alignment (different location) — breaks the uf standard's expectation
  of where Divisor files live.

### D7: Review triggers on every push with gate checks

The CI council review runs on every `pull_request` event (`opened`, `synchronize`).
Gate checks skip unnecessary runs: dependabot PRs, draft PRs, binary/lock-only
changes, and fork PRs without API credentials.

The workflow uses the `pull_request` event (not `pull_request_target`). This is a
deliberate security choice: GitHub does not expose repository or organization secrets
to workflows triggered by `pull_request` from forks. This means PRs from external
contributors (non-organization members) will naturally skip the council review because
the API credentials are unavailable. This is the desired behavior — maintainers review
external contributions manually. Additionally, GitHub organizations can require
maintainer approval before any workflow runs on fork PRs (configurable under
organization Actions settings).

**Alternatives considered:**
- `pull_request_target` event — exposes secrets to fork PRs, which is a security
  risk and would consume API credits for untrusted code.
- Label-triggered (`council-review` label) — saves costs but adds a manual step,
  easy to forget, inconsistent coverage.
- Comment-triggered (`/review-council` in PR comment) — familiar pattern but requires
  contributors to remember to invoke it.

### D8: Spec vs code review auto-detection via changed files

The workflow examines which files a PR changes to determine review mode:
- Only `specs/`, `openspec/`, `.specify/` files → Spec Review mode
- Any code files → Code Review mode
- Both spec and code files → Code Review mode (Guard checks spec alignment)

Uses `tj-actions/changed-files` (already used in `ci_dependencies.yml`) for
classification.

**Alternatives considered:**
- Branch name pattern matching (`NNN-*`) — fragile, not all branches follow this
  convention.
- Manual mode selection via label — adds friction, contributors can miscategorize.
- Always run both modes — wasteful, doubles API calls.

### D9: Single PR comment with replace-on-push

Council findings are posted as a single PR comment using
`peter-evans/create-or-update-comment` with `edit-mode: replace`. Each push updates
the same comment with fresh findings. This matches the existing pattern used in
`ci_dependencies.yml` for dependabot review comments.

**Alternatives considered:**
- New comment per push — clutters PR timeline, hard to find latest findings.
- Check run annotations — limited formatting, no structured tables.
- Status checks only (pass/fail) — loses the detailed persona findings.

### D10: Graceful failure when Divisor files are missing

If `.opencode/agents/divisor-*.md` files are not present (repo hasn't run `uf init`),
the workflow skips the review and posts a comment indicating that council review
requires setup. This prevents CI failures in repos that haven't adopted the workflow.

**Alternatives considered:**
- Embed fallback prompts — adds maintenance burden for a transitional scenario.
- Assume always present — breaks repos that haven't run `uf init` yet.

### D11: Per-repo docs/AI.md designed for manual copy

The per-repo `docs/AI.md` uses no org-infra-specific assumptions. It references the
community standard by URL and uses generic language that works for any repo regardless
of language (Go, Python, YAML-only). Repos excluded from sync (e.g., `complyscribe`)
can manually copy the file.

**Alternatives considered:**
- Sync-only design with repo-specific overrides — excluded repos get nothing.
- Template with placeholders — requires per-repo customization, defeats the purpose
  of a synced file.

## Risks / Trade-offs

### [RISK] Cross-repo ordering dependency
The community doc must be merged before per-repo docs can reference valid URLs.
→ **Mitigation**: Phase the rollout. Community PR merges first, then org-infra PR
follows.

### [RISK] AI API not configured → CI workflow fails
If the AI API credentials are not provisioned in GitHub Secrets, the council review
workflow will fail on all PRs.
→ **Mitigation**: Workflow fails gracefully with a clear error message. Document
API setup as a prerequisite in `docs/AI.md` and `AGENTS.md`.

### [RISK] API cost: 5 AI calls per push
Active repositories with frequent pushes could accumulate significant API costs.
→ **Mitigation**: Gate checks skip dependabot PRs, draft PRs, binary-only changes,
and fork PRs (no secrets available). Future enhancement: limit diff size per persona,
add a triage step to determine which personas are relevant.

### [RISK] Prompt quality: subagent → single-shot adaptation
Divisor agent files are designed for interactive subagent sessions with tool access.
CI uses single-shot API calls without tools. Some checklist items reference tool
actions (e.g., "read the convention packs") that must be adapted.
→ **Mitigation**: The CI workflow pre-reads governance files and embeds their content
in the prompt alongside the diff, replacing tool-dependent steps.

### [RISK] uf init overwrites synced Divisor files
After sync delivers baseline files, `uf init --divisor` overwrites them locally.
A contributor who then runs `git add .` could commit the uf-generated versions,
diverging from org-infra.
→ **Mitigation**: Document the expected behavior in `docs/AI.md`. The `.gitignore`
should be configured to avoid accidental commits of uf-overwritten files in repos
where sync is the authority.

### [RISK] Sync-excluded repos diverge
Repos excluded from Divisor file sync maintain their own persona definitions,
which may drift from the org-wide baseline.
→ **Mitigation**: Exclusions should be deliberate and documented in `sync-config.yml`
comments. Excluded repos are responsible for maintaining alignment.

### [TRADE-OFF] Community doc is not synced
`AI_NATIVE_DEVELOPMENT.md` lives only in the community repo and is referenced by
URL. This means per-repo docs point to an external file that could move or change
independently.
→ **Accepted**: The community repo is the canonical home for org-wide standards.
URL stability is maintained by convention (same as CONTRIBUTING.md, GOVERNANCE.md).

## Migration Plan

1. **Phase 1 — Community standards**: Create `AI_NATIVE_DEVELOPMENT.md`, update
   `STYLE_GUIDE.md`. Merge to community/main.
2. **Phase 2 — Per-repo guide**: Rename `docs/AI_TOOLING.md` → `docs/AI.md`,
   restructure content, update `AGENTS.md` references.
3. **Phase 3 — CI council review**: Create `reusable_council_review.yml` and
   `ci_council_review.yml`. Test on org-infra PR before syncing.
4. **Phase 4 — Distribution**: Update `sync-config.yml` with new paths (AI.md,
   Divisor files, consumer workflow). Run sync dry-run to verify.
5. **Phase 5 — Rollout**: Sync runs, all downstream repos receive new files.
   Repos verify council review works (requires AI API secrets configured).

**Rollback**: Revert sync-config.yml changes to stop distribution. Per-repo files
can be individually reverted. Community docs are independent and don't require
rollback coordination.

## Open Questions

- **Q1**: Which repos should be excluded from Divisor agent file sync? Needs input
  from repo maintainers who have custom persona definitions.
- **Q2**: Should the CI council review have a diff size limit per persona to control
  cost and prompt quality? If so, what threshold (e.g., 500 lines)?
- **Q3**: Which AI API provider will be used? (Vertex AI, Anthropic, etc.) This
  will be determined during the AI integration phase. The workflow design is
  provider-agnostic.
