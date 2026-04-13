# Data Model: Robust Dependabot Auto-Approval

**Branch**: `006-robust-dependabot-approval` | **Date**: 2026-04-08

## Workflow Data Flow

This feature modifies two workflow files. Data flows between jobs via GitHub Actions `outputs`.

### reusable_dependabot_reviewer.yml Outputs

| Output | Type | Description | Possible Values |
|--------|------|-------------|-----------------|
| `risk_level` | string | Semantic version risk classification | `low` (patch), `medium` (minor), `high` (major/unknown) |
| `updates_count` | string (number) | Repositories using this dependency version | `0`..`N`, informational only |
| `release_age_hours` | string (number) | Hours since the dependency version was released | `0`..`N`, or `-1` if unknown |
| `dep_name` | string | Fully qualified dependency name | e.g., `docker/setup-buildx-action`, `golang.org/x/net` |
| `dep_version` | string | New dependency version | e.g., `4.0.0`, `0.35.0` |

### reusable_deps_reviewer.yml Outputs (unchanged)

| Output | Type | Description | Possible Values |
|--------|------|-------------|-----------------|
| `review_conclusion` | string | Dependency vulnerability/security review result | `success`, `failure` |

### ci_dependencies.yml Data Consumption

The orchestrator workflow consumes outputs from both reusable workflows:

```text
call_deps_reviewer ──────┐
                         ├──► comment_on_dependabot_prs (all outputs → PR comment)
call_dependabot_reviewer ┤
                         └──► approve_dependabot_prs (risk_level, release_age_hours, review_conclusion)
```

### Auto-Approval Decision Matrix

| risk_level | review_conclusion | release_age_hours | CI Status | Decision |
|------------|-------------------|-------------------|-----------|----------|
| low | success | >= 24 | passing | AUTO-APPROVE |
| medium | success | >= 24 | passing | AUTO-APPROVE |
| high | success | >= 24 | passing | MANUAL REVIEW |
| low | failure | >= 24 | passing | MANUAL REVIEW |
| low | success | < 24 | passing | MANUAL REVIEW |
| low | success | -1 (unknown) | passing | MANUAL REVIEW |
| low | success | >= 24 | failing | MANUAL REVIEW |
| * | * | * | * | MANUAL REVIEW (default) |

### Extraction Fallback Chain

```text
Source 1: Commit body metadata (updated-dependencies block)
  ├── dependency-name    → dep_name
  ├── dependency-version → dep_version (to_version)
  └── update-type        → risk_level (direct mapping)

Source 2: Git diff (supplementary enrichment)
  ├── uses: name@sha     → USES_QUERY (for GitHub Actions usage search)
  └── version comments   → from_version (informational)

Source 3: Commit title/body text
  ├── "Bump X" / "Update X" → dep_name (fallback)
  └── "from A to B"         → from_version, to_version (fallback)
```

### Environment Variables (internal to workflow steps)

| Variable | Set By | Used By | Description |
|----------|--------|---------|-------------|
| `DEP_NAME` | Extract step | Risk, Ecosystem, Release Age, Usage | Dependency name |
| `DEP_VERSION` | Extract step | Release Age, Outputs | New version (primary; same value as TO_VERSION) |
| `FROM_VERSION` | Extract step | Comment (informational) | Old version (from commit title "from X to Y") |
| `TO_VERSION` | Extract step | Comment (informational) | New version (alias of DEP_VERSION for display consistency) |
| `UPDATE_TYPE` | Extract step | Risk classification | semver-major/minor/patch |
| `USES_QUERY` | Extract step | Usage search | SHA-pinned action ref for code search |

### PR Comment Structure

```text
🤖 Standardized Dependabot Review Summary 🤖

- Dependencies Review: {review_conclusion}
- Calculated Risk: {risk_level}
- Release Age: {release_age_hours}h ({release_age_status})
- Dependency Usage: {updates_count} repositories (informational)

Auto-approval: {decision} — {rationale}

---

Maintainer checklist:
1. Ensure the PR passed all CI tests.
2. Investigate failures for major updates or manual review requirements.
3. Review breaking changes and changelog information.
4. If the scorecard value is low, consider contributing to improve it.
5. Be diligent. When in doubt, ask another maintainer.
```
