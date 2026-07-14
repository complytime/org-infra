# Build Production Workflow — Tasks

## 1. Collect Workflow (fork-safe, pull_request trigger)

- [x] 1.1 Create `.github/workflows/ci_council_review_collect.yml` with `pull_request` trigger (opened, synchronize, reopened, ready_for_review) targeting `main`
- [x] 1.2 Add gate check: skip drafts and dependabot PRs
- [x] 1.3 Collect PR diff via `gh pr diff` and write `pr-meta.json` with PR number, head SHA, base ref, title
- [x] 1.4 Upload diff and metadata as `council-review-diff` artifact (1 day retention)
- [x] 1.5 Set workflow-level `permissions: {}` (none) and job-level `permissions: { contents: read, pull-requests: read }`
- [x] 1.6 Pin all actions to full 40-character SHA with inline version comment

## 2. Consumer Workflow (thin, workflow_run trigger, synced to downstream)

- [x] 2.1 Create `.github/workflows/ci_council_review.yml` with `workflow_run` trigger on "Council Review - Collect PR Diff" and `workflow_dispatch` for manual testing
- [x] 2.2 Call `reusable_council_review.yml` with secrets and `triggering-run-id` input
- [x] 2.3 Add concurrency group with `cancel-in-progress: true`
- [x] 2.4 Set workflow-level `permissions: {}` (none); job-level permissions inherited by reusable

## 3. Reusable Review Workflow (shared logic, NOT synced)

- [x] 3.1 Create `.github/workflows/reusable_council_review.yml` with `workflow_call` trigger accepting `triggering-run-id`, `model`, `max-diff-lines`, and WIF secrets
- [x] 3.2 Add WIF gate check: skip when WIF secrets are absent
- [x] 3.3 Download `council-review-diff` artifact from triggering run
- [x] 3.4 Authenticate via WIF using `google-github-actions/auth@v3` (SHA-pinned) and set up gcloud CLI
- [x] 3.5 Delegate review to `council-review-action` composite action (SHA-pinned)
- [x] 3.6 Clean up previous bot comments via `gh api` using `<!-- council-review-bot -->` marker
- [x] 3.7 Post inline review via Pull Request Review API (with collapsible `<details>` fallback)
- [x] 3.8 Post comment-only fallback when structured JSON is not available
- [x] 3.9 Accept model and max-diff-lines as configurable inputs

## 4. Validation and Cleanup

- [x] 4.1 Verify all action `uses:` references are pinned to full 40-character SHAs
- [x] 4.2 Open a test PR and verify: collect runs, consumer triggers, WIF auth succeeds, OpenCode responds, inline comments are posted
- [x] 4.3 Test with a draft PR: verify gate skips with logged reason
- [ ] 4.4 Delete `.github/workflows/ci_council_review_test.yml` after production validation succeeds
- [ ] 4.5 Squash commits on the branch and open PR for review
