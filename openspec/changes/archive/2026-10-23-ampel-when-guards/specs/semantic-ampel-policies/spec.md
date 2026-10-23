# Spec Delta

## ADDED Requirements

### Requirement: Policies declare when guards for multi-predicate bundles
Each granular ampel policy file SHALL include a `when` field that gates evaluation based on the availability of matching predicate types in loaded attestations.

#### Scenario: Policy skips when no matching predicate type is present
- **WHEN** a policy is evaluated against an attestation bundle containing no predicates matching the policy's declared predicate types
- **THEN** the policy produces a `SKIP` result instead of `FAIL`

#### Scenario: Policy evaluates normally when matching predicate type is present
- **WHEN** a policy is evaluated against an attestation bundle containing at least one predicate matching the policy's declared predicate types
- **THEN** the policy evaluates its tenets and produces `PASS` or `FAIL` as before

#### Scenario: When expression references correct predicate types
- **WHEN** a policy file's `when.expression` is inspected
- **THEN** it references every predicate type URL declared in the policy's `tenets[].predicates.types` arrays

### Requirement: When guard placement is consistent
The `when` field SHALL appear after the `id` field and before the `meta` field in each policy JSON file.

#### Scenario: Field ordering in policy files
- **WHEN** any granular policy JSON file is inspected
- **THEN** the top-level keys appear in order: `id`, `when`, `meta`, `tenets`

### Requirement: Lint check validates when guard completeness
A lint target SHALL verify that every policy file's `when` expression references all predicate type URLs from its tenets, and SHALL fail if any are missing.

#### Scenario: Lint passes for correctly guarded policy
- **WHEN** a policy file's `when.expression` contains all predicate type URLs from its `tenets[].predicates.types`
- **THEN** the lint check passes for that file

#### Scenario: Lint fails for incomplete when guard
- **WHEN** a policy file's `when.expression` is missing a predicate type URL that appears in its `tenets[].predicates.types`
- **THEN** the lint check fails with a non-zero exit code and names the missing predicate type

#### Scenario: Lint skips files without when field
- **WHEN** a policy file does not contain a `when` field
- **THEN** the lint check skips that file without error
