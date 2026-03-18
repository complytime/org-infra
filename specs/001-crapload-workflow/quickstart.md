# Quickstart: CRAP Load Analysis

## For Repository Maintainers (Adopting the Workflow)

### 1. Add the consumer workflow

Create `.github/workflows/ci_crapload.yml` in your repository:

```yaml
# SPDX-License-Identifier: Apache-2.0

name: CRAP Load Check

on:
  pull_request:
    branches:
      - main

permissions:
  contents: read
  pull-requests: write

jobs:
  crapload:
    name: CRAP Load Analysis
    uses: complytime/org-infra/.github/workflows/reusable_crapload_analysis.yml@main
    permissions:
      contents: read
      pull-requests: write
```

### 2. (Optional) Commit a baseline file

To enable regression detection, commit a baseline at `.gaze/baseline.json`. This file contains per-function CRAP scores from a known-good state. Without it, the workflow still runs but skips per-function comparison.

### 3. Open a pull request

The workflow runs automatically on PRs targeting `main` that modify Go files. Results appear as a PR comment with a summary table.

## Customizing Inputs

Override defaults by passing `with:` in the consumer workflow:

```yaml
jobs:
  crapload:
    uses: complytime/org-infra/.github/workflows/reusable_crapload_analysis.yml@main
    with:
      new-function-threshold: 20    # Stricter threshold
      packages: './cmd/... ./pkg/...'  # Specific packages only
      post-comment: false            # Disable PR comments
```

## For org-infra Contributors

The reusable workflow lives at `.github/workflows/reusable_crapload_analysis.yml`. Changes here affect all consuming repositories. Follow the constitution's Amendment Procedure for workflow modifications.

The consumer template at `.github/workflows/ci_crapload.yml` is distributed to Go repositories via the sync mechanism defined in `sync-config.yml`.
