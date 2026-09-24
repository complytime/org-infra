<!-- spec-review: passed -->

## MODIFIED Requirements

### Requirement: Conditional tag creation
The release preflight workflow SHALL accept an optional `tag_push_token` secret.
When provided, the tag-creation step SHALL use the provided token instead of
`GITHUB_TOKEN`, enabling the new tag event to trigger downstream workflows.

#### Scenario: Tag created with default token (no secret provided)
- **WHEN** a caller invokes the preflight workflow without providing the `tag_push_token` secret
- **AND** the provided tag does not exist in the repository
- **THEN** the tag-creation step uses `GITHUB_TOKEN` as `GH_TOKEN` in its `env:` block

> _Rationale: Tags created with `GITHUB_TOKEN` do not trigger downstream
> workflows due to GitHub's anti-recursion rule._

#### Scenario: Tag created with elevated token
- **WHEN** a caller provides an elevated token via the `tag_push_token` secret
- **AND** the provided tag does not exist in the repository
- **THEN** the tag-creation step uses the provided token as `GH_TOKEN` in its `env:` block

> _Rationale: Tags created with a non-`GITHUB_TOKEN` credential (PAT or GitHub
> App token) are eligible to trigger downstream tag-triggered workflows._

#### Scenario: Tag already exists (re-run)
- **WHEN** the provided tag already exists at HEAD
- **THEN** the tag creation step is skipped regardless of whether a `tag_push_token` secret was provided

#### Scenario: Provided token lacks sufficient permissions
- **WHEN** a caller provides an elevated token via the `tag_push_token` secret
- **AND** the token lacks `contents:write` permission or is expired
- **THEN** the tag-creation step fails with an error
- **AND** the workflow does not fall back to `GITHUB_TOKEN`

---

## ADDED Requirements

### Requirement: Elevated token scoped to tag-creation step
The provided `tag_push_token` secret SHALL only be used by the tag-creation step.
All other steps in the workflow SHALL continue using `GITHUB_TOKEN`.

#### Scenario: Non-tag steps use default token
- **WHEN** a caller provides a `tag_push_token` secret
- **THEN** steps that reference `GH_TOKEN` (e.g., "Verify CI checks passed on HEAD") continue using `GITHUB_TOKEN`
- **AND** steps that do not reference `GH_TOKEN` (e.g., "Check tag uniqueness") remain unaffected
- **AND** only the "Create and push tag" step uses the provided token
- **AND** no other step references `secrets.tag_push_token`

---

### Requirement: Recursive triggering warning in secret description
The `tag_push_token` secret declaration SHALL include a description warning
callers that downstream workflows must not re-trigger the preflight workflow with
an elevated token, to avoid infinite workflow loops.

#### Scenario: Secret description contains warning
- **WHEN** the workflow file's `secrets.tag_push_token.description` is read
- **THEN** it contains the following text: "Optional elevated token for tag creation. When provided, the tag event can trigger downstream workflows. WARNING: Do not use an elevated token in downstream workflows that re-invoke this preflight workflow, or you will create a recursive loop."
