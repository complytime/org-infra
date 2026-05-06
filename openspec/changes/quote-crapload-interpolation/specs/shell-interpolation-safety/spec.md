## ADDED Requirements

### Requirement: Input interpolations in shell assignments are quoted

All `${{ inputs.* }}` expressions assigned to shell variables in `reusable_crapload_analysis.yml` `run:` blocks SHALL be wrapped in double quotes to prevent word splitting and globbing.

> **Note**: This requirement addresses the known violation in `reusable_crapload_analysis.yml`. The same quoting convention SHOULD be followed across all reusable workflows. For new workflows, the preferred pattern is `env:` block indirection (per the `release-workflow` spec) rather than inline `${{ }}` interpolation.

#### Scenario: Numeric input assigned to shell variable

- **GIVEN** a reusable workflow with a `run:` block that assigns `workflow_call` inputs to shell variables
- **WHEN** a `workflow_call` input of type `number` is assigned to a shell variable
- **THEN** the assignment SHALL use double quotes around the interpolation (e.g., `VAR="${{ inputs.name }}"`)

#### Scenario: Consistency across adjacent assignments

- **GIVEN** a `run:` block containing multiple input-derived variable assignments
- **WHEN** multiple input-derived variables are assigned in the same `run:` block
- **THEN** all assignments SHALL follow the same quoting pattern
