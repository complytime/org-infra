## 1. Pin Consumer Workflows

- [x] 1.1 Update `.github/workflows/ci_checks.yml`: replace `reusable_ci.yml@main` with `reusable_ci.yml@baf5b2e21e61581b4a3a129795286e8592e6afbb # v0.1.0`
- [x] 1.2 Update `.github/workflows/ci_compliance.yml`: replace `reusable_compliance.yml@main` with `reusable_compliance.yml@baf5b2e21e61581b4a3a129795286e8592e6afbb # v0.1.0`
- [x] 1.3 Update `.github/workflows/ci_crapload.yml`: replace `reusable_crapload_analysis.yml@main` with `reusable_crapload_analysis.yml@baf5b2e21e61581b4a3a129795286e8592e6afbb # v0.1.0`
- [x] 1.4 Update `.github/workflows/ci_dependencies.yml`: replace `reusable_deps_reviewer.yml@main` with `reusable_deps_reviewer.yml@baf5b2e21e61581b4a3a129795286e8592e6afbb # v0.1.0`
- [x] 1.5 Update `.github/workflows/ci_dependencies.yml`: replace `reusable_dependabot_reviewer.yml@main` with `reusable_dependabot_reviewer.yml@baf5b2e21e61581b4a3a129795286e8592e6afbb # v0.1.0`
- [x] 1.6 Update `.github/workflows/ci_scheduled.yml`: replace `reusable_scheduled.yml@main` with `reusable_scheduled.yml@baf5b2e21e61581b4a3a129795286e8592e6afbb # v0.1.0`
- [x] 1.7 Update `.github/workflows/ci_security.yml`: replace `reusable_vuln_scan.yml@main` with `reusable_vuln_scan.yml@baf5b2e21e61581b4a3a129795286e8592e6afbb # v0.1.0`
- [x] 1.8 Update `.github/workflows/ci_security.yml`: replace `reusable_security.yml@main` with `reusable_security.yml@baf5b2e21e61581b4a3a129795286e8592e6afbb # v0.1.0`

## 2. Pin Reusable-to-Reusable Reference

- [x] 2.1 Update `.github/workflows/reusable_scheduled.yml`: replace `reusable_security.yml@main` with `reusable_security.yml@baf5b2e21e61581b4a3a129795286e8592e6afbb # v0.1.0`

## 3. Validation

- [x] 3.1 Run `yamllint` on all modified workflow files to verify YAML validity
- [x] 3.2 Verify zero `@main` references remain for `complytime/org-infra` reusable workflows across all `.github/workflows/*.yml` files
- [x] 3.3 Verify all 9 references use the full SHA `baf5b2e21e61581b4a3a129795286e8592e6afbb` with `# v0.1.0` comment
