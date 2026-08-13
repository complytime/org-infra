<!-- spec-review: passed -->
<!-- code-review: passed -->

## 1. Core Implementation

- [ ] 1.1 Add `replaces` processing logic to `sync_repository()` in `scripts/sync-org-repositories.py`: after syncing each `files_to_sync` entry, iterate over the optional `replaces` list, delete existing files with `os.remove()`, stage deletions with `repo.git.add()`, and track them in both `files_changed` and a separate `files_replaced` list (mapping removed path to replacement destination)
- [ ] 1.2 Skip `replaces` processing when the entry is excluded for the current repo via `exclude_repos` (ensure the existing `continue` short-circuits both sync and replacement)
- [ ] 1.3 Add dry-run support for replacements: when `dry_run=True`, print `[DRY RUN] Would remove (replaced): <path>` for each existing superseded file without deleting
- [ ] 1.4 Add path traversal validation for `replaces` entries in `scripts/sync-org-repositories.py`: reject paths containing `..` segments or resolving outside the repository clone root, log an error, and skip the deletion
- [ ] 1.5 Skip deletion when the `replaces` path is a directory or matches the entry's `destination` path

## 2. Reporting

- [ ] 2.1 Update the commit message in `sync_repository()` (`scripts/sync-org-repositories.py`) to list replaced files in a separate "Removed files (replaced)" section, including which file replaced them
- [ ] 2.2 Update the PR body construction in `sync_repository()` (`scripts/sync-org-repositories.py`) to add a "Files Removed (Replaced)" section when `files_replaced` is non-empty

## 3. Configuration

- [ ] 3.1 Add `replaces` entries to `sync-config.yml` for the issue template files superseded by PR #390 (`.github/ISSUE_TEMPLATE/bug_report.md`, `.github/ISSUE_TEMPLATE/feature_request.md`, etc.)

## 4. Tests

- [ ] 4.1 Add unit test in `tests/` for `replaces` processing: verify that an existing superseded file is deleted, tracked in `files_changed`, and tracked in `files_replaced` with its replacement source
- [ ] 4.2 Add unit test for `replaces` with a non-existent file: verify silent skip with no error
- [ ] 4.3 Add unit test for `replaces` skipped when `exclude_repos` matches the current repo
- [ ] 4.4 Add unit test for dry-run mode with `replaces`: verify stdout contains `[DRY RUN] Would remove (replaced): <path>` for each existing superseded file, and verify no files are actually deleted
- [ ] 4.5 Add unit test for `replaces` with multiple paths: verify all existing files are deleted and tracked in both `files_changed` and `files_replaced`
- [ ] 4.6 Add unit test verifying commit message includes "Removed files (replaced):" section when `files_replaced` is non-empty, and that the format matches `- <removed_path> (replaced by <replacement_path>)`
- [ ] 4.7 Add unit test verifying PR body includes "## Files Removed (Replaced)" section when replacements occur, and PR body is unchanged when no replacements exist
- [ ] 4.8 Add unit test for path traversal validation: verify `replaces` path with `..` segments is rejected with error log and no deletion
- [ ] 4.9 Add unit test for `replaces` path that is a directory: verify skip without error
- [ ] 4.10 Add unit test for `replaces` path matching the entry's `destination`: verify skip (no self-deletion)

## 5. Validation

- [ ] 5.1 Run `make lint` to verify `ruff` and `yamllint` pass on all modified files
- [ ] 5.2 Run `make test` to verify all existing and new tests pass
- [ ] 5.3 Run `make sync-dry-run` to verify the dry-run output includes expected replacement messages for the configured issue template entries
