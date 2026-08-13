## Context

The org-infra sync script (`scripts/sync-org-repositories.py`) synchronizes configuration files from org-infra to all downstream repositories. It processes a `files_to_sync` list from `sync-config.yml`, copying or transforming files into cloned downstream repos, then committing and pushing changes via PR.

The script currently has no mechanism to remove files from downstream repos. When a synced file is renamed or reformatted (e.g., issue templates converted from `.md` to `.yml`), the old file persists as an orphan. The immediate case is PR #390 which converted issue templates, leaving stale `.md` files across all downstream repos.

The sync flow in `sync_repository()` follows these steps:
1. Clone target repo to a temp directory
2. Set up credentials, check for existing sync PR
3. Loop through `files_to_sync` entries — copy/transform each file, track changes in `files_changed` list
4. Generate dependabot config
5. Commit all `files_changed`, push branch, create/update PR

File staging uses `repo.git.add(file_path)` for each changed file. The PR body and commit message list all files in `files_changed`.

## Goals / Non-Goals

**Goals:**
- Allow `sync-config.yml` entries to declare files they supersede, so the sync script deletes them from downstream repos
- Integrate deletion into the existing sync commit — no separate PRs or extra passes
- Provide clear visibility into deletions via commit messages and PR descriptions
- Maintain full backward compatibility — entries without `replaces` behave identically to today

**Non-Goals:**
- General-purpose file deletion unrelated to a replacement (no standalone "delete" entries)
- Glob/wildcard support in replacement paths (explicit paths only)
- Retroactive orphan detection or cleanup tooling
- Changes to the dependabot config generation path

## Decisions

### 1. `replaces` as an optional list on existing `files_to_sync` entries

Each `files_to_sync` entry gains an optional `replaces` key containing a list of file paths (relative to the downstream repo root) to delete.

```yaml
files_to_sync:
  - source: ".github/ISSUE_TEMPLATE/bug_report.yml"
    destination: ".github/ISSUE_TEMPLATE/bug_report.yml"
    replaces:
      - ".github/ISSUE_TEMPLATE/bug_report.md"
```

**Alternative considered: Separate `files_to_delete` top-level key.** Rejected because deletions are semantically tied to a replacement — keeping them together makes the relationship explicit and avoids coordination problems where a delete entry could run without its replacement being synced. It also follows the existing pattern of per-entry configuration (`exclude_repos`, `vars`).

**Alternative considered: `replaces` as a single string instead of a list.** Rejected because a single replacement file could supersede multiple old files (e.g., a consolidated config replacing two separate files). A list is more flexible and costs nothing when there is only one entry.

### 2. Delete superseded files using `os.remove()` + `repo.git.add()` (not `repo.git.rm()`)

The script will use `os.remove()` to delete the file from the working tree, then `repo.git.add(path)` to stage the deletion. This mirrors how the script already stages additions — using `repo.git.add()` for all changes — and avoids `git rm` which would error if the file does not exist in the index.

**Alternative considered: `repo.git.rm(path)`.** Rejected because `git rm` fails if the file is not tracked or does not exist. Since the replacement file may have already been manually removed or never existed in a particular downstream repo, silent no-ops on missing files are the correct behavior. Using `os.remove()` + `os.path.exists()` naturally handles this.

### 3. Process replacements during the file sync loop (Step 3)

Replacement processing happens inside the existing `for file_config in files_to_sync` loop, immediately after the replacement file is synced. For each path in `replaces`:
1. Check if the file exists in the downstream repo clone
2. If it exists, delete it with `os.remove()` and track it in `files_changed`
3. If it does not exist, skip silently (the file was already removed or never existed)

This approach processes replacements atomically with their associated file sync and requires no additional pass over the config.

**Alternative considered: Separate pass after all file syncs.** Rejected because it would decouple deletions from their replacements, making the code harder to follow and debug. Processing inline keeps the replacement relationship clear.

### 4. Track deleted files separately for reporting

Deleted files are appended to `files_changed` (so they are staged and committed) but also tracked in a separate `files_replaced` list. This allows the commit message and PR body to distinguish between "updated" and "removed (replaced by X)" entries.

**Alternative considered: Mix deletions into `files_changed` without distinction.** Rejected because reviewers of sync PRs need to understand that a file was intentionally removed as part of a replacement, not accidentally lost. Clear labeling reduces confusion and review friction.

### 5. Skip deletion when `exclude_repos` excludes the current repo

If a `files_to_sync` entry is excluded for the current repo via `exclude_repos`, its `replaces` entries are also skipped. The replacement and deletion are treated as a single unit — you cannot delete without also syncing the replacement.

**Alternative considered: Process `replaces` even for excluded repos.** Rejected because it would delete files without providing their replacement, which is the opposite of the intended behavior.

## Risks / Trade-offs

**[Risk] A `replaces` path targets a file the downstream repo intentionally keeps.**
→ Mitigation: Sync PRs require human review before merge. The PR description clearly lists removed files, giving maintainers the opportunity to reject the change. Additionally, `exclude_repos` can exempt specific repos from the entry entirely.

**[Risk] Typo in a `replaces` path silently does nothing.**
→ Mitigation: This is acceptable and by design — the file may not exist in every downstream repo. However, logging a message when a replacement target is not found provides visibility. A dry-run log entry (e.g., `[DRY RUN] Would remove (replaced): path`) makes it auditable before real runs.

**[Trade-off] No validation that `replaces` paths were ever synced files.**
→ Accepted: Adding a historical tracking system is out of scope and unnecessary complexity. The `replaces` mechanism is a declarative instruction, not a historical audit tool.

**[Risk] `replaces` entry refers to the same path as the `destination`.**
→ Mitigation: Skip the deletion for that path. The file is being written in the same commit, so deleting it would undo the sync.

**[Risk] Path traversal via `..` segments in `replaces` paths.**
→ Mitigation: Validate all `replaces` paths by canonicalizing the resolved path and verifying it stays within the cloned repository directory. Reject paths with `..` segments or that resolve outside the repo root. Log an error and skip the deletion.

**[Risk] `replaces` path points to a directory instead of a file.**
→ Mitigation: Check with `os.path.isfile()` rather than `os.path.exists()` to ensure only regular files are deleted. Skip directories silently — `os.remove()` would raise `IsADirectoryError` if attempted on a directory.

## Migration Plan

1. Add `replaces` support to the sync script (no behavior change for existing entries)
2. Add `replaces` entries to `sync-config.yml` for the issue template files from PR #390
3. Run `make sync-dry-run` to verify expected behavior
4. Merge and let the next sync cycle clean up downstream repos automatically

No rollback is needed — if the feature is reverted, orphaned files simply remain (the pre-existing state). No data loss is possible since deletions only happen via reviewed PRs.

## Open Questions

None — the scope is well-defined and the implementation is straightforward.
