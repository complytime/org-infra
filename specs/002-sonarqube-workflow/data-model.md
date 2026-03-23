# Data Model: Reusable SonarCloud Analysis Workflow

## Workflow Inputs

The reusable workflow accepts the following input parameters:

### Required Inputs

| Input | Type | Description |
|-------|------|-------------|
| `sonar_organization` | `string` | The SonarCloud organization key (e.g., `rh-psce`). Must match the organization configured in SonarCloud. |
| `sonar_project_key` | `string` | The SonarCloud project key (e.g., `rh-psce_complyctl`). Format is typically `organization_repository`. |

### Optional Inputs - Coverage Configuration

| Input | Type | Default | Description |
|-------|------|---------|-------------|
| `coverage_artifact_name` | `string` | `coverage` | Name of the coverage artifact uploaded by the previous job. Used to download the coverage file. |
| `coverage_file_path` | `string` | — | Path to the coverage file within the artifact (e.g., `coverage.out`, `coverage.xml`). When empty, no coverage data is provided to SonarCloud. |
| `language_scanner_property` | `string` | — | SonarCloud scanner property for coverage reports. Language-specific values:<br>• Go: `sonar.go.coverage.reportPaths`<br>• Python: `sonar.python.coverage.reportPaths` |

## Secrets

The workflow requires two secrets:

| Secret | Required | Description |
|--------|----------|-------------|
| `SONAR_TOKEN` | Yes | SonarCloud analysis token with permissions to publish analysis results for the specified project. Generated in SonarCloud under account security settings. |
| `source_token` | Yes | GitHub token with permissions to read repository contents. Typically `secrets.GITHUB_TOKEN` from the calling workflow. Used for SonarCloud GitHub integration. |

## Workflow Permissions

The workflow declares minimal permissions following the principle of least privilege:

### Top-level Permissions (Default)
```yaml
permissions:
  contents: none
  issues: none
  pull-requests: none
```

### Job-level Permissions (sonar_analysis job)
```yaml
permissions:
  contents: read        # Required to checkout repository code
```

## SonarCloud Scanner Configuration

The workflow dynamically constructs SonarCloud scanner arguments:

### Base Arguments (Always Provided)

```
-Dsonar.organization=<sonar_organization>
-Dsonar.projectKey=<sonar_project_key>
-Dsonar.qualitygate.wait=true
```

### Conditional Arguments

**Coverage Reporting** (when `coverage_file_path` is provided):
```
-D<language_scanner_property>=<coverage_file_path>
```

## Data Flow

1. Consumer workflow triggers on push to main branch
2. (Optional) Coverage generation job runs tests and uploads coverage artifact
3. Reusable workflow is called with organization and project key
4. Workflow checks out repository at current commit
5. (Optional) Downloads coverage artifact from previous job if coverage inputs are provided
6. Runs SonarCloud scanner with configured parameters (including coverage if provided)
7. SonarCloud analyzes code and evaluates quality gate
8. Workflow fails if quality gate does not pass

## Coverage Artifact Structure

When using coverage reports, a previous job in the workflow generates and uploads the coverage file as an artifact. The SonarCloud workflow then downloads this artifact.

**Example artifact structure:**
```
coverage/              # Artifact name (coverage_artifact_name)
  └── coverage.out     # Coverage file (coverage_file_path)
```

**For Go:**
- Artifact name: `coverage`
- Coverage file: `coverage.out`

**For Python:**
- Artifact name: `coverage`
- Coverage file: `coverage.xml`

The `coverage_file_path` input should match the path within the uploaded artifact where the coverage file is located.

## Environment Variables

The workflow uses environment variables to pass configuration to steps:

| Variable | Source | Usage |
|----------|--------|-------|
| `GITHUB_TOKEN` | `secrets.source_token` | SonarCloud scanner GitHub integration |
| `SONAR_TOKEN` | `secrets.SONAR_TOKEN` | SonarCloud authentication |
| `SONAR_ORGANIZATION` | `inputs.sonar_organization` | Scanner configuration |
| `SONAR_PROJECT_KEY` | `inputs.sonar_project_key` | Scanner configuration |
| `COVERAGE_ARTIFACT_NAME` | `inputs.coverage_artifact_name` | Artifact download step |
| `COVERAGE_FILE_PATH` | `inputs.coverage_file_path` | Conditional scanner argument |
| `LANGUAGE_SCANNER_PROPERTY` | `inputs.language_scanner_property` | Conditional scanner argument |

## Output Data

The workflow produces analysis results that are published to SonarCloud but does not expose outputs to calling workflows. Results can be accessed:

1. **SonarCloud Dashboard**: View detailed metrics at `https://sonarcloud.io/project/overview?id=<project_key>`
2. **Quality Gate Status**: Reflected in the workflow job status (pass/fail)

## Action Dependencies

The workflow uses the following pinned GitHub actions:

| Action | Purpose |
|--------|---------|
| `actions/checkout` | Repository code checkout |
| `actions/download-artifact` | Download coverage artifacts (current run) |
| `SonarSource/sonarqube-scan-action` | Execute SonarCloud analysis |

All actions are pinned to specific commit SHAs for supply chain security.
