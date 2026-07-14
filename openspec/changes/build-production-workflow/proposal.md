# Build Production Workflow

## Why

The council review concept has been validated end-to-end: ITPC WIF
authentication works, Claude Sonnet 4.6 and Opus 4.6 respond via Vertex AI,
and the test workflow (`ci_council_review_test.yml`) confirms the full chain
from GitHub Actions OIDC token to model response. However, no production
workflow exists. The test workflow must be replaced with a production
workflow that follows the org's conventions and handles gate checks, inline
review posting, and bot comment deduplication.

Tracked internally.

## Non-goals

- Multi-provider support (Bedrock, direct Anthropic API)
- Automating GCP resource provisioning (Terraform, Pulumi)
- Changing persona definitions or review output formatting
- Service account creation or key management
- Open-source model integration (DeepSeek, Qwen, Gemma)

## What Changes

- **New**: `ci_council_review_collect.yml` — fork-safe workflow triggered on
  `pull_request` that collects the PR diff and metadata, uploads as an artifact
- **New**: `ci_council_review.yml` — thin consumer triggered on `workflow_run`
  that calls the reusable workflow with secrets and the triggering run ID
- **New**: `reusable_council_review.yml` — shared review logic that downloads
  the artifact, authenticates via WIF, delegates to the council-review-action
  composite action, and posts inline review comments on the PR
- **Remove**: `ci_council_review_test.yml` — temporary test workflow,
  replaced by the production workflows above

## Capabilities

### New Capabilities

- `council-review-workflow`: Production AI council review via three-file chain
  matching org convention: fork-safe collect (no secrets) → thin consumer
  (triggers reusable) → reusable review (WIF auth, composite action, posting).
  Includes gate checks (drafts, dependabot, missing WIF credentials), inline
  review posting via GitHub Review API, smart diff filtering, and bot comment
  deduplication. Consumer workflows sync to downstream repos; reusable stays
  in org-infra and is called cross-repo.

### Modified Capabilities

(none)

## Impact

- **Workflows**: Three new workflow files, one removed
- **Sync**: `ci_council_review_collect.yml` and `ci_council_review.yml` synced
  to downstream repos; `reusable_council_review.yml` stays only in org-infra
- **Secrets**: Requires `GCP_WORKLOAD_IDENTITY_PROVIDER` and `GCP_PROJECT_ID`
  org secrets (already configured)
- **GCP**: Uses existing `unbound-force` project with WIF IAM bindings
  (already granted for both `complytime` and `unbound-force` orgs)
- **Dependencies**: `google-github-actions/auth@v3` (SHA-pinned),
  `google-github-actions/setup-gcloud@v3` (SHA-pinned), OpenCode CLI
  (pinned `opencode-ai@1.2.26`), `council-review-action` composite action
  (SHA-pinned)
