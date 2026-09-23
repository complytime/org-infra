## Why

`reusable_release_preflight.yml` creates tags using `GITHUB_TOKEN`. GitHub's
anti-recursion rule prevents events from `GITHUB_TOKEN` from triggering other
workflows. Repos with downstream tag-triggered workflows (e.g., complypack's
container build) never fire after preflight creates a tag.

Closes [#485](https://github.com/complytime/org-infra/issues/485).

## Non-goals

- Enforcing token type (PAT vs. GitHub App token) at the workflow level — token
  policy is an org-level concern.
- Changing any existing workflow inputs, outputs, permissions, or concurrency
  settings.
- Adding new jobs or steps to the workflow.
- Syncing this workflow to other repos (it is not in `sync-config.yml`).

## What Changes

- Add an optional `tag_push_token` secret to `reusable_release_preflight.yml`.
- When provided, use it for the tag-creation step instead of `GITHUB_TOKEN`,
  allowing the new tag to trigger downstream workflows.
- Scope the elevated token to the single "Create and push tag" step via `env:`,
  not job-level or workflow-level, preventing privilege creep.
- Use the established fallback pattern
  (`secrets.tag_push_token != '' && secrets.tag_push_token || secrets.GITHUB_TOKEN`)
  already in use by `reusable_publish_ghcr.yml` (as `org_check_token`).
- Callers that don't pass a token get identical behavior to today.

## Capabilities

### New Capabilities

_(none — this change extends an existing capability)_

### Modified Capabilities

- `release-workflow`: Add optional elevated-token support for the tag-creation
  step so downstream tag-triggered workflows can fire.

## Impact

- **Workflow file**: `.github/workflows/reusable_release_preflight.yml` — single
  file change.
- **Callers**: Repos that need downstream triggering add a
  `secrets.tag_push_token` to their caller workflow. No change required for
  repos that don't need it.
- **Security surface**: Accepting an external token is a policy decision. Org
  admins should be aware so they can audit which repos pass elevated tokens.
  The secret description warns about recursive triggering risk.
