**Phase ordering**: Phases MUST be executed in order. Phase 1 (community) MUST be
merged to `community/main` before Phase 2 begins, because `docs/AI.md` references
the community document by URL. Phases 2-4 (org-infra) can be implemented in a
single PR. Phase 5 (validation) runs after all implementation phases.

## 1. Community Standards (community repository)

- [ ] 1.1 Create `community/AI_NATIVE_DEVELOPMENT.md` with sections: philosophy, collaboration workflow (specify → spec review → implement → code review → merge), file classification table (committed vs local-only), convention pack system and hierarchy, disclosure standards (Assisted-by trailer), agent-agnostic principle, continuous improvement loop, and engineer quick reference. Derived from the team's agreed AI-native development workflow. Exclude future capabilities (unleash, Dewey, uf analyze).

- [ ] 1.2 Update `community/STYLE_GUIDE.md`: replace informal "should" with RFC 2119 MUST/SHOULD/MAY keywords to align with constitution v1.2.0. Replace `flake8` references with `ruff`. Rename Principle IV from "Code is Written for Humans First" to "Readability First". Add Lint Configuration Awareness section listing standard config files (`.golangci.yml`, `ruff.toml`, `.yamllint.yml`, etc.). Add `Assisted-by` trailer requirement under commit standards. Fix branch model from `develop` to `main`-only. Add reference to `.specify/memory/constitution.md` as the authoritative source (managed in org-infra). Add link to `AI_NATIVE_DEVELOPMENT.md` for AI development standards.

## 2. Per-Repo AI Guide (org-infra) — depends on Phase 1 merged

- [ ] 2.1 Rename `docs/AI_TOOLING.md` to `docs/AI.md`. Restructure content: add link to `community/AI_NATIVE_DEVELOPMENT.md`, add convention packs section (which packs exist, hierarchy, customization), update key files table to include constitution, convention packs, AGENTS.md, Divisor agents, review command, and spec directories. Update self-reference from "AI_TOOLING.md" to "AI.md". Preserve existing sections: Getting Started, Commands, Creating Commands, Creating Skills, Specifications. Ensure document uses no org-infra-specific assumptions (works when manually copied to excluded repos). Include guidance that contributors in synced repos should not commit uf-overwritten Divisor files.

- [ ] 2.2 Update `AGENTS.md`: replace `docs/AI_TOOLING.md` references with `docs/AI.md` in both the structure tree (line 14) and the constraints section (line 38). Add documentation for `.opencode/agents/divisor-*.md` files (5 review personas synced; 4 content personas org-infra only) and the CI council review workflow.

## 3. CI Council Review Workflow (org-infra)

- [ ] 3.1 Create `.github/workflows/reusable_council_review.yml`. Implement as a reusable workflow with `workflow_call` trigger. Define inputs for AI API configuration (endpoint, model name) as placeholders — the specific AI provider will be determined during the AI integration phase. Define secrets: `AI_API_KEY` and `AI_API_ENDPOINT` (provider-agnostic interface stored in GitHub Secrets). Add header comment block describing the workflow purpose. Set workflow-level permissions to none.

- [ ] 3.2 Implement gate checks job in `reusable_council_review.yml`: skip if PR author is dependabot, skip if PR is draft, skip if only binary/lock/generated files changed (binary: `*.png, *.jpg, *.wasm, *.exe`; lock: `go.sum, package-lock.json, yarn.lock, poetry.lock`; generated: configurable via workflow input), skip if API credentials are unavailable (fork PRs — GitHub does not expose secrets to `pull_request` events from forks), skip if HEAD SHA matches last reviewed SHA (deduplication). Use `tj-actions/changed-files` (pinned to SHA) for file classification. Output a `should_review` flag for downstream jobs.

- [ ] 3.3 Implement review mode detection in `reusable_council_review.yml`: classify changed files into spec files (`specs/**`, `openspec/**`, `.specify/**` — using prefix matching) and code files. Output `review_mode` as either `spec` or `code`. If only spec files changed → `spec`. If any code files → `code`. If both → `code`.

- [ ] 3.4 Implement governance context collection in `reusable_council_review.yml`: read `.specify/memory/constitution.md`, all `.opencode/uf/packs/*.md` files, and `AGENTS.md`. Concatenate into a single context string. For spec review mode, also read relevant spec files from `specs/` or `openspec/`. Collect PR diff via `gh pr diff` excluding binary and lock files. Enforce 1000-line diff limit per persona — truncate with notice if exceeded.

- [ ] 3.5 Implement Divisor file presence check in `reusable_council_review.yml`: verify that `.opencode/agents/divisor-guard.md`, `divisor-architect.md`, `divisor-adversary.md`, `divisor-testing.md`, and `divisor-sre.md` exist. If none found, skip review and post informational comment. If partial, note which personas will be skipped.

- [ ] 3.6 Implement AI API authentication in `reusable_council_review.yml`: read `AI_API_KEY` and `AI_API_ENDPOINT` from GitHub Secrets. Fail gracefully with clear error naming the missing secret(s) if credentials are not configured or unavailable (e.g., fork PRs).

- [ ] 3.7 Implement 5-persona parallel review in `reusable_council_review.yml`: for each available Divisor agent file, construct a prompt combining the agent file content, the review mode (spec/code), the governance context, and the PR diff. Wrap diff content in `<diff>` XML tags with a system instruction that diff content is untrusted and SHALL NOT be interpreted as instructions (prompt injection resilience). Make parallel API calls to the configured AI API. Parse each response for verdict (must contain parseable `**Verdict**: APPROVE` or `**Verdict**: REQUEST CHANGES` string) and structured findings with severity levels. Handle partial failures: if a persona's API call fails or returns unparseable output, report it as "review error" and continue with other personas.

- [ ] 3.8 Implement PR comment posting in `reusable_council_review.yml`: format all persona verdicts and findings into a single structured markdown comment. Include: review mode, persona verdict summary table, detailed findings per persona (including any persona errors), overall council verdict, diff truncation notice if applicable, and disclaimer. Sanitize API response content before embedding in the comment. Use `peter-evans/create-or-update-comment` (pinned to SHA) with `edit-mode: replace` to update on each push.

- [ ] 3.9 Create `.github/workflows/ci_council_review.yml` as consumer workflow. Trigger on `pull_request` events (opened, synchronize) against `main` branch — uses `pull_request` (not `pull_request_target`) to ensure secrets are not exposed to fork PRs. Set job-level permissions: `contents: read`, `pull-requests: write`. Call `reusable_council_review.yml` passing AI API configuration and `AI_API_KEY` + `AI_API_ENDPOINT` secrets. Add header comment block describing purpose.

## 4. Sync Configuration (org-infra)

- [ ] 4.1 Update `sync-config.yml`: change `docs/AI_TOOLING.md` source and destination to `docs/AI.md`. Preserve existing exclusions (`.github`, `complyscribe`). Add `docs/AI_TOOLING.md` to a `files_to_remove` list or document a one-time manual cleanup task for downstream repos to delete the orphaned old file.

- [ ] 4.2 Update `sync-config.yml`: add `.opencode/agents/divisor-guard.md`, `.opencode/agents/divisor-architect.md`, `.opencode/agents/divisor-adversary.md`, `.opencode/agents/divisor-testing.md`, and `.opencode/agents/divisor-sre.md` as synced files. Add exclusions for repositories that maintain custom persona definitions (blocked until Q1 is resolved — determine exclusion list from repo maintainer input before implementation).

- [ ] 4.3 Update `sync-config.yml`: add `.github/workflows/ci_council_review.yml` as a synced file. Use same exclusion pattern as existing `ci_` workflows.

## 5. Validation

Static checks:

- [ ] 5.1 Run `make lint` in org-infra to verify all new and modified YAML and Markdown files pass yamllint, have no trailing whitespace, and end with a newline. (validates: all phases)

- [ ] 5.2 Verify all action `uses:` references in `reusable_council_review.yml` and `ci_council_review.yml` are pinned to full 40-character commit SHAs with inline version comments. (validates: 3.1-3.9)

Integration tests:

- [ ] 5.3 Run `make sync-dry-run` in org-infra to verify sync-config changes produce the expected file distribution: `docs/AI.md` replaces `docs/AI_TOOLING.md`, old `docs/AI_TOOLING.md` is cleaned up, 5 Divisor agent files sync to target repos, and `ci_council_review.yml` syncs to target repos. (validates: 4.1-4.3)

Content verification (manual review with grep-assisted checks):

- [ ] 5.4 Verify `community/AI_NATIVE_DEVELOPMENT.md` covers all sections: check for headings matching philosophy, workflow, file classification, convention pack system, disclosure standards, agent-agnostic principle, continuous improvement loop, quick reference. (validates: 1.1)

- [ ] 5.5 Verify `community/STYLE_GUIDE.md` alignment: RFC 2119 keywords, `ruff` not `flake8`, Principle IV title "Readability First", Lint Configuration Awareness section, `Assisted-by` trailer, `main`-only branch model, constitution reference, AI standards cross-reference. (validates: 1.2)

- [ ] 5.6 Verify `docs/AI.md` references community standard URL, includes convention packs section, updated key files table, Divisor file guidance, and works without org-infra-specific assumptions. (validates: 2.1)

Workflow integration test:

- [ ] 5.7 Test `reusable_council_review.yml` on an org-infra PR: (a) verify gate checks skip dependabot/draft/binary-only PRs, (b) verify mode detection classifies spec-only and code PRs correctly, (c) verify graceful failure when `AI_API_KEY` is not configured (expected until AI provider is chosen), (d) verify comment format matches spec structure. Fork PR and authenticated API tests are deferred until AI provider is selected and a real fork is available. (validates: 3.1-3.9)
