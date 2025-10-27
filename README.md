# ⚙️ CI/CD Reusable Workflows

This repository centrally manages the standardized CI/CD workflows for the organization.
Its purpose is to ensure **security, consistency, and reusability** across all consuming repositories by defining common automation processes once.

---

## 🎯 Purpose

The primary goal is to provide **pre-vetted, security-hardened pipeline steps** for common tasks, such as environment deployment, lint checks, and dependency review.

Specifically, this repository includes:

* [Reusable Workflows](https://docs.github.com/en/actions/how-tos/reuse-automations/reuse-workflows) for dependencies review, vulnerability scanning, lint issues, etc.
* Templates to consume reusable workflows in org repositories.
* Templates for PRs and Issues
* Standardized labeling and commentary on pull requests.
* WIP

---

## 📁 Directory Structure

```
org-infra/
├── .github/
│  └── workflows/
│     ├── ci_checks.yml                     # Workflow to consume `reusable_ci`. Can be expanded with local and specific jobs if necessary.
│     ├── reusable_ci.yml                   # Generic CI checks, such as linters and typos
│     ├── reusable_dependabot_reviewer.yml  # Specific for dependabot PRs, classify risk based on semantic version and checks adoption.
│     ├── reusable_deps_reviewer.yml        # Check for vulnerabilities, license issues, and OpenSSF Scorecard Level.
│     └── review_dependencies.yml           # First consumes `reusable_deps_reviewer` and `reusable_dependabot_reviewer`,
│                                           # then use outputs to write a review comment and auto-approve dependabot PRs based on ORG criteria.
├── templates                               # This directory holds templated files to be synchronized with org repositories.
│  ├── .github/
│  │  ├── ISSUE_TEMPLATE/
│  │  │  ├── bug_report.md                  # Issue template to report a Bug.
│  │  │  └── feature_request.md             # Issue template to request a Feature.
│  ├── workflows/
│  │  ├── WIP
│  │  └── WIP
│  ├── dependabot.yml                       # Same dependabot settings for all repositories.
│  └── pull_request_template.md             # Same PR template for all repositories.
└── README.md
```

## Style Guides

* Reusable workflows are prefixed by `reusable_` and should have a clear, descriptive name reflecting its function.
* WIP
