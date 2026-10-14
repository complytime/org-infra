# Design

## Context

The Dependabot reviewer pipeline (`reusable_dependabot_reviewer.yml`) already
extracts dependency metadata, classifies risk, checks release age, detects org
ownership, and searches GitHub for usage. The consumer workflow
(`ci_dependencies.yml`) uses those signals to auto-approve and optionally
auto-merge. See `proposal.md` for the motivation behind adding a cross-repo
precedent signal.

Current approval paths:

- **Path A** (third-party): risk != high + review pass + release >= 24h
  --> auto-approve only
- **Path B** (org-owned): risk != high + review pass --> auto-approve +
  auto-merge

Both workflows are synced to all org repos via `sync-config.yml`.

## Goals / Non-Goals

**Goals:**

- Add a precedent lookup step that detects whether the same dep@version was
  merged with human approval in another org repo.
- Extend the approval matrix with Path C (org precedent) to auto-approve +
  auto-merge when precedent exists and all existing gates pass.
- Surface the precedent signal in the PR comment for maintainer transparency.

**Non-Goals:**

- Changing the existing Path A or Path B conditions (beyond extending
  auto-merge eligibility).
- Adding new secrets, GitHub Apps, or infrastructure.
- Building a persistent registry or event-driven dispatch system.

## Decisions

### Decision 1: GitHub Search API for precedent detection

**Choice**: Use `gh search prs` to find merged Dependabot PRs matching the
same dependency and version across the org.

**Alternatives considered**:
- **Shared registry** (JSON file in org-infra, GitHub gist, or issue):
  Requires write access to a shared location on every merge event. Adds
  infrastructure and a new failure mode (stale/corrupt registry). Rejected
  because the API approach requires zero infra.
- **Cross-repo `repository_dispatch`**: On merge in repo A, dispatch events
  to repos with matching open PRs. Requires knowing which repos have open PRs
  (chicken-and-egg) and a dispatch mechanism. Too complex for the value.

**Rationale**: The search API is free, requires no infrastructure, and the
existing workflow already uses it for the "Dependency Usage" popularity check.
The failure mode is clean: search fails --> `org_precedent=false` --> existing
behavior.

### Decision 2: `--review approved` pre-filter + Reviews API verification

**Choice**: Use `--review approved` in the search query to pre-filter PRs that
had at least one approval, then use the Reviews REST API to verify the
approval came from a human (not a bot).

**Alternatives considered**:
- **`--review approved` only** (no Reviews API call): Cannot distinguish human
  from bot approvals. The pipeline's own auto-approve step creates bot
  approvals on every eligible PR, so this filter alone would match PRs that
  were never human-reviewed. Rejected for circular trust risk.
- **`--reviewed-by <user>` filter**: Would require knowing maintainer usernames
  upfront or maintaining a list. Rejected as it violates the "no configuration"
  requirement.

**Rationale**: The two-step approach (search pre-filter + API verification)
minimizes API calls while correctly distinguishing human from bot approvals.
The Reviews REST API has a 5000 req/hr limit (vs 30 req/min for search), so
the additional calls are negligible.

### Decision 3: Human detection via `user.type != "Bot"`

**Choice**: Identify human reviewers by checking `user.type != "Bot"` in the
Reviews API response.

**Alternatives considered**:
- **Blocklist of known bot logins** (e.g., `github-actions[bot]`,
  `dependabot[bot]`): Fragile -- new bots would bypass the list. Rejected.
- **Allowlist of known human logins**: Requires maintenance. Rejected.
- **Check `user.type == "User"`**: Equivalent to `!= "Bot"` for practical
  purposes. GitHub account types are `User`, `Bot`, `Organization`, and
  `Mannequin`. Using `!= "Bot"` is more explicit about intent.

**Rationale**: The `user.type` field is a stable part of the GitHub API.
Filtering on `!= "Bot"` correctly excludes `github-actions[bot]` (the author
of auto-approve reviews) and any future bot accounts, without requiring a
maintained list.

### Decision 4: Title-based search matching

**Choice**: Search for `"${DEP_NAME} ${DEP_VERSION}"` in PR titles using
`--match title`.

**Alternatives considered**:
- **Full-text search** (title + body): Higher recall but more false positives.
  Dependabot PR titles are predictable and sufficient. Rejected.
- **Exact title match**: Too rigid -- Dependabot title format varies slightly
  (`Bump X from A to B` vs `Update X requirement from A to B` vs prefixed
  with `ci(deps):`). Rejected.

**Rationale**: Searching for both `DEP_NAME` and `DEP_VERSION` in the title,
combined with `--author dependabot[bot]` and `--merged`, is precise enough to
avoid false positives while accommodating title format variations.

### Decision 5: Release age gate applies to precedent path

**Choice**: Path C requires `release_age >= 24h`, same as Path A.

**Alternatives considered**:
- **Skip release age with precedent**: The human review is arguably a stronger
  signal than a time-based heuristic. However, the 24h gate serves a different
  purpose: it gives the security community time to discover and publish
  advisories for compromised releases. A human reviewer cannot detect a
  supply-chain attack that hasn't been disclosed yet. Rejected.

**Rationale**: The release age gate and human review serve orthogonal purposes.
Keeping both ensures defense in depth.

### Decision 6: Placement in the reusable workflow

**Choice**: Add the precedent check as a new step in
`reusable_dependabot_reviewer.yml`, after the existing "Search GitHub for
Dependency Usage" step.

**Alternatives considered**:
- **Separate reusable workflow**: Adds another `workflow_call` and job in the
  consumer. Increases complexity and run time (parallel job overhead). Rejected.
- **Inline in `ci_dependencies.yml`**: The consumer is a thin orchestrator;
  adding logic there breaks the pattern. Rejected.

**Rationale**: The step naturally belongs alongside the other dependency
analysis steps. It uses the same inputs (`DEP_NAME`, `DEP_VERSION`) and
follows the same patterns (search with retry, output to `GITHUB_OUTPUT`).

### Decision 7: Retry strategy

**Choice**: Use the same retry pattern as the existing "Search GitHub for
Dependency Usage" step: 3 attempts with exponential backoff (15s, 30s, 45s),
30-second timeout per attempt.

**Alternatives considered**:
- **No retry**: The search API is occasionally flaky. The existing step already
  retries for this reason. Using the same pattern ensures consistency. Rejected.

**Rationale**: Consistency with the existing search pattern. The retry loop is
proven in production.

## Risks / Trade-offs

- **[Search API reliability]** The GitHub Search API occasionally returns
  incomplete results or rate-limits.
  --> Mitigation: Graceful fallback to `org_precedent=false`. Retry with
  backoff. Precedent is additive, never a gate.

- **[False positive on title match]** A non-Dependabot PR or unrelated update
  could match the search query.
  --> Mitigation: The query combines `--author dependabot[bot]` + `--merged` +
  `--review approved` + `--match title` with both dep name and version. False
  positives require an adversary to control Dependabot's PR titles, which is
  outside the threat model.

- **[Circular trust]** If only bot-approved merges were counted, the first
  auto-approved repo would cascade trust to all others with no human in the
  loop.
  --> Mitigation: Human approval verification (Decision 2) prevents this.
  Only merges with a human `APPROVED` review count as precedent.

- **[Follower PRs don't auto-re-evaluate]** After the seed PR merges, follower
  PRs won't automatically re-run CI. They pick up the precedent on next CI
  trigger (manual re-run or dependabot rebase).
  --> Mitigation: Acceptable for v1. A scheduled sweep workflow can be added
  later if the delay is operationally significant.

- **[Major bump auto-merge with precedent]** A major bump reviewed in one repo
  might have different impact in another repo that uses the dependency
  differently.
  --> Mitigation: `risk != high` gate blocks all major bumps from Path C,
  regardless of precedent.

## Migration Plan

No migration needed. The change is additive:

1. New step + outputs in `reusable_dependabot_reviewer.yml`
2. Extended conditions in `ci_dependencies.yml`
3. Both files sync automatically to downstream repos

Rollback: revert the two workflow files. No state to clean up, no registry
to remove, no secrets to rotate.
