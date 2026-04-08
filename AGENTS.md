# org-infra

CI/CD infrastructure hub for ComplyTime. Syncs reusable workflows, lint configs, templates, and AI tooling to all org repositories via `sync-config.yml`.

## Structure

```text
.github/workflows/      # Reusable (reusable_*) and consumer (ci_*) workflows
scripts/                 # sync-org-repositories.py (Python, GitPython + PyYAML + requests)
tests/                   # pytest unit tests for sync script
compliance/              # Ampel policy definitions (branch protection rules)
specs/                   # Feature specifications (managed by OpenSpec/SpecKit)
ai/                      # AI tooling documentation and skills directory
.opencode/command/       # Project-specific AI commands (review_pr.md)
sync-config.yml          # Defines which files sync to org repos — check before modifying any config
.specify/memory/constitution.md  # All coding standards and governance (single source of truth)
Makefile                 # Build/test/lint automation
```

## Commands

```bash
make lint            # yamllint + ruff (all linters)
make test            # pytest -v
make sync-dry-run    # Preview file sync to org repos
make clean           # Remove __pycache__ and .pyc
```

## Constraints

- **Sync impact**: Config files (`.golangci.yml`, `.yamllint.yml`, `ruff.toml`, `.mega-linter.yml`, `commitlint.config.js`) and workflows (`ci_*`, `reusable_*`) sync to all org repos. Check `sync-config.yml` before modifying to understand downstream impact.
- **Workflow naming**: Reusable workflows MUST use `reusable_` prefix, consumer workflows `ci_` prefix.
- **Python**: Lint with `ruff` (`ruff.toml`). No `go.mod` — this repo is Python + YAML, not Go (Go configs are sync templates for other repos).
- **YAML**: Lint with `yamllint` (`.yamllint.yml`). Line length follows yamllint config, not the 99-char code rule.
- **Standards**: All coding standards are in `.specify/memory/constitution.md`. Do not duplicate them.
- **AI tooling**: Setup, commands, and skill creation documented in `ai/README.md`.

## Commits

All commits MUST use Conventional Commits, the `-s` flag (Signed-off-by), and include an `Assisted-by` trailer:

```bash
git commit -s -m "feat: add feature X

Description of changes.

Assisted-by: OpenCode (model-name)"
```

Replace `model-name` with the actual model identifier (e.g., `claude-opus-4-6`).

<!-- MANUAL ADDITIONS START -->
<!-- MANUAL ADDITIONS END -->
