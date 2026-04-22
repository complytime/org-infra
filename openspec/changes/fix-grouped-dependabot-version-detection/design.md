## Context

The `reusable_dependabot_reviewer.yml` workflow extracts dependency information
from Dependabot commits using a three-source pipeline:

1. **Commit metadata** -- parses the `updated-dependencies` YAML block for
   `dependency-name`, `dependency-version`, and `update-type`.
2. **Commit subject** -- regex extracts semver patterns (`v?N.N.N`) for
   `from_version` and `to_version`.
3. **Diff enrichment** -- extracts SHA-pinned action refs for usage search.

The "Classify Risk" step then uses two paths:
- **Primary**: `update-type` from metadata (e.g., `semver-minor`).
- **Fallback**: Compares `from_version` vs `to_version` numerically.

**Grouped Dependabot PRs** break both paths because they:
- Omit `update-type` from the metadata block (only include `dependency-group`).
- Use a subject like `bump lxml in the pip group across 1 directory` with no
  version numbers.

The version data is available in the commit body text
(`Updates \`lxml\` from 6.0.0 to 6.1.0`) and in the PR title, but neither
source is currently consulted.

## Goals / Non-Goals

**Goals:**

- Populate `from_version` and `to_version` for grouped Dependabot PRs so the
  semver comparison fallback in "Classify Risk" works correctly.
- Derive `update_type` from extracted versions when the metadata field is absent.
- Preserve the existing extraction priority: commit metadata remains the primary
  source; new fallbacks only activate when existing sources yield incomplete data.

**Non-Goals:**

- Changing the risk classification thresholds or auto-approval criteria.
- Supporting extraction of multiple dependencies from a single grouped PR
  (existing first-dependency heuristic is retained).
- Migrating to a different extraction approach (e.g., GitHub API for PR metadata
  instead of commit parsing).

## Decisions

### Decision 1: Add commit body version extraction as second fallback

**Choice**: When the commit subject yields fewer than two semver matches, scan
`COMMIT_BODY` for the pattern `from v?N.N.N to v?N.N.N`.

**Alternatives considered**:
- **Use PR title only** (via `github.event.pull_request.title`): Simpler, but
  the PR title is not available in all workflow trigger contexts (e.g., manual
  re-runs or `workflow_dispatch`). The commit body is always available once the
  repo is checked out.
- **Parse the `dependency-group` metadata field** to infer update type: Does not
  help because grouped metadata still omits per-dependency version ranges.

**Rationale**: The commit body is always accessible after checkout and contains
machine-generated text from Dependabot with a stable format
(`Updates \`<name>\` from <old> to <new>`). This makes it a reliable and
self-contained fallback.

### Decision 2: Add PR title as a third fallback source

**Choice**: If neither the commit subject nor body yield version numbers, fall
back to `github.event.pull_request.title` which uses the format
`bump <name> from X.Y.Z to A.B.C in the <group>`.

**Alternatives considered**:
- **Omit PR title fallback**: Fewer code paths to maintain. Rejected because the
  PR title contains version info in scenarios where the commit body format may
  differ (e.g., multi-dependency grouped PRs).
- **Use GitHub API to fetch PR details**: Over-engineered for this use case; the
  PR title is already available in the event payload.

**Rationale**: Defense in depth. The PR title is available at no extra cost from
the event context and covers edge cases where the commit body format varies.

### Decision 3: Derive update_type from versions when metadata is absent

**Choice**: After extracting `from_version` and `to_version`, if `update_type`
is still empty, compute it by comparing major/minor/patch components and set it
to `semver-patch`, `semver-minor`, or `semver-major`.

**Alternatives considered**:
- **Only fix the fallback path in "Classify Risk"**: The fallback already
  compares versions, so populating `from_version` alone would fix classification.
  However, this leaves `UPDATE_TYPE` empty in `GITHUB_ENV`, meaning downstream
  consumers (PR comment, future steps) cannot reference it.

**Rationale**: Computing `update_type` keeps the data model complete for all
downstream consumers, not just the classification step. The computation is
trivial and mirrors the existing logic in "Classify Risk."

## Risks / Trade-offs

- **[Risk] Commit body format changes**: Dependabot could change the body text
  format in future versions. **Mitigation**: The regex is conservative (looks for
  `from v?N.N.N to v?N.N.N` anywhere in the body) and the fallback chain means
  other sources would compensate. The existing metadata extraction has the same
  dependency on Dependabot's format.

- **[Risk] PR title not available in non-PR contexts**: If the workflow is
  triggered via `workflow_dispatch` or re-run, the PR title may be empty.
  **Mitigation**: The PR title is the third and final fallback; commit body is
  tried first. Empty PR title is handled by the existing guard
  (`[[ -z "$to_version" ]]`).

- **[Trade-off] Slightly more complex extraction logic**: Three version sources
  instead of one. **Mitigation**: The fallback chain is linear and
  well-commented. Each source is tried only when previous sources yield
  incomplete data, keeping the fast path unchanged.

## Open Questions

_None -- the approach is straightforward and all data sources are verified from
the failing CI job._
