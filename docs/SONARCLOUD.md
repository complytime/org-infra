# SonarCloud Setup

How SonarCloud is configured in the ComplyTime organization, how to
onboard new repositories, and how it relates to other quality checks.

## Organization

The SonarCloud organization `complytime` is **bound** to the
`complytime` GitHub organization. This binding provides:

- Automatic import of new GitHub repositories into SonarCloud.
- Automatic PR decoration on bound projects.
- GitHub member synchronization.
- Privacy settings inherited from GitHub (public/private).

Dashboard: <https://sonarcloud.io/organizations/complytime/projects>

## Analysis Methods

SonarCloud supports two analysis methods. They **cannot** coexist on
the same project — enabling both causes CI failures.

### Automatic Analysis

SonarCloud reads the repository directly and analyzes on every push
to `main` and on pull requests. No CI workflow, token, or
configuration is required.

Limitations:

- No code coverage support.
- No branch analysis beyond `main` and PRs.
- No monorepo support.
- No analysis logs.

**This is the default for all imported repositories.** Repos that do
not need coverage data in SonarCloud require no setup at all.

### CI-Based Analysis

A GitHub Actions workflow runs the SonarCloud scanner with explicit
configuration. This is required when coverage data must be uploaded
to SonarCloud.

The reusable workflow lives in this repository:

```text
.github/workflows/reusable_sonarqube.yml
```

Consumer repos call it from their own `ci_sonarcloud.yml`. See
[complyctl's consumer workflow](https://github.com/complytime/complyctl/blob/main/.github/workflows/ci_sonarcloud.yml)
for a reference implementation.

## Onboarding a New Repository

### Automatic Analysis (no coverage)

Nothing to do. When the repository is created in the `complytime`
GitHub org, SonarCloud auto-imports it and begins automatic analysis.

Verify the project appears at the
[organization dashboard](https://sonarcloud.io/organizations/complytime/projects).

### CI-Based Analysis (with coverage)

Follow these steps when the repository needs coverage data in
SonarCloud (e.g., Go projects that generate `coverage.out`).

#### 1. Disable automatic analysis

In SonarCloud, go to the project:
**Administration > Analysis Method > toggle Automatic Analysis OFF**.

#### 2. Set GitHub variables and secrets

| Setting | Level | Value |
|---|---|---|
| `vars.SONAR_ORGANIZATION` | Org or repo | `complytime` |
| `vars.SONAR_PROJECT_KEY` | Repo | `complytime_<repo-name>` |
| `secrets.SONAR_TOKEN` | Org or repo | SonarCloud analysis token |

If `SONAR_ORGANIZATION` and `SONAR_TOKEN` are configured at the
GitHub **org level**, only a per-repo `SONAR_PROJECT_KEY` variable is
needed.

#### 3. Add the consumer workflow

Create `.github/workflows/ci_sonarcloud.yml` in the repository.

#### 4. Add `sonar-project.properties`

Create `sonar-project.properties` in the repository root. This file
is used for local developer scans; CI overrides these values via
`-D` flags.

```properties
sonar.projectKey=complytime_<repo-name>
sonar.organization=complytime
sonar.projectName=<repo-name>
sonar.exclusions=vendor/**
```

Adjust `sonar.exclusions` and language-specific sensor settings as
needed.

## Reusable Workflow Inputs

The `reusable_sonarqube.yml` workflow accepts the following inputs:

| Input | Required | Default | Description |
|---|---|---|---|
| `sonar_organization` | Yes | — | SonarCloud organization key |
| `sonar_project_key` | Yes | — | SonarCloud project key |
| `coverage_artifact_name` | No | `coverage` | Name of the uploaded coverage artifact |
| `coverage_file_path` | No | — | Path to coverage file; skip if empty |
| `language_scanner_property` | No | — | Scanner property for coverage (e.g., `sonar.go.coverage.reportPaths`) |
| `sonar_sources` | No | `""` | Comma-separated source directories |
| `sonar_tests` | No | `""` | Comma-separated test directories |

Secrets:

| Secret | Required | Description |
|---|---|---|
| `SONAR_TOKEN` | Yes | SonarCloud analysis token |
| `source_token` | Yes | GitHub token (usually `secrets.GITHUB_TOKEN`) |

## Relationship with CRAP Load

Some repositories run both SonarCloud and CRAP Load checks. These are
**independent, complementary** quality gates.

| Aspect | SonarCloud | CRAP Load |
|---|---|---|
| Scope | Project-wide code quality | Per-function complexity risk |
| Metrics | Bugs, smells, vulnerabilities, coverage % | CRAP score, GazeCRAP score |
| Baseline | SonarCloud quality gate | Committed `.gaze/baseline.json` |
| Coverage source | `coverage.out` via CI artifact | `coverage.out` generated in-workflow |
| Workflow | `ci_sonarcloud.yml` → `reusable_sonarqube.yml` | `ci_crapload.yml` → `reusable_crapload_analysis.yml` |
| Runs on | Push to `main` | Pull requests |

Both consume Go test coverage data but generate and process it
independently. They do not share artifacts or interfere with each
other. A repository can use either, both, or neither.

## Links

| Resource | URL |
|---|---|
| SonarCloud dashboard | <https://sonarcloud.io/organizations/complytime/projects> |
| Reusable workflow source | [reusable_sonarqube.yml](../.github/workflows/reusable_sonarqube.yml) |
| Consumer workflow reference | [complyctl ci_sonarcloud.yml](https://github.com/complytime/complyctl/blob/main/.github/workflows/ci_sonarcloud.yml) |
| CRAP Load reusable workflow | [reusable_crapload_analysis.yml](../.github/workflows/reusable_crapload_analysis.yml) |
| SonarCloud documentation | <https://docs.sonarsource.com/sonarqube-cloud/> |
| Migration tracking issue | [complyctl#916](https://github.com/complytime/complyctl/issues/916) |
