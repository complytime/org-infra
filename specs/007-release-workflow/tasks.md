# Task List: Release Workflow for org-infra

**Branch**: `feat/adds-release-workflow` | **Plan**: [plan.md](plan.md)

## Tasks

### Task 1 — Create release-drafter configuration

**File**: `.github/release-drafter.yml`

- [x] 1.1 Define `name-template` and `tag-template` using `v$RESOLVED_VERSION`
- [x] 1.2 Configure `version-resolver` with major/minor/patch label mappings
- [x] 1.3 Define changelog categories (breaking, workflows, compliance, sync, features, fixes, performance, maintenance)
- [x] 1.4 Configure `autolabeler` for conventional commit prefixes and file path patterns
- [x] 1.5 Add `exclude-labels` for `skip-changelog`
- [x] 1.6 Add `exclude-contributors` for `dependabot[bot]` and `github-actions[bot]`
- [x] 1.7 Add consumer guidance in release template body (upgrade notes, diff link)

---

### Task 2 — Create release workflow

**File**: `.github/workflows/release.yaml`

- [x] 2.1 Add `workflow_dispatch` trigger with `tag` input (required, semver format)
- [x] 2.2 Add tag format validation step (reject non-semver tags)
- [x] 2.3 Add branch restriction step (reject triggers from non-main branches)
- [x] 2.4 Add checkout step with `fetch-depth: 0` for full history
- [x] 2.5 Add conditional tag creation step (create and push if absent, skip if exists)
- [x] 2.6 Add release-drafter publish step with `GITHUB_TOKEN` env
- [x] 2.7 Set workflow-level `permissions: {}` and job-level `contents: write`
- [x] 2.8 Pin all action SHAs with inline version comments
- [x] 2.9 Add header comment block with usage instructions and consumer guidance
- [x] 2.10 Route all user inputs through `env:` blocks (no `${{ }}` interpolation in `run:`)

---

### Task 3 — Create release notes preview workflow

**File**: `.github/workflows/release_notes_preview.yml`

- [x] 3.1 Add `workflow_dispatch` trigger (no inputs)
- [x] 3.2 Add release-drafter dry-run step with `GITHUB_TOKEN` env
- [x] 3.3 Add step to write preview to `$GITHUB_STEP_SUMMARY`
- [x] 3.4 Add artifact upload for `release-notes-preview.md`
- [x] 3.5 Set read-only permissions (`contents: read`, `pull-requests: read`)
- [x] 3.6 Pin all action SHAs with inline version comments

---

### Task 4 — Validation

- [x] 4.1 Verify `yamllint` passes on all three files
- [ ] 4.2 Verify `make sync-dry-run` includes release workflow files if applicable
- [ ] 4.3 Run release notes preview workflow to confirm dry-run output
- [ ] 4.4 Test release workflow with first release (e.g., `v0.1.0`)

---

### Task 5 — Self-review checklist

Before opening the PR to `complytime/org-infra`:

- [x] `.github/release-drafter.yml` exists with correct category/label mappings
- [x] `.github/workflows/release.yaml` validates tag format, enforces main branch, creates tag if absent
- [x] `.github/workflows/release_notes_preview.yml` runs dry-run preview
- [x] All `uses:` are pinned to full SHA with `# vX.Y.Z` comment
- [x] Workflow-level permissions are `{}` or read-only
- [x] `GITHUB_TOKEN` is passed to release-drafter steps
- [x] Header comments include consumer guidance
- [x] No `${{ }}` interpolation in `run:` blocks — all user inputs via `env:`
- [x] Release restricted to `main` branch only
- [x] Spec files exist under `specs/007-release-workflow/`
- [ ] PR description documents the release process and consumer pinning strategy
