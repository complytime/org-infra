## Context

ComplyTime ships Go CLI binaries (complyctl, complypack) that users install via
Homebrew on macOS and Linux. The `complytime/homebrew-tap` repository hosts
Homebrew formulae. Currently, complyctl PR #742 inlines the Homebrew publishing
step in its release workflow using heredoc + `sed` templating. Complypack has no
Homebrew setup at all.

org-infra already centralises release workflows with `reusable_release_preflight.yml`
(tag validation) and `reusable_release_goreleaser.yml` (binary build + sign). Adding
`reusable_release_homebrew.yml` completes the release chain: preflight -> goreleaser
-> homebrew.

**Constraints:**
- Must run on `ubuntu-latest` (formula generation + tap push are not macOS-specific)
- Cross-repo push to `complytime/homebrew-tap` requires scoped GitHub App token
- Formula must be source-build (depends_on "go" => :build), not pre-built bottles
- Must follow all org-infra workflow conventions (permissions, SHA pinning, env vars)

## Goals / Non-Goals

**Goals:**
- Single reusable workflow for Homebrew formula publishing across all Go CLI repos
- Standardised GitHub App authentication for cross-repo tap access
- Quality gate via `brew audit --strict` before pushing to the tap
- Parameterised formula generation from workflow inputs (no sed placeholder templating)
- Idempotent re-runs (no-op if formula content unchanged)

**Non-Goals:**
- Pre-built bottle support (binary distribution via Homebrew bottles)
- Cask formulae (GUI app installers)
- Non-Go projects (formula template assumes Go source build)
- Syncing a caller workflow to downstream repos (release workflows are repo-specific)

## Decisions

### D1: Formula generation via shell heredoc with variable interpolation

**Decision:** Generate the formula using a bash heredoc with direct shell variable
interpolation (`${VERSION}`, `${SHA256}`, etc.) rather than sed placeholder
replacement.

**Alternative considered:** Heredoc + `sed` placeholder replacement (as in complyctl
PR #742). Rejected because sed introduces fragility (delimiter collisions, ordering
sensitivity) and is harder to read. Direct variable interpolation in a heredoc is
simpler and achieves the same result safely when inputs are validated.

**Alternative considered:** Template file checked into the repository. Rejected because
it would need to be synced, adding a non-workflow file to the sync config. The formula
template is small enough to inline in the workflow.

### D2: Run on ubuntu-latest, not macOS

**Decision:** The reusable workflow runs on `ubuntu-latest`.

**Alternative considered:** macOS runner for native `brew audit` support. Rejected
because `brew audit --strict` works on Linux via Homebrew-on-Linux (linuxbrew), and
macOS runners are significantly more expensive (10x cost). The CI test workflow
(`ci_test_homebrew.yml`) can optionally use macOS for deeper platform validation.

### D3: GitHub App token via actions/create-github-app-token

**Decision:** Use `actions/create-github-app-token` with `client-id` and
`private-key` secrets, scoped to `repositories: homebrew-tap` with
`permission-contents: write`.

**Alternative considered:** PAT (Personal Access Token). Rejected because PATs are
tied to individual accounts, cannot be scoped to a single repository, and expire
requiring manual rotation.

**Alternative considered:** Deploy keys. Rejected because deploy keys are per-repo
SSH keys that cannot be scoped to specific permissions and are harder to audit.

### D4: Workflow inputs cover all formula-variable parts

**Decision:** The reusable workflow accepts inputs for all parts that vary between
projects: `tag`, `project_name`, `description`, `binary_name`, `tap_repo`,
`go_main_path`, `ldflags_module`, and `homepage`. The formula class name is
derived from `project_name` via shell transformation.

**Alternative considered:** Fewer inputs with convention-based defaults. Rejected
because conventions vary between repos (e.g., complyctl builds from `./cmd/complyctl`
while complypack uses `./cmd/complypack`). Explicit inputs are clearer and prevent
silent misconfiguration.

### D5: brew audit --strict as a quality gate

**Decision:** Run `brew audit --strict --formula` on the generated formula before
pushing to the tap. Fail the workflow if audit fails.

**Alternative considered:** Skip audit and rely on manual review. Rejected because
automated quality gates catch formula syntax errors, missing fields, and style
violations before they reach the tap.

### D6: Secrets passed by caller, not hardcoded names

**Decision:** The reusable workflow declares `secrets:` for `app_client_id` and
`app_private_key`. Callers pass their own secret names.

**Alternative considered:** Hardcode secret names like
`APP_ID_HOMEBREW_FORMULA_PUBLISHER`. Rejected because different orgs or forks
may use different secret names. The reusable pattern in org-infra always lets
callers map their secrets.

## Risks / Trade-offs

- **[Risk] brew audit may differ between Homebrew versions on Linux vs macOS** ->
  Mitigation: Pin Homebrew installation step; the CI test workflow runs on macOS
  for cross-platform validation.

- **[Risk] Source tarball may not be immediately available after tag creation** ->
  Mitigation: Retry logic with exponential backoff on tarball download (curl --retry).
  Callers should chain this after the release job which creates the GitHub Release
  (and thus the tarball).

- **[Risk] GitHub App token scope creep** ->
  Mitigation: Token is scoped to a single repository (`homebrew-tap`) with only
  `contents:write`. The `# zizmor: ignore[github-app]` annotation documents the
  intentional cross-org scope.

- **[Trade-off] ubuntu-latest means brew audit may miss macOS-specific issues** ->
  Acceptable because the formula uses `depends_on "go" => :build` which is
  platform-agnostic. The CI test workflow provides macOS coverage for deeper
  validation.

## Open Questions

- Should the workflow support custom `test do` blocks in the formula, or is
  `assert_match version.to_s` sufficient for all CLI tools? (Current decision:
  start with the version assertion pattern; add input for custom test block
  if needed later.)
