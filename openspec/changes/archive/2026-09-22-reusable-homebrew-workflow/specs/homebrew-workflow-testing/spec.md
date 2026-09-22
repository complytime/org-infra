## ADDED Requirements

### Requirement: Self-test workflow for Homebrew reusable workflow
A CI test workflow SHALL validate the reusable Homebrew workflow on PRs that
modify Homebrew-related workflow files.

#### Scenario: PR triggers test on workflow changes
- **WHEN** a PR modifies files matching `.github/workflows/*homebrew*`
- **THEN** the CI test workflow runs to validate the reusable workflow

#### Scenario: Formula generation validation
- **WHEN** the test workflow runs
- **THEN** it invokes the reusable workflow with test inputs and verifies that a valid formula file is produced

### Requirement: macOS runner for platform validation
The CI test workflow SHALL run on a macOS runner to validate Homebrew formula
compatibility on the primary target platform.

#### Scenario: macOS brew audit
- **WHEN** the test workflow generates a formula on macOS
- **THEN** `brew audit --strict` runs natively on the macOS Homebrew installation
