## ADDED Requirements

### Requirement: Reusable council review workflow

A reusable GitHub Actions workflow (`reusable_council_review.yml`) SHALL run an
automated AI review council on pull requests. The workflow SHALL read committed
Divisor agent files as prompt context, authenticate to an AI API using credentials
stored in GitHub Secrets, and invoke 5 review personas in parallel. The specific
AI provider (e.g., Vertex AI, Anthropic) is determined during the AI integration
phase; the workflow design SHALL be provider-agnostic.

#### Scenario: Workflow invoked by consumer workflow

- **WHEN** a consumer workflow calls `reusable_council_review.yml`
- **THEN** the workflow accepts inputs for AI API configuration (endpoint, model)
  and secrets for API credentials

#### Scenario: Gate check skips dependabot PRs

- **WHEN** a pull request is authored by dependabot
- **THEN** the council review is skipped and no comment is posted

#### Scenario: Gate check skips draft PRs

- **WHEN** a pull request is in draft state
- **THEN** the council review is skipped and no comment is posted

#### Scenario: Gate check skips binary-only changes

- **WHEN** a pull request contains only binary files, lock files, or generated files
- **THEN** the council review is skipped and no comment is posted

#### Scenario: Fork PRs skip review due to missing secrets

- **WHEN** a pull request is opened from a fork by a non-organization contributor
- **THEN** the council review is skipped because the `pull_request` event does not
  expose repository or organization secrets to fork workflows

### Requirement: Spec vs code review auto-detection

The workflow SHALL automatically detect whether a pull request requires spec review
or code review based on the files changed in the PR.

#### Scenario: Spec-only PR triggers spec review

- **WHEN** a pull request changes only files in `specs/`, `openspec/`, or
  `.specify/` directories
- **THEN** the workflow runs in Spec Review mode and each persona uses its spec
  review checklist

#### Scenario: Code PR triggers code review

- **WHEN** a pull request changes any source code, workflow, or configuration files
- **THEN** the workflow runs in Code Review mode and each persona uses its code
  review checklist

#### Scenario: Mixed PR defaults to code review

- **WHEN** a pull request changes both spec files and code files
- **THEN** the workflow runs in Code Review mode (the Guard persona checks spec
  alignment as part of its code review checklist)

### Requirement: Governance context collection

The workflow SHALL read governance context files from the repository and embed their
content in the prompts sent to each persona.

#### Scenario: Constitution loaded

- **WHEN** the workflow prepares prompts for review
- **THEN** it reads `.specify/memory/constitution.md` and includes its content as
  governance context

#### Scenario: Convention packs loaded

- **WHEN** the workflow prepares prompts for review
- **THEN** it reads all files matching `.opencode/uf/packs/*.md` and includes their
  content as convention context

#### Scenario: AGENTS.md loaded

- **WHEN** the workflow prepares prompts for review
- **THEN** it reads `AGENTS.md` and includes relevant project context

#### Scenario: Spec files loaded for spec review

- **WHEN** the workflow runs in Spec Review mode
- **THEN** it reads the relevant spec files from `specs/` or `openspec/` and
  includes them as review context

### Requirement: Five Divisor personas run in parallel

The workflow SHALL invoke 5 review personas (Guard, Architect, Adversary, Tester,
SRE) as parallel API calls to the configured AI API. Each persona SHALL use its
committed agent file (`.opencode/agents/divisor-*.md`) as the prompt definition.

#### Scenario: All 5 personas invoked

- **WHEN** the workflow runs a review
- **THEN** it makes 5 parallel API calls to the configured AI API, one per persona:
  Guard, Architect, Adversary, Tester, SRE

#### Scenario: Each persona uses its agent file

- **WHEN** the workflow constructs a prompt for a persona
- **THEN** it reads the corresponding `.opencode/agents/divisor-<persona>.md` file
  and uses the role definition, review checklist, and output format from that file

#### Scenario: Each persona receives the PR diff

- **WHEN** the workflow constructs a prompt for a persona
- **THEN** it includes the scoped PR diff (excluding binary files and lock files)
  as review input

#### Scenario: Each persona returns a structured verdict

- **WHEN** a persona completes its review
- **THEN** it returns either APPROVE or REQUEST CHANGES with structured findings
  that include severity level, file reference, constraint or convention reference,
  description, and recommendation

### Requirement: Structured PR comment posted

The workflow SHALL post a single structured PR comment with all persona findings.
The comment SHALL be updated on each push rather than creating new comments.

#### Scenario: Comment created on first review

- **WHEN** the council review runs for the first time on a PR
- **THEN** a structured comment is created showing review mode, persona verdicts,
  and detailed findings

#### Scenario: Comment updated on subsequent pushes

- **WHEN** a new push is made to a PR that already has a council review comment
- **THEN** the existing comment is replaced with fresh findings from the new review

#### Scenario: Comment shows overall verdict

- **WHEN** the council review completes
- **THEN** the comment shows an overall council verdict (APPROVE if all personas
  approve, REQUEST CHANGES if any persona requests changes) with a finding count
  summary per persona

#### Scenario: Comment includes disclaimer

- **WHEN** the council review comment is posted
- **THEN** the comment includes a disclaimer stating that findings assist human
  reviewers and do not replace human judgment

### Requirement: Graceful failure when Divisor files are missing

The workflow SHALL handle the case where Divisor agent files are not present in the
repository by skipping the review and posting an informational comment.

#### Scenario: Divisor files not found

- **WHEN** the workflow runs in a repository that has not completed `uf init` setup
- **THEN** the workflow skips the review and posts a comment indicating that council
  review requires Divisor agent setup

#### Scenario: Partial Divisor files present

- **WHEN** some but not all 5 Divisor agent files are present
- **THEN** the workflow runs only the personas whose agent files exist and notes
  which personas were skipped

### Requirement: AI API authentication via GitHub Secrets

The workflow SHALL authenticate to the configured AI API using credentials stored
in GitHub Secrets at the organization level. The authentication method (API key,
WIF token, etc.) SHALL be determined by the chosen AI provider during the AI
integration phase.

#### Scenario: API credentials available

- **WHEN** the workflow runs and AI API credentials are configured in GitHub Secrets
- **THEN** it authenticates and makes API calls to the configured AI endpoint

#### Scenario: API credentials missing

- **WHEN** the workflow runs and AI API credentials are not configured
- **THEN** the workflow fails gracefully with a clear error message indicating
  that AI API setup is required

#### Scenario: Fork PR has no access to secrets

- **WHEN** the workflow is triggered by a `pull_request` event from a fork
- **THEN** secrets are not available (GitHub built-in security) and the workflow
  skips the review gracefully

### Requirement: Consumer council review workflow

A consumer workflow (`ci_council_review.yml`) SHALL be created and synced to all
repositories. It SHALL call `reusable_council_review.yml` with the appropriate
secrets and permissions.

#### Scenario: Consumer workflow triggers on PR events

- **WHEN** a pull request is opened or updated against the main branch
- **THEN** the consumer workflow triggers and calls the reusable council review
  workflow

#### Scenario: Consumer workflow passes required secrets

- **WHEN** the consumer workflow calls the reusable workflow
- **THEN** it passes AI API credential secrets from the organization's GitHub
  Secrets store

#### Scenario: Consumer workflow has minimal permissions

- **WHEN** the consumer workflow runs
- **THEN** it has only `contents: read` and `pull-requests: write` permissions
  at the job level
