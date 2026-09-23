## 1. Commit Body Version Extraction Fallback

- [x] 1.1 In `.github/workflows/reusable_dependabot_reviewer.yml`, in the "Get
  Dependency Information" step, add a commit body fallback block after the
  existing subject-line version extraction (line 95). When `versions` array has
  fewer than 2 entries, scan `COMMIT_BODY` for the pattern
  `from v?N.N.N to v?N.N.N` and re-populate the `versions` array.

## 2. PR Title Version Extraction Fallback

- [x] 2.1 In `.github/workflows/reusable_dependabot_reviewer.yml`, in the "Get
  Dependency Information" step, add a PR title fallback block after the commit
  body fallback. Pass `github.event.pull_request.title` as an environment
  variable (`PR_TITLE`). When `versions` array still has fewer than 2 entries
  after the body fallback, scan `PR_TITLE` with the same semver regex.

## 3. Derived Update Type

- [x] 3.1 In `.github/workflows/reusable_dependabot_reviewer.yml`, in the "Get
  Dependency Information" step, after all version extraction is complete, add
  logic to derive `update_type` from `from_version` and `to_version` when
  `update_type` is empty. Compare major/minor/patch components and set
  `update_type` to `version-update:semver-patch`, `version-update:semver-minor`,
  or `version-update:semver-major`.

## 4. Validation

- [x] 4.1 Run `make lint` to verify the modified workflow passes yamllint and
  all other linters with zero issues.
- [x] 4.2 Manually verify the extraction logic by tracing through the grouped
  Dependabot commit from PR complytime/complyscribe#836 (subject:
  `bump lxml in the pip group across 1 directory`, body: `Updates lxml from
  6.0.0 to 6.1.0`) and confirming the expected outputs: `from_version=6.0.0`,
  `to_version=6.1.0`, `update_type=version-update:semver-minor`,
  `risk_level=medium`.
