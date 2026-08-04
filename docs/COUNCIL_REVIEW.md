# Council Review — Operational Guide

AI-assisted PR review using OpenCode on Vertex AI with Divisor persona
discovery. Reviews are posted as inline comments on PR diff lines.

## Architecture

```text
┌─────────────────────────────────────────────────────────┐
│  Downstream Repo (e.g., complytime, gaze)               │
│                                                         │
│  ci_council_review_collect.yml  (pull_request trigger)  │
│  ├── Gate: skip bots, drafts, non-org-members           │
│  ├── Capture diff: gh pr diff → pr-diff.patch           │
│  ├── Build metadata: pr-meta.json                       │
│  └── Upload artifact: council-review-diff               │
│                                                         │
│  ci_council_review.yml  (workflow_run / workflow_dispatch)│
│  └── calls → reusable_council_review.yml (org-infra)    │
└────────────────────────┬────────────────────────────────┘
                         │
┌────────────────────────▼────────────────────────────────┐
│  org-infra: reusable_council_review.yml                 │
│                                                         │
│  ├── Download artifact (pr-diff.patch, pr-meta.json)    │
│  ├── WIF auth → Google Cloud (Vertex AI)                │
│  ├── council-review-action (SHA-pinned composite)       │
│  │   ├── Filter noise → pr-diff-filtered.patch          │
│  │   ├── Annotate lines → pr-diff-annotated.patch       │
│  │   ├── Pre-fetch PR context (CI, reviews, issues)     │
│  │   ├── Discover Divisor personas                      │
│  │   ├── Build prompt + opencode run                    │
│  │   └── Parse + validate → review_output.json          │
│  ├── Clean up previous bot comments                     │
│  ├── Post review summary (issue comment)                │
│  └── Post inline comments (PR review comments)          │
└─────────────────────────────────────────────────────────┘
```

## Workflow files

| File                            | Synced? | Trigger                              | Purpose                                                  |
|---------------------------------|---------|--------------------------------------|----------------------------------------------------------|
| `ci_council_review_collect.yml` | Yes     | `pull_request`                       | Fork-safe diff collection, no secrets needed             |
| `ci_council_review.yml`         | Yes     | `workflow_run` / `workflow_dispatch` | Thin consumer, passes secrets to the reusable            |
| `reusable_council_review.yml`   | **No**  | `workflow_call`                      | Core logic: WIF auth, action invocation, comment posting |

Consumer workflows have `DO NOT EDIT` provenance headers indicating they
are managed by org-infra. Downstream repos should not modify them directly.

## Required secrets

| Secret                           | Required | Scope     | Purpose                                               |
|----------------------------------|----------|-----------|-------------------------------------------------------|
| `GCP_WORKLOAD_IDENTITY_PROVIDER` | Yes      | Org-level | WIF provider for Vertex AI authentication             |
| `GCP_PROJECT_ID`                 | Yes      | Org-level | GCP project containing Vertex AI                      |
| `ORG_CHECK_TOKEN`                | No       | Org-level | PAT with `org:read` for private org membership checks |

If `GCP_WORKLOAD_IDENTITY_PROVIDER` is not set, the review is skipped with a
`::notice::` annotation. No tokens are consumed.

If `ORG_CHECK_TOKEN` is not set, the collect workflow falls back to
`GITHUB_TOKEN` which can only check **public** org membership. Private org
members (the GitHub default) will be treated as non-members and skipped.

## Gate conditions

The collect workflow skips council review when:

- PR is a draft
- PR author is `dependabot[bot]`
- PR author is not a member of the repository's org

## Composite action

The review logic lives in
[`unbound-force/unbound-force/council-review-action/`](https://github.com/unbound-force/unbound-force/tree/main/council-review-action).
It is pinned by full SHA in `reusable_council_review.yml`.

The action:

1. Installs `opencode-ai@1.2.26` via npm
2. Filters noise files from the diff (lock files, vendor, generated code)
3. Annotates the diff with `[L<N>]` source-file line numbers
4. Pre-fetches PR context (CI status, existing reviews, linked issues)
5. Discovers Divisor personas from `.opencode/agents/divisor-*.md`
6. Builds a constrained review prompt with injection defense
7. Runs `opencode run` on Vertex AI
8. Parses structured JSON output and validates line numbers against the diff

## Rollout

Rollout is staged via `sync-config.yml` `exclude_repos`:

1. **Current**: Only org-infra receives the consumer workflows
2. **Phase 2**: Remove repos from `exclude_repos` after:
   - Composite action SHA points to a merged `main` commit
   - Security hardening (#429) is in place
   - Token consumption controls (#430) are in place
   - End-to-end chain validated on org-infra

## Manual trigger

To manually trigger a council review on an existing PR:

1. Find the collect workflow run ID from the PR's "Checks" tab
   (the "Council Review - Collect" run)
2. Go to Actions → "Council Review" → "Run workflow"
3. Select the PR's branch, enter the collect run ID

Or via CLI:

```bash
gh workflow run ci_council_review.yml \
  --repo complytime/org-infra \
  --ref <branch> \
  -f triggering_run_id=<collect-run-id>
```

## Bot comment lifecycle

All bot comments are tagged with `<!-- council-review-bot -->`.

On each new review:
1. Previous issue comments (summary) are **deleted**
2. Previous PR review comments (inline) are **deleted**
3. Previous Reviews API objects are **minimized** (collapsed as "outdated")
4. New summary and inline comments are posted

## Troubleshooting

### Review skipped — "No WIF credentials"

The `GCP_WORKLOAD_IDENTITY_PROVIDER` secret is not configured for this repo.
Set it at the org level or add a repo-level secret.

### Review skipped — "PR author is not a member"

Either the author is not an org member, or `ORG_CHECK_TOKEN` is not set and
the author's membership is private. Configure `ORG_CHECK_TOKEN` with a PAT
that has `org:read` scope.

### Review produced no inline comments

The model may have returned a summary-only review, or the diff was too small
to warrant inline findings. Check the review summary comment on the PR.

### Inline comments on wrong lines

The `[L<N>]` annotation in the diff helps the model identify correct line
numbers. If comments land on wrong lines, check:
- `filter-diff-lines.py` validation logic in the composite action
- Whether the diff has since been invalidated by new commits

### Credentials error — "Could not load the default credentials"

The WIF authentication succeeded but the credentials were not passed to
OpenCode. Check that `GOOGLE_APPLICATION_CREDENTIALS` is set in the
environment when `opencode run` executes.

## Related issues

- Security hardening: [#429](https://github.com/complytime/org-infra/issues/429)
- Token consumption controls: [#430](https://github.com/complytime/org-infra/issues/430)
- `continue-on-error` removal: [#440](https://github.com/complytime/org-infra/issues/440)
- Error handling hardening: [#454](https://github.com/complytime/org-infra/issues/454)
- Composite action tracking: [unbound-force#253](https://github.com/unbound-force/unbound-force/issues/253)
