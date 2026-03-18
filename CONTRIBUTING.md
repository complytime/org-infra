# Contributing to org-infra

Thank you for your interest in contributing! Please refer to the
[organization-wide contribution guidelines](https://github.com/complytime/community/blob/main/CONTRIBUTING.md)
for general policies.

## Repository-Specific Notes

- Reusable workflows are prefixed with `reusable_` and consumer workflows with `ci_`.
- All workflow changes MUST follow the Principle of Least Privilege for permissions.
- Write permissions must be avoided. When necessary, they are defined in the minimal possible scope.
- Prefer defining explicit permissions per Job.
- The sync script (`scripts/sync-org-repositories.py`) can be tested with `--dry-run`.
- See [docs/LOCAL_TESTING.md](docs/LOCAL_TESTING.md) for detailed local testing instructions.
