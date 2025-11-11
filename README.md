# ⚙️ CI/CD Reusable Workflows

This repository centrally manages configuration files, templates, and standardized CI/CD workflows for the organization.
Its purpose is to ensure **security, consistency, and reusability** across all repositories by defining common settings and automation processes once.

---

## 🎯 Purpose

The primary goal is to provide **pre-vetted, security-hardened pipeline steps** for common tasks, such as environment deployment, lint checks, dependency review, vulnerability scans, tests coverage, and more.

Specifically, this repository includes:

* [Reusable Workflows](https://docs.github.com/en/actions/how-tos/reuse-automations/reuse-workflows) for common tasks
* Templates to consume reusable workflows in org repositories
* Templates for PRs and Issues creation
* Configuration files for lint checks
* Synchronization script integrated with [peribolos](https://github.com/complytime/.github/blob/main/peribolos.yaml) to periodically check consistence among repositories

---

## 📁 Directory Structure

```bash
org-infra/
├── .github/
│  ├── ISSUE_TEMPLATE/
│  │  ├── bug_report.md                     # Issue template to report a Bug.
│  │  └── feature_request.md                # Issue template to request a Feature.
│  ├── workflows/
│  │  ├── ci_checks.yml                     # Workflow to consume `reusable_ci`. 
│  │  ├── ci_dependencies.yml               # Workflow to consume `reusable_dependabot_reviewer` and `reusable_deps_reviewer`
│  │  │                                     # plus local jobs to auto-approve and comment on dependabot PRs.
│  │  ├── ci_scheduled.yml                  # Workflow to consume `reusable_scheduled`.
│  │  ├── ci_vulns.yml                      # Workflow to consume `reusable_vuln_scan`.
│  │  ├── reusable_ci.yml                   # Generic CI checks, such as linters, typos and PR titles.
│  │  ├── reusable_dependabot_reviewer.yml  # Specific for dependabot PRs. Classify risk and checks dependency adoption.
│  │  ├── reusable_deps_reviewer.yml        # Check for vulnerabilities, license issues, and OpenSSF Scorecard Level.
│  │  ├── reusable_scheduled.yml            # Scheduled vulnerability scan. Place for more scheduled jobs.
│  │  ├── reusable_vuln_scan.yml            # Check for vulnerabilities using OSV-Scanner.
│  │  └── sync_org_repositories.yml         # Manual, scheduled, and event-based workflow to synchronize files.
│  ├── dependabot.yml                       # Dependabot settings applicable to all repositories.
│  └── pull_request_template.md             # PR template applicable to all repositories.
├── docs/                                   # More detailed and specific documentation.
|  ├── LOCAL_TESTING.md                     # Documentation on how to test synchronization locally.
|  └── SYNC_REPOSITORIES_SETUP.md           # Documentation on how to setup the repository synchronization infrastructure.
├── scripts/
│  └── sync-org-repositories.py             # Python script to check and ensure consistence among repositories.
├── ...                                     # Multiple technology specific configuration files 
├── sync-config.yml                         # Configuration file consumed by `sync-org-repositories.py`
└── README.md                               # This file.
```

## Style Guides

* Reusable workflows are prefixed by `reusable_` and should have a clear, descriptive name reflecting its function.
* Reusable workflows are generic enough to be consumed by any repository within the organization.
* Regular workflows consuming reusable workflows are prefixed by `ci_`.
* Workflows must ensure the Principle of Least Privilege.
* Write permissions must be avoided. When necessary, they are defined in the minimal possible scope.
* Prefer defining explicit permissions per Job.
* PRs must pass all CI jobs.
