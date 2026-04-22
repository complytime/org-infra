## Why

The recent sync process refactoring (`robust-sync-process`) enabled `enable_trivy_source: true`
in `ci_security.yml`, which is synced identically to all organization repositories. Trivy source
scanning (secrets + misconfig) is valuable for repositories with actual source code but adds noise
and CI time to documentation, policy, and community repositories that have no meaningful attack
surface for these scanners. Additionally, the `call_reusable_vuln_scan` job grants `packages: write`
and `id-token: write` permissions that are only required by the `trivy_image` job, which is never
enabled in `ci_security.yml` -- violating the Principle of Least Privilege.

## What Changes

- Add a `vars` mechanism to `sync-config.yml` that allows per-repo value substitution when syncing
  workflow files, using `sync-config.yml` as the single source of truth.
- Configure `enable_trivy_source` per-repo: enabled for code repositories (Go/Python), disabled
  for docs/policy/community repositories.
- Remove unnecessary `packages: write` and `id-token: write` permissions from the
  `call_reusable_vuln_scan` job in `ci_security.yml`.
- Extend the sync script (`sync-org-repositories.py`) with text-based var substitution logic
  applied during file copy.

## Non-goals

- Building a general-purpose workflow templating engine. The `vars` mechanism is intentionally
  minimal (text substitution), not a full template system.
- Changing the reusable workflow (`reusable_vuln_scan.yml`) -- its inputs and defaults are correct.
- Managing `enable_trivy_image` via sync -- image scanning belongs in publish workflows, not
  `ci_security.yml`.

## Capabilities

### New Capabilities

- `sync-file-vars`: Per-file variable substitution during sync, driven by `sync-config.yml`.
  Allows workflow files to have per-repo customized values without maintaining separate templates.

### Modified Capabilities

_None. No existing spec-level requirements are changing._

## Impact

- **sync-config.yml**: New `vars` key added to the `ci_security.yml` file entry.
- **sync-org-repositories.py**: New substitution logic in the file sync path (~15-20 lines).
  File comparison logic updated to compare resolved content rather than source content.
- **ci_security.yml**: Permissions tightened on `call_reusable_vuln_scan` job. The
  `enable_trivy_source` value in the source file remains `true` (correct for org-infra); the sync
  script overrides it per-repo.
- **Tests**: New test coverage for var resolution, text substitution, and edge cases.
- **Downstream repos**: Next sync cycle will update `ci_security.yml` in all org repos with
  correct permissions and per-repo Trivy config.
