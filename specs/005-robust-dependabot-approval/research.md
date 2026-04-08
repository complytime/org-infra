# Research: Robust Dependabot Auto-Approval

**Branch**: `005-robust-dependabot-approval` | **Date**: 2026-04-08

## R1: Dependabot Commit Metadata Availability

**Decision**: Use dependabot commit body metadata as primary extraction source, with diff parsing and title parsing as fallbacks.

**Rationale**: Dependabot commit messages typically contain a structured `updated-dependencies` YAML block in the commit body with `dependency-name`, `dependency-version`, `dependency-type`, and `update-type` fields. However, this metadata is **not guaranteed** for all ecosystems or configurations. Some dependency types (e.g., pre-commit hooks, less common registries) may not produce this block. The extraction must handle its absence gracefully by falling back to diff parsing and then to commit title parsing.

**Findings**:
- The `updated-dependencies` block is a YAML fragment embedded in the commit body, separated by `---` and `...` markers.
- Fields: `dependency-name` (full qualified name), `dependency-version` (new version only), `dependency-type` (direct:production, direct:development), `update-type` (version-update:semver-major, version-update:semver-minor, version-update:semver-patch).
- The `from_version` is NOT included in the metadata block; it appears only in the commit title/body prose ("from X to Y").
- Parsing is achievable with simple `grep`/`sed` -- no YAML parser needed.

**Alternatives considered**:
- Diff-only parsing (current approach): Fragile, 112 lines of complex bash, crashes on composite action files. Rejected as primary source.
- Commit metadata only (no diff parsing): Would lose SHA-pinned ref extraction needed for usage search queries. Rejected as sole source.
- External action for extraction (e.g., dependabot/fetch-metadata): Adds an external dependency. Rejected per constitution Principle V (vet dependencies) and simplification constraint.

## R2: Release Date Lookup Per Ecosystem

**Decision**: Implement ecosystem-specific release date lookups using lightweight API calls available in the workflow environment.

**Rationale**: Release date information is needed for the 24-hour cooling-off check. Different ecosystems expose this data through different APIs. Not all ecosystems provide reliable release date information. When unavailable, the system defaults to "unknown" and blocks auto-approval (safe default).

**Findings**:

| Ecosystem | API | Field | Auth Required |
|-----------|-----|-------|---------------|
| GitHub Actions | `gh api repos/{owner}/{repo}/releases/tags/v{version}` | `.published_at` | GH_TOKEN (available) |
| GitHub Actions (tag only) | `gh api repos/{owner}/{repo}/git/ref/tags/v{version}` | tag object date | GH_TOKEN (available) |
| Go modules | `curl https://proxy.golang.org/{module}/@v/v{version}.info` | `.Time` | None |
| Python/pip | `curl https://pypi.org/pypi/{package}/{version}/json` | `.urls[0].upload_time_iso_8601` | None |
| Unknown/other | N/A | N/A | N/A |

- GitHub Actions releases: Most actions use GitHub Releases. Fall back to tag creation date if no release exists.
- Go modules: The Go proxy provides a JSON endpoint with a `Time` field in RFC3339 format.
- Python/pip: PyPI provides JSON metadata per version with upload timestamps.
- For unknown ecosystems or when the API call fails: `release_age_hours` is set to `-1` (unknown), blocking auto-approval.

**Alternatives considered**:
- Single API approach (GitHub-only): Would not cover Go or Python ecosystems. Rejected.
- Third-party release monitoring service: Adds external dependency and complexity. Rejected.
- Skip release age check entirely: Does not meet FR-002. Rejected.

## R3: Auto-Approval Condition Fix

**Decision**: Reference workflow job outputs directly in the `if:` condition using `needs.*` context instead of step-level `env:`.

**Rationale**: The current `ci_dependencies.yml` auto-approve step uses step-level `env:` to pass values from `needs` outputs, then references them in the step's `if:` condition. While technically valid in GitHub Actions, this pattern is non-idiomatic and confusing. Moving to direct `needs.*` references in the `if:` is clearer and avoids the string-to-number coercion issue with `UPDATES_COUNT`.

**Findings**:
- Step-level `env:` IS available to the same step's `if:` in GitHub Actions (not a bug).
- The `env.UPDATES_COUNT > 10` comparison involves string-to-number coercion, which silently evaluates to `false` if the value is empty.
- Best practice: use `needs.<job>.outputs.<output>` directly in `if:` conditions.

**Alternatives considered**:
- Keep current env pattern: Works but confusing and masks failures. Rejected.
- Job-level `env:`: Evaluated too early (before `needs` outputs available). Not viable.

## R4: Complexity Reduction Analysis

**Decision**: Net reduction in bash complexity by replacing 112-line diff parser with ~30-line metadata+fallback extractor.

**Rationale**: The user explicitly requires the implementation to simplify or at least not increase complexity. The current extraction step is 112 lines of bash with nested loops, temp file I/O, and `set -e`. The proposed approach replaces this with structured metadata parsing (~10 lines), simplified diff enrichment (~10 lines), and title fallback (~10 lines).

**Findings**:

| Component | Current Lines | Proposed Lines | Change |
|-----------|--------------|----------------|--------|
| Dependency extraction (bash) | 112 | ~30 | -82 |
| Risk classification | 30 | ~15 | -15 |
| Ecosystem detection | 23 | ~23 | 0 |
| Usage search | 60 | ~55 | -5 |
| Release age check (new) | 0 | ~35 | +35 |
| **Total reusable_dependabot_reviewer.yml** | **~278** | **~210** | **-68** |
| Auto-approval condition | 5 | 10 | +5 |
| PR comment template | 18 | 30 | +12 |
| **Total ci_dependencies.yml** | **~86** | **~103** | **+17** |
| **Net change** | **~364** | **~313** | **-51** |

Net reduction of ~51 lines, with significantly reduced logical complexity (no nested loops, no temp files, no `set -e`).

**Alternatives considered**:
- Adding a separate script file for extraction: Would reduce workflow line count but add another file to maintain. Deferred (could be a future improvement).
