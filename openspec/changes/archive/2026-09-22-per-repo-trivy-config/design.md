## Context

The sync script (`sync-org-repositories.py`) currently copies files verbatim from org-infra to
target repositories. It has no mechanism to customize file content per-repo -- files are either
synced as-is or excluded entirely via `exclude_repos`. The one exception is `dependabot.yml`, which
is dynamically generated from a dedicated `dependabot` config section.

`ci_security.yml` calls `reusable_vuln_scan.yml` with `enable_trivy_source: true` and grants
`packages: write` + `id-token: write` permissions to the vuln scan job. These permissions exist
solely for the `trivy_image` job, which is never enabled in this workflow. The hardcoded Trivy
source scan is useful for code repos but unnecessary for docs/policy repos.

Key files involved:
- `sync-config.yml` -- declarative sync configuration (single source of truth)
- `scripts/sync-org-repositories.py` -- sync script with file copy and dependabot generation logic
- `.github/workflows/ci_security.yml` -- consumer workflow (source template + org-infra's own)
- `tests/test_sync_org_repositories.py` -- pytest test suite for the sync script

## Goals / Non-Goals

**Goals:**
- Enable per-repo value customization of synced workflow files, driven by `sync-config.yml`
- Configure `enable_trivy_source` appropriately per repository
- Remove unnecessary elevated permissions from the vuln scan caller job
- Maintain backward compatibility with the existing sync process

**Non-Goals:**
- Full template engine (Jinja2, mustache, etc.)
- Modifying the reusable workflow inputs or defaults
- Managing `enable_trivy_image` or other workflow inputs not relevant to `ci_security.yml`
- Per-repo customization of non-workflow files (no current need)

## Decisions

### 1. Text substitution via regex, not YAML parse/rewrite

**Decision**: Use regex-based text substitution on the file content string to replace var values.

**Rationale**: YAML parsing and re-serialization would destroy comments, formatting, and the
carefully pinned SHA references (e.g., `@baf5b2e21e...  # v0.1.0`). Text substitution preserves
the source file byte-for-byte except for the targeted value.

**Pattern**: For each var, match `<var_name>:\s*\S+` and replace the value portion.

```python
import re
pattern = rf"({re.escape(var_name)}:\s*)\S+"
content = re.sub(pattern, rf"\g<1>{resolved_value}", content)
```

**Alternatives rejected:**
- **YAML parse/dump**: Destroys comments, reorders keys, reformats strings. Unacceptable for
  workflow files with SHA pins and inline version comments.
- **Jinja2 templates**: Would require the source file to contain template syntax (e.g.,
  `{{ enable_trivy_source }}`), making it invalid YAML and breaking org-infra's own workflow.
  Also adds a dependency.
- **Separate template files**: Maintaining both a template and a working workflow creates drift
  risk and duplication.

### 2. Config schema: `vars` as a per-file key in `files_to_sync`

**Decision**: Add an optional `vars` key to each `files_to_sync` entry. Each var has a `default`
value and a `repos` map of per-repo overrides.

```yaml
- source: .github/workflows/ci_security.yml
  destination: .github/workflows/ci_security.yml
  vars:
    enable_trivy_source:
      default: "false"
      repos:
        complyctl: "true"
        complytime: "true"
        complytime-providers: "true"
        complytime-collector-components: "true"
        gemara-content-service: "true"
        complyscribe: "true"
```

**Rationale**: Extends the existing per-file config structure naturally. `repos` as a map (not a
list) allows different values per repo in the future, not just boolean on/off.

**Alternatives rejected:**
- **Top-level `workflow_overrides` section**: Separates the var config from the file entry,
  making it harder to see the full picture for a given file.
- **`include_repos` list (boolean only)**: Less flexible. The `repos: { name: value }` map
  supports non-boolean vars if needed later, at zero additional complexity.
- **GitHub repository variables (`vars.ENABLE_TRIVY_SOURCE`)**: Decentralizes config -- each
  repo's settings live in GitHub UI, not in `sync-config.yml`. Violates single source of truth.

### 3. Resolve vars before file comparison

**Decision**: The sync script must compare the *resolved* content (after var substitution) against
the destination file, not the raw source content.

**Rationale**: Without this, the script would detect a diff on every run for repos where the
resolved value differs from the source file value, creating unnecessary commits and PR noise.

**Implementation**: Apply var substitution to the source content in memory, then compare with the
destination. If identical, skip. This affects both the normal sync path and the dry-run path.

### 4. Static permission fix in ci_security.yml

**Decision**: Remove `packages: write` and `id-token: write` from the `call_reusable_vuln_scan`
job permissions. These are only needed by the `trivy_image` job, which is never enabled in this
workflow.

The corrected permissions:

```yaml
call_reusable_vuln_scan:
  permissions:
    contents: read
    actions: read
    security-events: write
```

**Alternatives rejected:**
- **Making permissions dynamic via vars**: Permissions are not per-repo -- no repo needs
  `trivy_image` in `ci_security.yml`. A static fix is correct.
- **Keeping permissions for future use**: Violates Principle of Least Privilege. If
  `enable_trivy_image` is added later, permissions should be added then.

## Risks / Trade-offs

**[Risk] Regex matches unintended content** (e.g., a comment containing `enable_trivy_source`):
The var name is specific enough that false matches are extremely unlikely in a workflow file.
Mitigation: test with the actual file content; the regex replaces only the first match by default
but `re.sub` replaces all -- verify only one occurrence exists in the source file.

**[Risk] Var name not found in source file**: If a configured var doesn't exist in the file content
(e.g., typo in config), the substitution silently does nothing.
Mitigation: Log a warning when a var pattern produces zero matches. Include in test coverage.

**[Risk] Sync comparison correctness**: If the resolved-content comparison is not implemented
correctly, the script could either skip needed updates or create unnecessary PRs.
Mitigation: Explicit test cases comparing resolved vs. destination content.

**[Trade-off] Source file serves dual purpose**: `ci_security.yml` is both org-infra's own
workflow and the sync template. The source file retains `enable_trivy_source: true` (correct for
org-infra), while the sync script overrides it for other repos. This is acceptable because
org-infra is excluded from sync, but it means the source file alone doesn't show what downstream
repos receive.
Mitigation: `sync-config.yml` is the single source of truth for downstream values. The dry-run
mode should clearly show resolved values.
