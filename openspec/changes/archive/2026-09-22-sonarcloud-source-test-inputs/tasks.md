## 1. Workflow Changes

- [x] 1.1 Add `sonar_sources` and `sonar_tests` inputs to the `workflow_call` section of
  `.github/workflows/reusable_sonarqube.yml` (optional string inputs, empty default,
  descriptive `description` fields)
- [x] 1.2 Add `SONAR_SOURCES` and `SONAR_TESTS` environment variables to the `SonarCloud Scan`
  step's `env:` block, mapped from the new inputs
- [x] 1.3 Fix line 87: remove outer double quotes from the conditional coverage `-D` flag
- [x] 1.4 Append two conditional `-D` flags for `sonar.sources` and `sonar.tests` to the
  `args` block, using the unquoted pattern and `env:` indirection

## 2. Documentation Updates

- [x] 2.1 [P] Update `specs/002-sonarqube-workflow/quickstart.md`: add a usage example
  showing `sonar_sources` and `sonar_tests` inputs (Python example with
  `sonar_sources: complyscribe/` and `sonar_tests: tests/`); add the new inputs to the
  Configuration Options section
- [x] 2.2 [P] Update `specs/002-sonarqube-workflow/spec.md`: add source/test path
  configuration to functional requirements; note `sonar-project.properties` as an
  alternative in scope boundaries

## 3. Validation

- [x] 3.1 Run `make lint` and fix any issues in modified files
- [x] 3.2 Run `make test` to verify no regressions
