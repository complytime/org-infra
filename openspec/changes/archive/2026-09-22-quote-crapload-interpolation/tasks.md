## 1. Fix Unquoted Interpolation

- [x] 1.1 Add double quotes around `${{ inputs.new-function-threshold }}` on line 154 of `.github/workflows/reusable_crapload_analysis.yml`

## 2. Validation

> **Test strategy**: YAML workflow files have no unit test framework. Coverage for this change relies on `yamllint` (syntax validation), `grep`-based verification (quoting consistency), and code review. Regression protection depends on review conventions.

- [x] 2.1 Run `yamllint` on `.github/workflows/reusable_crapload_analysis.yml` to confirm valid YAML
- [x] 2.2 Verify all 3 `${{ inputs.* }}` shell variable assignments (`BASELINE`, `NEW_FUNC_THRESHOLD`, `EPSILON`) in `.github/workflows/reusable_crapload_analysis.yml` use double-quoted interpolation
