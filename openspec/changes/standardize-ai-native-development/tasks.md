## 1. Community Standards (community repository)

- [ ] 1.1 Create `community/AI_NATIVE_DEVELOPMENT.md` with sections: philosophy, 6-step workflow (specify → spec review → implement → code review → merge), file classification table (committed vs local-only), convention pack system and hierarchy, disclosure standards (Assisted-by trailer), agent-agnostic principle, continuous improvement loop, and engineer quick reference. Derived from the team's agreed AI-native development workflow. Exclude future capabilities (unleash, Dewey, uf analyze).

- [ ] 1.2 Update `community/STYLE_GUIDE.md`: replace informal "should" with RFC 2119 MUST/SHOULD/MAY keywords to align with constitution v1.2.0. Replace `flake8` references with `ruff`. Rename Principle IV from "Code is Written for Humans First" to "Readability First". Add Lint Configuration Awareness section listing standard config files (`.golangci.yml`, `ruff.toml`, `.yamllint.yml`, etc.). Add `Assisted-by` trailer requirement under commit standards. Fix branch model from `develop` to `main`-only. Add reference to `.specify/memory/constitution.md` as the authoritative source (managed in org-infra). Add link to `AI_NATIVE_DEVELOPMENT.md` for AI development standards.

## 2. Per-Repo AI Guide (org-infra)

- [ ] 2.1 Rename `docs/AI_TOOLING.md` to `docs/AI.md`. Restructure content: add link to `community/AI_NATIVE_DEVELOPMENT.md`, add convention packs section (which packs exist, hierarchy, customization), update key files table to include constitution, convention packs, AGENTS.md, Divisor agents, review command, and spec directories. Update self-reference from "AI_TOOLING.md" to "AI.md". Preserve existing sections: Getting Started, Commands, Creating Commands, Creating Skills, Specifications. Ensure document uses no org-infra-specific assumptions (works when manually copied to excluded repos).

- [ ] 2.2 Update `AGENTS.md`: replace `docs/AI_TOOLING.md` references with `docs/AI.md` in both the structure tree (line 14) and the constraints section (line 38). Add documentation for `.opencode/agents/divisor-*.md` files and the CI council review workflow.

## 3. CI Council Review Workflow (org-infra)

- [ ] 3.1 Create `.github/workflows/reusable_council_review.yml`. Implement as a reusable workflow with `workflow_call` trigger. Define inputs for AI API configuration (endpoint, model name) as placeholders — the specific AI provider will be determined during the AI integration phase. Define secrets for API credentials (stored in GitHub Secrets). Add header comment block describing the workflow purpose. Set workflow-level permissions to none.

- [ ] 3.2 Implement gate checks job in `reusable_council_review.yml`: skip if PR author is dependabot, skip if PR is draft, skip if only binary/lock/generated files changed, skip if API credentials are unavailable (fork PRs — GitHub does not expose secrets to `pull_request` events from forks). Use `tj-actions/changed-files` (pinned to SHA) for file classification. Output a `should_review` flag for downstream jobs.

- [ ] 3.3 Implement review mode detection in `reusable_council_review.yml`: classify changed files into spec files (`specs/`, `openspec/`, `.specify/`) and code files. Output `review_mode` as either `spec` or `code`. If only spec files changed → `spec`. If any code files → `code`. If both → `code`.

- [ ] 3.4 Implement governance context collection in `reusable_council_review.yml`: read `.specify/memory/constitution.md`, all `.opencode/uf/packs/*.md` files, and `AGENTS.md`. Concatenate into a single context string. For spec review mode, also read relevant spec files from `specs/` or `openspec/`. Collect PR diff via `gh pr diff` excluding binary and lock files.

- [ ] 3.5 Implement Divisor file presence check in `reusable_council_review.yml`: verify that `.opencode/agents/divisor-guard.md`, `divisor-architect.md`, `divisor-adversary.md`, `divisor-testing.md`, and `divisor-sre.md` exist. If none found, skip review and post informational comment. If partial, note which personas will be skipped.

- [ ] 3.6 Implement AI API authentication in `reusable_council_review.yml`: read API credentials from GitHub Secrets. The authentication method is provider-dependent and will be finalized during the AI integration phase. Fail gracefully with clear error if credentials are not configured or unavailable (e.g., fork PRs).

- [ ] 3.7 Implement 5-persona parallel review in `reusable_council_review.yml`: for each available Divisor agent file, construct a prompt combining the agent file content, the review mode (spec/code), the governance context, and the PR diff. Make parallel API calls to the configured AI API. Parse each response for verdict (APPROVE/REQUEST CHANGES) and structured findings with severity levels.

- [ ] 3.8 Implement PR comment posting in `reusable_council_review.yml`: format all persona verdicts and findings into a single structured markdown comment. Include: review mode, persona verdict summary table, detailed findings per persona, overall council verdict, and disclaimer. Use `peter-evans/create-or-update-comment` (pinned to SHA) with `edit-mode: replace` to update on each push.

- [ ] 3.9 Create `.github/workflows/ci_council_review.yml` as consumer workflow. Trigger on `pull_request` events (opened, synchronize) against `main` branch — uses `pull_request` (not `pull_request_target`) to ensure secrets are not exposed to fork PRs. Set job-level permissions: `contents: read`, `pull-requests: write`. Call `reusable_council_review.yml` passing AI API configuration and credential secrets. Add header comment block describing purpose.

## 4. Sync Configuration (org-infra)

- [ ] 4.1 Update `sync-config.yml`: change `docs/AI_TOOLING.md` source and destination to `docs/AI.md`. Preserve existing exclusions (`.github`, `complyscribe`).

- [ ] 4.2 Update `sync-config.yml`: add `.opencode/agents/divisor-guard.md`, `.opencode/agents/divisor-architect.md`, `.opencode/agents/divisor-adversary.md`, `.opencode/agents/divisor-testing.md`, and `.opencode/agents/divisor-sre.md` as synced files. Add exclusions for repositories that maintain custom persona definitions (determine exclusion list from repo maintainer input).

- [ ] 4.3 Update `sync-config.yml`: add `.github/workflows/ci_council_review.yml` as a synced file. Use same exclusion pattern as existing `ci_` workflows.

## 5. Validation

- [ ] 5.1 Run `make lint` in org-infra to verify all new and modified YAML and Markdown files pass yamllint, have no trailing whitespace, and end with a newline.

- [ ] 5.2 Verify all action `uses:` references in `reusable_council_review.yml` and `ci_council_review.yml` are pinned to full 40-character commit SHAs with inline version comments.

- [ ] 5.3 Run `make sync-dry-run` in org-infra to verify sync-config changes produce the expected file distribution: `docs/AI.md` replaces `docs/AI_TOOLING.md`, 5 Divisor agent files sync to target repos, and `ci_council_review.yml` syncs to target repos.

- [ ] 5.4 Verify `community/AI_NATIVE_DEVELOPMENT.md` covers all sections from the proposal: philosophy, workflow, file classification, convention pack system, disclosure standards, agent-agnostic principle, continuous improvement loop, quick reference.

- [ ] 5.5 Verify `community/STYLE_GUIDE.md` alignment: RFC 2119 keywords, `ruff` not `flake8`, Principle IV title "Readability First", Lint Configuration Awareness section, `Assisted-by` trailer, `main`-only branch model, constitution reference, AI standards cross-reference.

- [ ] 5.6 Verify `docs/AI.md` references community standard URL, includes convention packs section, updated key files table, and works without org-infra-specific assumptions.

- [ ] 5.7 Test `reusable_council_review.yml` on an org-infra PR: verify gate checks (including fork PR handling), mode detection, graceful failure when AI API credentials are not configured, and comment format.
