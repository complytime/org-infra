# Proposal: Sync Replaces Support

Resolves: [complytime/org-infra#397](https://github.com/complytime/org-infra/issues/397)

## Why

When org-infra syncs configuration files to downstream repositories, it can only add or update files — it has no mechanism to remove files that have been superseded. This creates orphaned files in downstream repos.

The immediate trigger is PR #390, which converted issue templates from `.md` to `.yml` format. The new `.yml` templates sync correctly, but the old `.md` templates remain in every downstream repo with no automated way to clean them up. Manual cleanup across all org repos is error-prone and does not scale.

This problem will recur any time a synced file is renamed, reformatted, or split into multiple files.

## What Changes

The sync script gains the ability to delete superseded files in downstream repositories when pushing their replacements.

A new optional `replaces` key is added to `sync-config.yml` file entries. When the sync script processes an entry with `replaces`, it deletes the listed files from the downstream repo as part of the same sync commit that adds the replacement file.

## Capabilities

### New Capabilities

- **`replaces` key in sync-config.yml**: Each `files_to_sync` entry can declare an optional `replaces` list of file paths (relative to the downstream repo root) that should be removed when the replacement is synced.
- **Superseded file deletion**: The sync script deletes files listed in `replaces` from the downstream repo during the sync operation, within the same branch and commit as the replacement file push.
- **Replacement reporting**: Sync PR descriptions and commit messages include information about which files were removed as replacements, providing visibility into what changed.

### Modified Capabilities

- **sync-config.yml schema**: Extended with the optional `replaces` field on file entries.
- **sync-org-repositories.py**: Updated to process `replaces` entries and perform file deletions in downstream repos.
- **Sync PR content**: PR descriptions updated to list any files removed due to replacement.

## Impact

- **Downstream repositories**: Superseded files are automatically cleaned up. No manual intervention required.
- **Existing sync entries**: No impact. The `replaces` key is optional; entries without it behave exactly as before.
- **Sync PRs**: PRs that include replacements will clearly list removed files, so reviewers understand the full scope of changes.

## Non-goals

- **Standalone file deletion**: This change does not add a general-purpose "delete these files" mechanism. Deletions are always tied to a replacement file being synced.
- **Retroactive cleanup**: This change does not automatically clean up files that were orphaned before the feature is deployed. Existing orphans can be addressed by adding `replaces` entries to current sync-config entries going forward.
- **Wildcard/glob patterns in replaces**: The initial implementation uses explicit file paths, not patterns. Each file to be removed must be listed individually. Explicit paths prevent accidental mass deletion and make the scope of each replacement auditable in review.

## Constitution Alignment

- **I. Single Source of Truth**: The `replaces` key is declared in `sync-config.yml`, the existing single source for sync configuration. No new config files introduced.
- **II. Simplicity & Isolation**: Minimal change — one optional key processed inline in the existing sync loop. No new modules or abstractions.
- **III. Incremental Improvement**: Focused on a single concern (file replacement during sync). No unrelated changes bundled.
- **IV. Composability**: Integrates into the existing sync mechanism following Unix philosophy — small, composable additions rather than a parallel system.
