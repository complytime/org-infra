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

## Engineering Constitution

This organization follows the [ComplyTime Constitution](.specify/memory/constitution.md) — a set of
engineering principles and coding standards that apply to all repositories and contributors (human and AI).
It covers commit conventions, code review requirements, coding standards per language, and security practices.
All changes MUST comply with the constitution's normative rules (RFC 2119: MUST/SHOULD/MAY).
