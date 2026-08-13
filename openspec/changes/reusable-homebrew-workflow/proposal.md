## Why

Each ComplyTime repo that ships a Go CLI binary needs to publish a Homebrew source-build
formula to `complytime/homebrew-tap` as a post-release step. Today this logic is inlined
in individual release workflows (complyctl PR #742) using heredoc + `sed` templating,
with no shared quality gates. A second repo (complypack) has no Homebrew setup at all.

A reusable workflow eliminates duplication, prevents drift, standardises GitHub App
authentication, and adds `brew audit --strict` validation that no repo currently runs.

Closes complytime/org-infra#500.

## What Changes

- Add `reusable_release_homebrew.yml` — a reusable workflow that generates a
  source-build Homebrew formula from workflow inputs, computes SHA256 from the
  source tarball, runs `brew audit --strict`, and pushes the formula to the tap repo.
- Add `ci_test_homebrew.yml` — a self-test workflow that validates the reusable
  workflow on a macOS runner in PRs that touch Homebrew workflow files.
- Update `sync-config.yml` — no sync needed for the reusable workflow itself (it stays
  in org-infra and is called cross-repo), but document any caller patterns for
  downstream repos.

## Non-goals

- Publishing pre-built bottles (binary packages). This workflow is source-build only;
  users compile from source via `brew install`.
- Cask support. Casks are for GUI apps with `.dmg`/`.pkg` installers, not CLI tools.
- Syncing a caller workflow to downstream repos via `sync-config.yml` — each repo's
  release workflow is unique enough that it should call the reusable directly.

## Capabilities

### New Capabilities

- `homebrew-formula-publish`: Reusable workflow that generates, validates, and pushes
  a Homebrew source-build formula to a tap repository as a post-release step.
- `homebrew-workflow-testing`: CI self-test workflow for validating the reusable
  Homebrew workflow on macOS runners.

### Modified Capabilities

(none)

## Impact

- **New files**: `.github/workflows/reusable_release_homebrew.yml`,
  `.github/workflows/ci_test_homebrew.yml`
- **Dependencies**: Requires a GitHub App (`complytime-homebrew-formula-publisher` or
  similar) with `contents:write` permission on `complytime/homebrew-tap`.
  Uses `actions/create-github-app-token` for cross-repo auth.
- **Downstream repos**: complyctl and complypack release workflows will call this
  reusable workflow instead of inlining Homebrew logic.
- **Tap repo**: `complytime/homebrew-tap` must exist with a `Formula/` directory
  structure.
