# Build Production Workflow — Design

## Context

The council review test workflow (`ci_council_review_test.yml`) has validated
end-to-end connectivity: GitHub Actions → ITPC WIF pool → `unbound-force` GCP
project → Claude Sonnet 4.6 on Vertex AI via OpenCode CLI. Both `complytime`
and `unbound-force` GitHub orgs are registered with ITPC and have
`roles/aiplatform.user` IAM bindings on the `unbound-force` project.

No production workflow exists yet. The org follows a reusable workflow pattern
where `reusable_*.yml` workflows contain shared logic and `ci_*.yml` consumer
workflows call them. Consumer workflows sync to downstream repos via
`sync-config.yml`.

**Stakeholders**: org-infra maintainers, downstream repos consuming the
synced workflows, contributors using fork-and-pull.

## Goals / Non-Goals

**Goals:**

- Three-file workflow chain matching org convention (collect + consumer + reusable)
- Fork PR support via `workflow_run` (collect runs in fork context, review in upstream)
- Keyless authentication via ITPC WIF (no stored credentials)
- OpenCode CLI invocation with explicit model IDs via council-review-action
- Graceful degradation when WIF secrets are absent
- Cost controls (skip drafts, dependabot, concurrency, diff size limits)
- Smart diff filtering (exclude lock files, vendor, generated code)
- Inline review comments via GitHub Review API
- Follows all org conventions (SHA-pinned actions, minimal permissions, naming)
- Downstream repos receive consumer workflows via sync; reusable stays in org-infra

**Non-Goals:**

- Multi-model dynamic selection (future enhancement, not in v1)
- Persona prompt engineering or review output formatting
- GCP resource automation (Terraform/Pulumi)

## Decisions

### D1: Three-file workflow chain (org convention)

**Decision**: Use the org's standard reusable workflow pattern:

1. `ci_council_review_collect.yml` — fork-safe diff collection (synced)
2. `ci_council_review.yml` — thin consumer calling the reusable (synced)
3. `reusable_council_review.yml` — shared review logic (NOT synced, called cross-repo)

The consumer and collect workflows are synced to downstream repos via
`sync-config.yml`. Downstream repos call the reusable cross-repo:
`complytime/org-infra/.github/workflows/reusable_council_review.yml@SHA`.

**Alternative**: Single `pull_request` workflow with WIF gate.

**Why rejected**: The org uses a fork-and-pull model — fork PRs lack secrets
access. The two-step chain (collect in fork context, review in upstream
context via `workflow_run`) ensures all PRs are reviewed. The three-file
split matches how `ci_security.yml` / `reusable_security.yml` and other
org workflows are structured.

### D2: Composite action for review orchestration

**Decision**: Delegate review logic to `council-review-action` in
`unbound-force/unbound-force`. The composite action handles OpenCode
installation, Divisor agent discovery, prompt construction, review execution,
and output parsing. The reusable workflow handles org-specific concerns:
WIF auth, diff collection, and comment posting.

**Alternative**: Inline all review logic in the reusable workflow.

**Why rejected**: The composite action is reusable across orgs, testable
independently, and separates review methodology from infrastructure plumbing.

### D3: OpenCode CLI via npm (pinned version)

**Decision**: Install OpenCode CLI via `npm install -g opencode-ai@1.2.26`
(pinned to a specific version validated in production by gaze).

**Alternative A**: Claude Code CLI via `curl | bash`.

**Why rejected**: OpenCode supports multiple providers (including
`google-vertex-anthropic`) with native config, and the install script
is a `downloadThenRun` pattern that Scorecard flags.

**Alternative B**: Latest OpenCode via unpinned `npm install`.

**Why rejected**: Supply-chain risk — unpinned install in a workflow with
`id-token: write` and `pull-requests: write` permissions.

### D4: Explicit model IDs, not aliases

**Decision**: Use `google-vertex-anthropic/claude-sonnet-4-6` as the model ID.

**Alternative**: Use short aliases like `sonnet`.

**Why rejected**: Aliases can resolve to unexpected model versions. Explicit
IDs with provider prefix ensure the correct model is called via the correct
authentication path.

### D5: `global` region for Vertex AI

**Decision**: Set `VERTEX_LOCATION=global` for automatic capacity routing.

**Alternative**: Pin to `us-east5` (confirmed working region).

**Why rejected**: `global` routing was validated in the test workflow and
provides resilience against regional capacity issues.

### D6: Actions pinned to SHA

**Decision**: Pin all actions to full 40-character SHAs.

**Pinned versions:**

| Action                               | Version | SHA                                        |
| ------------------------------------ | ------- | ------------------------------------------ |
| `actions/checkout`                   | v6.0.3  | `df4cb1c069e1874edd31b4311f1884172cec0e10` |
| `actions/upload-artifact`            | v7.0.1  | `043fb46d1a93c77aae656e7c1c64a875d1fc6a0a` |
| `actions/download-artifact`          | v8.0.1  | `3e5f45b2cfb9172054b4087a40e8e0b5a5461e7c` |
| `google-github-actions/auth`         | v3.0.0  | `7c6bc770dae815cd3e89ee6cdf493a5fab2cc093` |
| `google-github-actions/setup-gcloud` | v3.0.1  | `aa5489c8933f4cc7a4f7d45035b3b1440c9c10db` |
| `council-review-action`              | (dev)   | SHA-pinned to feature branch commit        |

### D7: Inline review via GitHub Review API

**Decision**: Post review findings as inline comments on specific diff lines
via the Pull Request Review API, with a collapsible `<details>` fallback
when inline posting fails.

**Alternative**: Post all findings as a single PR comment.

**Why rejected**: Inline comments are more actionable — reviewers see
findings on the exact lines they apply to. The fallback ensures findings
are never lost.

### D8: Smart diff filtering

**Decision**: Filter out noise files (lock files, vendor directories,
generated code, test fixtures) before applying the line budget. A
`filter-diff-lines.py` script also drops inline comments targeting lines
outside diff hunks (GitHub API rejects these with HTTP 422).

**Alternative**: Naive `head -n` truncation.

**Why rejected**: A `go.sum` with 1500 lines would consume 75% of the
budget, leaving no room for actual code changes.

## Risks / Trade-offs

**[R1] `workflow_run` triggers only from default branch** — The `workflow_run`
event only fires when the collect workflow definition exists on the `main`
branch. During initial development, manual `workflow_dispatch` is needed for
testing. → Acceptable; once merged to main, it works automatically.

**[R2] Cost from Opus usage** — If Opus 4.6 is added later, cost per
review increases. → Mitigated by gate checks, concurrency control, and
GCP budget alerts.

**[R3] OpenCode CLI breaking changes** — A breaking change in OpenCode
could fail the workflow. → Mitigated by version pinning (`1.2.26`).

**[R4] Artifact retention** — Artifacts are retained for 1 day. If the
review workflow is delayed beyond that, the artifact will be deleted and
the review will fail. → Acceptable; `workflow_run` triggers immediately.

## Migration Plan

1. **Create workflows**: Add `ci_council_review_collect.yml`,
   `ci_council_review.yml`, and `reusable_council_review.yml`
2. **Validate**: Open a test PR, verify collect runs, consumer triggers,
   WIF auth succeeds, OpenCode responds, and inline comments are posted
3. **Remove test workflow**: Delete `ci_council_review_test.yml`
4. **Update sync config**: Add both `ci_*` files to `sync-config.yml`
   (reusable stays only in org-infra, called cross-repo by downstream)
5. **Sync to org repos**: Downstream repos receive the consumer workflows;
   they call the reusable cross-repo with SHA pin

**Rollback**: Remove the workflow files. No GCP resources need to be
torn down — they are inert without the workflow invoking them.
