# Quickstart: Release Workflow for org-infra

## For Maintainers (Creating a Release)

### 1. Preview the release notes (optional)

Run the preview workflow to see what the next release changelog will contain:

```bash
gh workflow run release_notes_preview.yml
```

Check the Actions tab for the job summary, or download the `release-notes-preview` artifact.

### 2. Create a release

Trigger the release workflow with a semver tag:

```bash
# From the CLI
gh workflow run release.yaml -f tag=v1.0.0
```

Or use the Actions tab: select **Release**, click **Run workflow**, enter the tag.

The workflow will:
1. Validate the tag format (`v<major>.<minor>.<patch>` or `v<major>.<minor>.<patch>-rc.<n>`)
2. Create and push the tag if it does not already exist
3. Publish a GitHub Release with auto-generated changelog

### 3. Verify the release

```bash
# Check the release was created
gh release view v1.0.0

# List all releases
gh release list
```

## For Downstream Consumers (Pinning to a Release)

### Update your caller workflows

Replace `@main` with a release tag:

```yaml
# Before (living edge — not recommended)
uses: complytime/org-infra/.github/workflows/reusable_ci.yml@main

# After (pinned to release tag)
uses: complytime/org-infra/.github/workflows/reusable_ci.yml@v1.0.0
```

For maximum reproducibility, pin to the release commit SHA:

```yaml
uses: complytime/org-infra/.github/workflows/reusable_ci.yml@<sha>
```

### Upgrading to a new release

1. Check the [Releases page](https://github.com/complytime/org-infra/releases) for new versions
2. Read the changelog — pay attention to **Breaking changes** section
3. Update the tag in your caller workflow
4. Test in a feature branch before merging

## How Version Bumps Work

Version numbers are resolved automatically from PR labels:

| Label(s) | Version bump | Example |
|----------|-------------|---------|
| `breaking`, `major` | Major | v1.0.0 → v2.0.0 |
| `feature`, `enhancement`, `minor` | Minor | v1.0.0 → v1.1.0 |
| `fix`, `workflows`, `compliance`, `maintenance`, etc. | Patch | v1.0.0 → v1.0.1 |
| No matching labels | Patch (default) | v1.0.0 → v1.0.1 |

Labels are auto-assigned by the release-drafter autolabeler based on:
- Conventional commit prefixes in PR titles (e.g., `feat:` → `feature`)
- File paths changed (e.g., `.github/workflows/**` → `workflows`)

## Troubleshooting

### Release workflow fails with "Tag must match semver format"

The tag input must match `v<major>.<minor>.<patch>`.
Examples: `v1.0.0`, `v2.1.3`. Tags like `1.0.0` (missing `v`) or `v1.0` (missing patch)
are rejected.

### Changelog is empty or missing PRs

- PRs must be merged to the default branch to appear in the changelog
- PRs labeled `skip-changelog` are excluded
- Dependabot PRs are excluded by default
- If a PR has no labels and the autolabeler did not match, it may be excluded

### Release notes preview shows unexpected version

The version is resolved from PR labels since the last release tag. If PRs have incorrect labels
(e.g., a breaking change labeled as `fix`), the resolved version will be wrong. Fix the PR labels
and re-run the preview.
