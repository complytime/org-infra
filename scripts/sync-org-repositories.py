#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0

"""
Script to synchronize standard files and workflows across all repositories
defined in peribolos.yml from the .github repository.

This script uses a direct-push workflow with GitHub App authentication:
1. Clones the target repository directly
2. Creates a feature branch
3. Copies synced files and generates dependabot config
4. Pushes branch and creates a PR against the default branch

Security guardrails:
- API endpoint allowlist restricts which GitHub API calls are permitted
- Branch name prefix enforcement (only sync-repo-standards-* branches)
- No force push allowed
- Branch protection on main prevents direct pushes (human review required)
"""

import argparse
import filecmp
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import yaml
import requests

from datetime import datetime
from git import GitCommandError
from git.repo import Repo
from pathlib import Path
from typing import Dict, List, Optional, Tuple


GITHUB_API = "https://api.github.com"
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN", os.getenv("GITHUB_PAT"))
DEFAULT_CONFIG_FILE = "sync-config.yml"
SYNC_BRANCH_PREFIX = "sync-repo-standards-"
SYNC_PR_TITLE = "chore: sync repository standards"


def parse_args() -> argparse.Namespace:
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        description="Sync repository standards across organization repositories"
    )
    parser.add_argument(
        "--org",
        required=True,
        help="GitHub organization name",
    )
    parser.add_argument(
        "--config",
        default=DEFAULT_CONFIG_FILE,
        help=f"Path to sync configuration file (default: {DEFAULT_CONFIG_FILE})",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be done without making changes",
    )
    parser.add_argument(
        "--repos",
        nargs="*",
        help="Specific repositories to sync (default: all from peribolos.yml)",
    )
    return parser.parse_args()


def load_sync_config(config_path: str) -> dict:
    """Load the sync configuration file."""
    script_dir = Path(__file__).parent.parent
    full_path = f"{script_dir}/{config_path}"
    with open(full_path, "r") as f:
        return yaml.safe_load(f)


def validate_github_api_request(endpoint: str, method: str) -> bool:
    """Validate that a GitHub API request is in the allowlist.

    Only permits the minimum set of endpoints needed for the sync workflow:
    - GET repo info (check repo exists)
    - GET/POST pull requests (check existing, create new)
    - GET file contents (read existing dependabot.yml)
    """
    allowed_patterns = [
        (r"^" + re.escape(GITHUB_API) + r"/repos/[^/]+/[^/]+$", "GET"),
        (r"^" + re.escape(GITHUB_API) + r"/repos/[^/]+/[^/]+/pulls$", "GET"),
        (r"^" + re.escape(GITHUB_API) + r"/repos/[^/]+/[^/]+/pulls$", "POST"),
        (r"^" + re.escape(GITHUB_API) + r"/repos/[^/]+/[^/]+/contents/.+$", "GET"),
    ]
    return any(
        re.match(pattern, endpoint) and method == allowed_method
        for pattern, allowed_method in allowed_patterns
    )


def github_api_request(
    endpoint: str,
    method: str = "GET",
    data: Optional[dict] = None,
    params: Optional[dict] = None,
) -> Tuple[int, Dict]:
    """Make a GitHub API request using the requests library.

    Args:
        endpoint: Full API URL (e.g., "https://api.github.com/repos/org/repo")
        method: HTTP method (GET, POST, etc.)
        data: Optional JSON body to send
        params: Optional query parameters

    Returns:
        Tuple of (status_code, response_data)
    """
    if not validate_github_api_request(endpoint, method):
        print(f"Error: Endpoint {endpoint} with method {method} is not allowed")
        return 403, {"error": "Endpoint not allowed"}

    headers = {
        "Accept": "application/vnd.github+json",
        "Authorization": f"Bearer {GITHUB_TOKEN}",
        "X-GitHub-Api-Version": "2022-11-28",
    }

    try:
        response = requests.request(
            method=method,
            url=endpoint,
            headers=headers,
            json=data,
            params=params,
            timeout=30,
        )
        try:
            response_data = response.json()
        except json.JSONDecodeError:
            response_data = {"raw": response.text}
        return response.status_code, response_data
    except requests.RequestException as e:
        print(f"API request failed: {e}")
        return 500, {"error": str(e)}


def validate_branch_name(branch_name: str) -> bool:
    """Validate that a branch name uses the required sync prefix.

    This guardrail ensures the script never pushes to unexpected branches
    (e.g., main, develop, or arbitrary branch names).
    """
    return bool(branch_name) and branch_name.startswith(SYNC_BRANCH_PREFIX)


def check_existing_sync_pr(org: str, repo_name: str) -> Optional[str]:
    """Check if an open sync PR already exists for the target repository.

    Args:
        org: GitHub organization name
        repo_name: Repository name

    Returns:
        The PR URL if an open sync PR exists, None otherwise.
    """
    url = f"{GITHUB_API}/repos/{org}/{repo_name}/pulls"
    status, data = github_api_request(url, method="GET", params={"state": "open"})

    if status != 200:
        print(f"Warning: Could not check existing PRs (HTTP {status})")
        return None

    if not isinstance(data, list):
        return None

    for pr in data:
        if pr.get("title") == SYNC_PR_TITLE:
            return pr.get("html_url")

    return None


def fetch_peribolos_file(org: str) -> dict:
    """Fetch peribolos.yaml from the organization's .github repository."""
    peribolos_repo = ".github"
    github_repo_url = f"https://github.com/{org}/{peribolos_repo}.git"
    print(f"Fetching peribolos configuration from {github_repo_url}")

    with tempfile.TemporaryDirectory() as tmpdir:
        try:
            cmd = f"git clone --quiet --depth 1 {github_repo_url}"
            subprocess.check_call(cmd, cwd=tmpdir, shell=True)

            repo_path = os.path.join(tmpdir, peribolos_repo)
            peribolos_path = os.path.join(repo_path, "peribolos.yaml")
            if os.path.exists(peribolos_path):
                with open(peribolos_path, "r") as f:
                    return yaml.safe_load(f)
            print(f"Error: peribolos.yaml not found in {peribolos_repo} repository")
            sys.exit(1)
        except subprocess.CalledProcessError as e:
            print(f"Error cloning {peribolos_repo} repository: {e}")
            sys.exit(1)


def extract_repositories(peribolos_data: dict, org: str) -> list:
    """Extract list of repositories from peribolos data."""
    repos: list = []

    if "orgs" in peribolos_data and org in peribolos_data["orgs"]:
        org_data = peribolos_data["orgs"][org]
        if "repos" in org_data:
            repos = list(org_data["repos"].keys())

    print(f"Found {len(repos)} repositories in peribolos configuration for {org}")
    return repos


def compare_files(source_file: str, dest_file: str) -> bool:
    """Compare two files and return True if they are identical."""
    if not os.path.exists(dest_file):
        return False
    return filecmp.cmp(source_file, dest_file, shallow=False)


def sync_file(source_path: str, dest_path: str, relative_path: str) -> bool:
    """Sync a file from source to destination.

    Returns True if file was copied/updated, False if identical.
    """
    os.makedirs(os.path.dirname(dest_path), exist_ok=True)

    if os.path.exists(dest_path):
        if compare_files(source_path, dest_path):
            print(f"{relative_path} is up to date")
            return False
        else:
            print(f"{relative_path} needs update")
    else:
        print(f"{relative_path} is missing")

    shutil.copy2(source_path, dest_path)
    return True


def setup_git_credentials(repo_path: str, org: str, repo_name: str) -> None:
    """Configure git credentials for authenticated pushes to the target repo."""
    repo = Repo(repo_path)
    auth_url = f"https://x-access-token:{GITHUB_TOKEN}@github.com/{org}/{repo_name}.git"
    try:
        repo.remote("origin").set_url(auth_url)
    except Exception:
        repo.create_remote("origin", auth_url)


def create_branch_and_commit(
    repo_path: str,
    branch_name: str,
    files_changed: List[str],
    commit_message: str,
) -> bool:
    """Create a new branch, commit changes, and push to origin.

    Enforces branch name validation and never uses force push.
    """
    if not validate_branch_name(branch_name):
        print(
            f"Error: Branch name '{branch_name}' does not match "
            f"required prefix '{SYNC_BRANCH_PREFIX}'"
        )
        return False

    repo = Repo(repo_path)

    try:
        repo.git.checkout("-b", branch_name)

        for file_path in files_changed:
            repo.git.add(file_path)

        repo.index.commit(commit_message)

        # Push without --force (standard push only)
        repo.git.push("--set-upstream", "origin", branch_name)
        print(f"Pushed branch: {branch_name}")
        return True
    except GitCommandError as e:
        print(f"Git operation failed: {e}")
        return False


def create_pull_request(
    org: str,
    repo_name: str,
    branch_name: str,
    title: str,
    body: str,
    base_branch: str = "main",
) -> bool:
    """Create a pull request from a branch in the target repository.

    Args:
        org: Organization name
        repo_name: Repository name
        branch_name: Source branch name
        title: PR title
        body: PR body/description
        base_branch: Target branch (default: main)
    """
    data = {
        "title": title,
        "body": body,
        "base": base_branch,
        "head": branch_name,
    }

    url = f"{GITHUB_API}/repos/{org}/{repo_name}/pulls"
    status, response_data = github_api_request(url, method="POST", data=data)

    if status == 201:
        pr_url = response_data.get("html_url", "")
        print(f"Pull request created successfully: {pr_url}")
        return True
    else:
        error_msg = response_data.get("message", "Unknown error")
        print(f"Failed to create PR (HTTP {status}): {error_msg}")
        return False


def generate_dependabot_config(repo_name: str, config: dict) -> Optional[List[dict]]:
    """Build the managed set of Dependabot entries for a repository.

    Starts with common entries, then applies per-repo overrides.
    An override for the same package-ecosystem replaces the common entry.

    Args:
        repo_name: Target repository name
        config: Full sync configuration

    Returns:
        List of managed Dependabot update entries, or None if the repo
        is excluded from Dependabot sync.
    """
    dependabot_config = config.get("dependabot")
    if dependabot_config is None:
        return None

    dependabot_exclude = dependabot_config.get("exclude_repos", [])
    if repo_name in dependabot_exclude:
        return None

    common_entries = dependabot_config.get("common", [])
    overrides = dependabot_config.get("overrides", {})
    repo_overrides = overrides.get(repo_name, [])

    # Build managed set keyed by package-ecosystem.
    # Overrides replace common entries for the same ecosystem.
    managed: Dict[str, dict] = {}
    for entry in common_entries:
        ecosystem = entry["package-ecosystem"]
        managed[ecosystem] = dict(entry)

    for entry in repo_overrides:
        ecosystem = entry["package-ecosystem"]
        managed[ecosystem] = dict(entry)

    return list(managed.values())


def merge_dependabot_entries(
    managed_entries: List[dict],
    existing_path: str,
) -> str:
    """Merge managed entries with unmanaged entries from the existing file.

    Reads the existing dependabot.yml, identifies entries whose
    package-ecosystem is NOT in the managed set (unmanaged), and
    combines managed + unmanaged into the final YAML output.

    Args:
        managed_entries: Entries managed by org-infra
        existing_path: Path to the existing dependabot.yml in the cloned repo

    Returns:
        The rendered dependabot.yml content as a string.
    """
    managed_ecosystems = {entry["package-ecosystem"] for entry in managed_entries}

    unmanaged_entries: List[dict] = []
    if os.path.exists(existing_path):
        with open(existing_path, "r") as f:
            existing_data = yaml.safe_load(f)
        if existing_data and "updates" in existing_data:
            for entry in existing_data["updates"]:
                if entry.get("package-ecosystem") not in managed_ecosystems:
                    unmanaged_entries.append(entry)

    all_entries = managed_entries + unmanaged_entries

    dependabot_data = {
        "version": 2,
        "updates": all_entries,
    }

    header = (
        "# Dependabot configuration managed by org-infra.\n"
        "# Entries for managed ecosystems are overwritten on sync.\n"
        "# Additional ecosystem entries not managed by org-infra"
        " are preserved.\n"
        "# See: https://docs.github.com/code-security/dependabot/"
        "dependabot-version-updates/"
        "configuration-options-for-the-dependabot.yml-file\n\n"
    )

    return header + yaml.dump(dependabot_data, default_flow_style=False, sort_keys=False)


def sync_repository(
    org: str,
    repo_name: str,
    config: dict,
    dry_run: bool = False,
) -> bool:
    """Sync a single repository with standard files using direct push.

    Args:
        org: Organization name
        repo_name: Repository name
        config: Sync configuration
        dry_run: If True, only show what would be done
    """
    print(f"\n{'=' * 60}")
    print(f"Processing: {org}/{repo_name}")
    print(f"{'=' * 60}")

    source_root = Path(__file__).parent.parent
    files_to_sync = config.get("files_to_sync", [])
    base_branch = config.get("default_base_branch", "main")

    repo_url = f"https://github.com/{org}/{repo_name}.git"

    with tempfile.TemporaryDirectory() as tmpdir:
        try:
            # Step 1: Clone the target repository
            print(f"Cloning {repo_url}...")
            cmd = ["git", "clone", "--quiet", repo_url]
            subprocess.check_call(cmd, cwd=tmpdir, stderr=subprocess.DEVNULL)
            repo_path = os.path.join(tmpdir, repo_name)

            # Configure git credentials for push (unless dry run)
            if not dry_run:
                setup_git_credentials(repo_path, org, repo_name)

            # Step 2: Process static files to sync
            files_changed: List[str] = []
            for file_config in files_to_sync:
                source_rel_path = file_config["source"]
                dest_rel_path = file_config.get("destination", source_rel_path)

                source_path = source_root / source_rel_path
                dest_path = os.path.join(repo_path, dest_rel_path)

                if not source_path.exists():
                    print(f"Source file not found: {source_rel_path}")
                    continue

                if "exclude_repos" in file_config:
                    if repo_name in file_config["exclude_repos"]:
                        print(f"{source_rel_path} excluded for this repo")
                        continue

                if dry_run:
                    if not os.path.exists(dest_path):
                        print(f"[DRY RUN] Would add: {dest_rel_path}")
                        files_changed.append(dest_rel_path)
                    elif not compare_files(str(source_path), dest_path):
                        print(f"[DRY RUN] Would update: {dest_rel_path}")
                        files_changed.append(dest_rel_path)
                    else:
                        print(f"{dest_rel_path} is up to date")
                else:
                    if sync_file(str(source_path), dest_path, dest_rel_path):
                        files_changed.append(dest_rel_path)

            # Step 3: Generate and sync dependabot.yml
            managed_entries = generate_dependabot_config(repo_name, config)
            if managed_entries is not None:
                dependabot_dest = os.path.join(repo_path, ".github", "dependabot.yml")
                rendered = merge_dependabot_entries(managed_entries, dependabot_dest)
                dependabot_rel = ".github/dependabot.yml"

                os.makedirs(os.path.dirname(dependabot_dest), exist_ok=True)

                existing_content = ""
                if os.path.exists(dependabot_dest):
                    with open(dependabot_dest, "r") as f:
                        existing_content = f.read()

                if rendered != existing_content:
                    if dry_run:
                        print(f"[DRY RUN] Would update: {dependabot_rel} (generated)")
                    else:
                        with open(dependabot_dest, "w") as f:
                            f.write(rendered)
                        print(f"{dependabot_rel} updated (generated)")
                    files_changed.append(dependabot_rel)
                else:
                    print(f"{dependabot_rel} is up to date")

            if not files_changed:
                print(f"All files up to date for {repo_name}")
                return True

            if dry_run:
                print(f"[DRY RUN] Would create PR with {len(files_changed)} file(s)")
                return True

            # Step 4: Check for existing open sync PR
            existing_pr = check_existing_sync_pr(org, repo_name)
            if existing_pr:
                print(f"Open sync PR already exists: {existing_pr} — skipping PR creation")
                return True

            # Step 5: Create branch, commit, and push
            timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
            branch_name = f"{SYNC_BRANCH_PREFIX}{timestamp}"
            commit_message = "chore: sync repository standards\n\nUpdated files:\n" + "\n".join(
                f"- {f}" for f in files_changed
            )

            print("\nCreating branch and committing changes...")
            if not create_branch_and_commit(repo_path, branch_name, files_changed, commit_message):
                return False

            # Step 6: Create pull request
            pr_body = (
                "This PR synchronizes repository standards from "
                "org-infra.\n\n"
                "## Files Updated\n" + "\n".join(f"- `{f}`" for f in files_changed) + "\n\n"
                "## Description\n"
                "This is an automated PR to ensure repository settings "
                "are consistent across the organization.\n\n"
                "---\n"
                "*This PR was automatically generated by the "
                "sync_org_repositories workflow.*\n"
            )

            print("Creating pull request...")
            return create_pull_request(
                org,
                repo_name,
                branch_name,
                SYNC_PR_TITLE,
                pr_body,
                base_branch,
            )
        except subprocess.CalledProcessError as e:
            print(f"Error processing {repo_name}: {e}")
            return False
        except Exception as e:
            print(f"Unexpected error processing {repo_name}: {e}")
            import traceback

            traceback.print_exc()
            return False


def main() -> None:
    """Entry point for the sync script."""
    args = parse_args()

    if not GITHUB_TOKEN:
        print("Error: GITHUB_TOKEN or GITHUB_PAT environment variable not set")
        sys.exit(1)

    config = load_sync_config(args.config)

    # Fetch and parse peribolos.yml
    peribolos_data = fetch_peribolos_file(args.org)
    repositories = extract_repositories(peribolos_data, args.org)

    if not repositories:
        print("No repositories found in peribolos configuration")
        sys.exit(0)

    if args.repos:
        repositories = [r for r in repositories if r in args.repos]
        print(f"Filtering to {len(repositories)} specified repository(ies)")

    # Skip excluded repos
    excluded_repos = config.get("exclude_repos", ["org-infra"])
    repositories = [r for r in repositories if r not in excluded_repos]

    if args.dry_run:
        print("\n" + "=" * 60)
        print("DRY RUN MODE - No changes will be made")
        print("=" * 60)

    excluded_list = "\n- ".join(excluded_repos)
    print(f"{len(excluded_repos)} repositories were excluded in this sync:\n- {excluded_list}")
    print(f"\nWill process {len(repositories)} repository(ies)")

    success_count = 0
    for repo_name in repositories:
        try:
            if sync_repository(args.org, repo_name, config, args.dry_run):
                success_count += 1
        except Exception as e:
            print(f"Failed to process {repo_name}: {e}")
            import traceback

            traceback.print_exc()

    print(f"\n{'=' * 60}")
    print(f"Summary: Successfully processed {success_count}/{len(repositories)} repositories")
    print(f"{'=' * 60}")


if __name__ == "__main__":
    main()
