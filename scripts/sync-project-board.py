#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0

"""Sync open issues/PRs from configured orgs into a GitHub Project (v2).

Discovers repositories across one or more organizations, optionally links
them to the target project, and adds any open issues/PRs that are not
already on the board. PRs inherit Priority from linked issues when that
field is empty. Designed for cross-org boards where a single GitHub App
installation token is insufficient (use a PAT with multi-org access).
"""

from __future__ import annotations

import argparse
import os
import sys
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Set

import requests
import yaml

GITHUB_API = "https://api.github.com"
GITHUB_GRAPHQL = f"{GITHUB_API}/graphql"
DEFAULT_CONFIG = "project-sync-config.yml"

# Expected failure modes while iterating orgs/repos (HTTP + explicit RuntimeError).
# Keeps programming bugs (TypeError, KeyError, …) from being swallowed per item.
SYNC_EXCEPTIONS = (requests.RequestException, RuntimeError)


@dataclass
class SyncStats:
    """Counters written to the job summary."""

    repos_considered: int = 0
    repos_linked: int = 0
    repos_link_skipped: int = 0
    items_seen: int = 0
    items_already_on_board: int = 0
    items_added: int = 0
    items_failed: int = 0
    priority_set: int = 0
    priority_failed: int = 0
    errors: List[str] = field(default_factory=list)


# Project Priority / Review priority option names, highest first.
PRIORITY_RANK = {"Urgent": 4, "High": 3, "Medium": 2, "Low": 1}


@dataclass
class ProjectFields:
    """Resolved project id plus single-select field metadata."""

    project_id: str
    status_field_id: Optional[str]
    status_options: Dict[str, str]
    priority_field_id: Optional[str] = None
    priority_options: Dict[str, str] = field(default_factory=dict)
    review_priority_field_id: Optional[str] = None
    review_priority_options: Dict[str, str] = field(default_factory=dict)


class GitHubClient:
    """Thin GitHub REST + GraphQL client."""

    def __init__(self, token: str, dry_run: bool = False) -> None:
        self.dry_run = dry_run
        self.session = requests.Session()
        self.session.headers.update(
            {
                "Authorization": f"Bearer {token}",
                "Accept": "application/vnd.github+json",
                "X-GitHub-Api-Version": "2022-11-28",
                "User-Agent": "complytime-project-board-sync",
            }
        )

    def _request(
        self,
        method: str,
        url: str,
        *,
        params: Optional[Dict[str, Any]] = None,
        json_body: Optional[Dict[str, Any]] = None,
        max_retries: int = 5,
    ) -> requests.Response:
        for attempt in range(max_retries):
            response = self.session.request(
                method, url, params=params, json=json_body, timeout=60
            )
            if response.status_code in (403, 429) and "rate limit" in response.text.lower():
                reset = response.headers.get("X-RateLimit-Reset")
                sleep_for = 30
                if reset and reset.isdigit():
                    sleep_for = max(5, int(reset) - int(time.time()) + 1)
                print(f"Rate limited; sleeping {sleep_for}s (attempt {attempt + 1})")
                time.sleep(min(sleep_for, 120))
                continue
            if response.status_code >= 500:
                time.sleep(2 ** attempt)
                continue
            return response
        return response

    def rest_paginate(self, path: str, params: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """Paginate a REST collection endpoint."""
        url = f"{GITHUB_API}{path}"
        query = dict(params or {})
        query.setdefault("per_page", 100)
        items: List[Dict[str, Any]] = []
        while url:
            response = self._request("GET", url, params=query)
            response.raise_for_status()
            payload = response.json()
            if isinstance(payload, list):
                items.extend(payload)
            else:
                raise RuntimeError(f"Unexpected REST payload for {path}: {type(payload)}")
            # Subsequent pages already encode query in Link URL
            query = None
            url = response.links.get("next", {}).get("url")
        return items

    def graphql(self, query: str, variables: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        response = self._request(
            "POST",
            GITHUB_GRAPHQL,
            json_body={"query": query, "variables": variables or {}},
        )
        response.raise_for_status()
        payload = response.json()
        if payload.get("errors"):
            raise RuntimeError(f"GraphQL errors: {payload['errors']}")
        return payload["data"]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--config",
        default=DEFAULT_CONFIG,
        help=f"Path to sync config (default: {DEFAULT_CONFIG})",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Discover work and report actions without mutating the project",
    )
    parser.add_argument(
        "--orgs",
        default="",
        help="Optional space-separated org filter (defaults to all configured orgs)",
    )
    return parser.parse_args()


def load_config(path: Path) -> Dict[str, Any]:
    with path.open(encoding="utf-8") as handle:
        return yaml.safe_load(handle)


def validate_config(config: Any) -> Dict[str, Any]:
    """Validate required sync config shape; return the config on success."""
    if not isinstance(config, dict):
        raise ValueError("Config must be a mapping")
    project = config.get("project")
    if not isinstance(project, dict):
        raise ValueError("Config missing 'project' mapping")
    if not project.get("owner"):
        raise ValueError("Config project requires 'owner'")
    if "number" not in project:
        raise ValueError("Config project requires 'number'")
    organizations = config.get("organizations")
    if not isinstance(organizations, list) or not organizations:
        raise ValueError("Config requires a non-empty 'organizations' list")
    for org in organizations:
        if not isinstance(org, dict) or not org.get("name"):
            raise ValueError("Each organization requires a 'name'")
    return config


def list_org_repos(
    client: GitHubClient,
    org: str,
    *,
    exclude: Set[str],
    skip_archived: bool,
) -> List[Dict[str, Any]]:
    repos = client.rest_paginate(f"/orgs/{org}/repos", {"type": "all", "sort": "full_name"})
    selected = []
    for repo in repos:
        name = repo["name"]
        if name in exclude:
            continue
        if skip_archived and repo.get("archived"):
            continue
        selected.append(repo)
    return selected


def get_project(client: GitHubClient, owner: str, number: int) -> ProjectFields:
    """Return project id and Status / Priority / Review priority metadata."""
    data = client.graphql(
        """
        query($owner: String!, $number: Int!) {
          organization(login: $owner) {
            projectV2(number: $number) {
              id
              fields(first: 50) {
                nodes {
                  ... on ProjectV2SingleSelectField {
                    id
                    name
                    options { id name }
                  }
                }
              }
            }
          }
        }
        """,
        {"owner": owner, "number": number},
    )
    project = data["organization"]["projectV2"]
    if not project:
        raise RuntimeError(f"Project #{number} not found in org {owner}")

    fields = ProjectFields(
        project_id=project["id"],
        status_field_id=None,
        status_options={},
    )
    for node in project["fields"]["nodes"]:
        if not node:
            continue
        name = node.get("name")
        options = {opt["name"]: opt["id"] for opt in node.get("options", [])}
        if name == "Status":
            fields.status_field_id = node["id"]
            fields.status_options = options
        elif name == "Priority":
            fields.priority_field_id = node["id"]
            fields.priority_options = options
        elif name == "Review priority":
            fields.review_priority_field_id = node["id"]
            fields.review_priority_options = options
    return fields


def existing_content_ids(client: GitHubClient, project_id: str) -> Set[str]:
    """Return node IDs of issues/PRs already on the project."""
    query = """
    query($projectId: ID!, $cursor: String) {
      node(id: $projectId) {
        ... on ProjectV2 {
          items(first: 100, after: $cursor) {
            pageInfo { hasNextPage endCursor }
            nodes {
              content {
                ... on Issue { id }
                ... on PullRequest { id }
              }
            }
          }
        }
      }
    }
    """
    ids: Set[str] = set()
    cursor = None
    while True:
        data = client.graphql(query, {"projectId": project_id, "cursor": cursor})
        items = data["node"]["items"]
        for node in items["nodes"]:
            content = node.get("content") or {}
            content_id = content.get("id")
            if content_id:
                ids.add(content_id)
        if not items["pageInfo"]["hasNextPage"]:
            break
        cursor = items["pageInfo"]["endCursor"]
    return ids


def link_repository(client: GitHubClient, project_id: str, repository_id: str) -> bool:
    """Link a repository to the project. Returns True if a link was created."""
    if client.dry_run:
        print(f"  [dry-run] would link repository {repository_id}")
        return True
    try:
        client.graphql(
            """
            mutation($projectId: ID!, $repositoryId: ID!) {
              linkProjectV2ToRepository(input: {
                projectId: $projectId
                repositoryId: $repositoryId
              }) {
                repository { id nameWithOwner }
              }
            }
            """,
            {"projectId": project_id, "repositoryId": repository_id},
        )
        return True
    except RuntimeError as exc:
        message = str(exc)
        # Already linked is not a failure for idempotent syncs.
        if "already linked" in message.lower() or "already exists" in message.lower():
            return False
        raise


def list_open_items(
    client: GitHubClient,
    full_name: str,
    *,
    include_issues: bool,
    include_prs: bool,
) -> List[Dict[str, Any]]:
    """List open issues and/or PRs for a repository via REST."""
    items: List[Dict[str, Any]] = []
    # /issues returns issues + PRs; filter client-side.
    raw = client.rest_paginate(
        f"/repos/{full_name}/issues",
        {"state": "open", "direction": "asc"},
    )
    for entry in raw:
        is_pr = "pull_request" in entry
        if is_pr and not include_prs:
            continue
        if (not is_pr) and not include_issues:
            continue
        items.append(entry)
    return items


def set_single_select(
    client: GitHubClient,
    project_id: str,
    item_id: str,
    field_id: str,
    option_id: str,
) -> None:
    """Set a project single-select field value."""
    if client.dry_run:
        print(f"  [dry-run] would set field {field_id}={option_id} on {item_id}")
        return
    client.graphql(
        """
        mutation($projectId: ID!, $itemId: ID!, $fieldId: ID!, $optionId: String!) {
          updateProjectV2ItemFieldValue(input: {
            projectId: $projectId
            itemId: $itemId
            fieldId: $fieldId
            value: { singleSelectOptionId: $optionId }
          }) {
            projectV2Item { id }
          }
        }
        """,
        {
            "projectId": project_id,
            "itemId": item_id,
            "fieldId": field_id,
            "optionId": option_id,
        },
    )


def add_item(
    client: GitHubClient,
    project_id: str,
    content_id: str,
    status_field_id: Optional[str],
    status_option_id: Optional[str],
) -> None:
    if client.dry_run:
        print(f"  [dry-run] would add {content_id}")
        return

    data = client.graphql(
        """
        mutation($projectId: ID!, $contentId: ID!) {
          addProjectV2ItemById(input: {projectId: $projectId, contentId: $contentId}) {
            item { id }
          }
        }
        """,
        {"projectId": project_id, "contentId": content_id},
    )
    item_id = data["addProjectV2ItemById"]["item"]["id"]

    if status_field_id and status_option_id:
        set_single_select(
            client, project_id, item_id, status_field_id, status_option_id
        )


def highest_priority(names: List[Optional[str]]) -> Optional[str]:
    """Return the highest named Priority among known options, if any."""
    ranked = [name for name in names if name in PRIORITY_RANK]
    if not ranked:
        return None
    return max(ranked, key=lambda name: PRIORITY_RANK[name])


def list_board_priority_items(
    client: GitHubClient, project_id: str
) -> List[Dict[str, Any]]:
    """Return board items with Priority, Review priority, and linked issues."""
    query = """
    query($projectId: ID!, $cursor: String) {
      node(id: $projectId) {
        ... on ProjectV2 {
          items(first: 100, after: $cursor) {
            pageInfo { hasNextPage endCursor }
            nodes {
              id
              priority: fieldValueByName(name: "Priority") {
                ... on ProjectV2ItemFieldSingleSelectValue { name }
              }
              reviewPriority: fieldValueByName(name: "Review priority") {
                ... on ProjectV2ItemFieldSingleSelectValue { name }
              }
              content {
                __typename
                ... on Issue { id }
                ... on PullRequest {
                  id
                  closingIssuesReferences(first: 20) {
                    nodes { id }
                  }
                }
              }
            }
          }
        }
      }
    }
    """
    collected: List[Dict[str, Any]] = []
    cursor = None
    while True:
        data = client.graphql(query, {"projectId": project_id, "cursor": cursor})
        items = data["node"]["items"]
        collected.extend(items["nodes"])
        if not items["pageInfo"]["hasNextPage"]:
            break
        cursor = items["pageInfo"]["endCursor"]
    return collected


def _copy_priority_field(
    client: GitHubClient,
    fields: ProjectFields,
    item_id: str,
    option_name: str,
    field_id: Optional[str],
    options: Dict[str, str],
    stats: SyncStats,
    label: str,
) -> None:
    """Copy a named priority onto one single-select field when it is mapped."""
    option_id = options.get(option_name)
    if not field_id or not option_id:
        return
    try:
        set_single_select(client, fields.project_id, item_id, field_id, option_id)
        stats.priority_set += 1
        print(f"  priority {label} -> {option_name}")
    except SYNC_EXCEPTIONS as exc:
        stats.priority_failed += 1
        msg = f"Failed copying Priority onto {label}: {exc}"
        print(f"  ! {msg}")
        stats.errors.append(msg)


def ensure_pr_priority_from_issues(
    client: GitHubClient,
    fields: ProjectFields,
    stats: SyncStats,
) -> None:
    """Set empty PR Priority / Review priority from linked issues.

    Uses ``closingIssuesReferences`` (Fixes/Closes and Development links).
    Does not default a value when there is no linked issue, or when linked
    issues have no Priority. Does not overwrite a value already set on the PR.
    If several linked issues have Priority, the highest rank wins.
    """
    if not fields.priority_field_id and not fields.review_priority_field_id:
        print("Priority fields missing on project; skipping PR priority copy")
        return

    print("\n=== Copying Priority from linked issues onto PRs ===")
    issue_priority: Dict[str, Optional[str]] = {}
    pr_nodes: List[Dict[str, Any]] = []
    for node in list_board_priority_items(client, fields.project_id):
        content = node.get("content") or {}
        content_id = content.get("id")
        if not content_id:
            continue
        current = (node.get("priority") or {}).get("name")
        typename = content.get("__typename")
        if typename == "Issue":
            issue_priority[content_id] = current
            continue
        if typename == "PullRequest":
            pr_nodes.append(node)

    for node in pr_nodes:
        content = node.get("content") or {}
        linked = content.get("closingIssuesReferences") or {}
        linked_ids = [item.get("id") for item in linked.get("nodes") or []]
        wanted = highest_priority([issue_priority.get(cid) for cid in linked_ids])
        if not wanted:
            continue
        item_id = node["id"]
        current_priority = (node.get("priority") or {}).get("name")
        current_review = (node.get("reviewPriority") or {}).get("name")
        pr_id = content.get("id") or item_id
        if not current_priority:
            _copy_priority_field(
                client,
                fields,
                item_id,
                wanted,
                fields.priority_field_id,
                fields.priority_options,
                stats,
                f"Priority {pr_id}",
            )
        if not current_review:
            _copy_priority_field(
                client,
                fields,
                item_id,
                wanted,
                fields.review_priority_field_id,
                fields.review_priority_options,
                stats,
                f"Review priority {pr_id}",
            )


def format_summary(stats: SyncStats, dry_run: bool) -> str:
    """Format the job summary markdown (pure; no I/O)."""
    lines = [
        "## Compliance Automation project sync",
        "",
        f"- Mode: `{'dry-run' if dry_run else 'apply'}`",
        f"- Repositories considered: **{stats.repos_considered}**",
        f"- Repositories linked: **{stats.repos_linked}**"
        + (f" (skipped/already linked: {stats.repos_link_skipped})" if stats.repos_link_skipped else ""),
        f"- Open items scanned: **{stats.items_seen}**",
        f"- Already on board: **{stats.items_already_on_board}**",
        f"- Added: **{stats.items_added}**",
        f"- Failed: **{stats.items_failed}**",
        f"- Priority copied from linked issues: **{stats.priority_set}**",
        f"- Priority copy failed: **{stats.priority_failed}**",
    ]
    if stats.errors:
        lines.extend(["", "### Errors", ""])
        lines.extend(f"- `{err}`" for err in stats.errors[:50])
    return "\n".join(lines) + "\n"


def write_summary(stats: SyncStats, dry_run: bool) -> None:
    """Print the job summary and append it to GITHUB_STEP_SUMMARY when set."""
    summary = format_summary(stats, dry_run)
    print(summary)
    step_summary = os.getenv("GITHUB_STEP_SUMMARY")
    if step_summary:
        with open(step_summary, "a", encoding="utf-8") as handle:
            handle.write(summary)


def sync(config: Dict[str, Any], client: GitHubClient, org_filter: Set[str]) -> SyncStats:
    stats = SyncStats()
    project_cfg = config["project"]
    sync_cfg = config.get("sync", {})
    owner = project_cfg["owner"]
    number = int(project_cfg["number"])
    default_status = project_cfg.get("default_status", "Backlog")
    include_issues = bool(sync_cfg.get("issues", True))
    include_prs = bool(sync_cfg.get("pull_requests", True))
    skip_archived = bool(sync_cfg.get("skip_archived", True))
    link_repos = bool(sync_cfg.get("link_repositories", True))

    fields = get_project(client, owner, number)
    project_id = fields.project_id
    status_field_id = fields.status_field_id
    status_options = fields.status_options
    status_option_id = status_options.get(default_status) if status_options else None
    if default_status and status_field_id and not status_option_id:
        print(
            f"Warning: Status option '{default_status}' not found; "
            "items will be added without a Status value"
        )

    print(f"Project {owner}/{number} id={project_id}")
    on_board = existing_content_ids(client, project_id)
    print(f"Existing board items with content: {len(on_board)}")

    for org_cfg in config.get("organizations", []):
        org = org_cfg["name"]
        if org_filter and org not in org_filter:
            continue
        exclude = set(org_cfg.get("exclude_repos") or [])
        print(f"\n=== {org} (exclude={sorted(exclude) or 'none'}) ===")
        try:
            repos = list_org_repos(
                client, org, exclude=exclude, skip_archived=skip_archived
            )
        except SYNC_EXCEPTIONS as exc:
            msg = f"Failed listing repos for {org}: {exc}"
            print(msg)
            stats.errors.append(msg)
            continue

        for repo in repos:
            full_name = repo["full_name"]
            stats.repos_considered += 1
            print(f"\n- {full_name}")

            if link_repos:
                # GitHub only allows linking a repository to a project owned by
                # the same org. Cross-org boards (e.g. unbound-force repos on a
                # complytime project) can still receive issues/PRs via
                # addProjectV2ItemById — skip the unsupported link step.
                if org != owner:
                    stats.repos_link_skipped += 1
                    print(
                        "  skip repo link (cross-org; items still sync onto the board)"
                    )
                else:
                    try:
                        linked = link_repository(
                            client, project_id, repo["node_id"]
                        )
                        if linked:
                            stats.repos_linked += 1
                            print("  linked to project")
                        else:
                            stats.repos_link_skipped += 1
                            print("  already linked (or skipped)")
                    except SYNC_EXCEPTIONS as exc:
                        # Linking is best-effort for same-org repos (permissions
                        # may be missing). Do not fail the job: item sync is the
                        # primary goal.
                        stats.repos_link_skipped += 1
                        print(f"  skip repo link for {full_name} ({exc})")

            try:
                open_items = list_open_items(
                    client,
                    full_name,
                    include_issues=include_issues,
                    include_prs=include_prs,
                )
            except SYNC_EXCEPTIONS as exc:
                msg = f"Failed listing items for {full_name}: {exc}"
                print(f"  {msg}")
                stats.errors.append(msg)
                continue

            for item in open_items:
                stats.items_seen += 1
                node_id = item["node_id"]
                title = item.get("title", "")
                number_ = item.get("number")
                kind = "PR" if "pull_request" in item else "Issue"
                label = f"{kind} #{number_}: {title}"

                if node_id in on_board:
                    stats.items_already_on_board += 1
                    continue

                try:
                    add_item(
                        client,
                        project_id,
                        node_id,
                        status_field_id,
                        status_option_id,
                    )
                    stats.items_added += 1
                    on_board.add(node_id)
                    print(f"  + {label}")
                except SYNC_EXCEPTIONS as exc:
                    stats.items_failed += 1
                    msg = f"Failed adding {full_name} {label}: {exc}"
                    print(f"  ! {msg}")
                    stats.errors.append(msg)

    ensure_pr_priority_from_issues(client, fields, stats)
    return stats


def main() -> int:
    args = parse_args()
    token = os.getenv("GITHUB_TOKEN") or os.getenv("PROJECT_SYNC_TOKEN")
    if not token:
        print("GITHUB_TOKEN or PROJECT_SYNC_TOKEN is required", file=sys.stderr)
        return 2

    config_path = Path(args.config)
    if not config_path.exists():
        print(f"Config not found: {config_path}", file=sys.stderr)
        return 2

    try:
        config = validate_config(load_config(config_path))
    except ValueError as exc:
        print(f"Invalid config: {exc}", file=sys.stderr)
        return 2
    org_filter = {part for part in args.orgs.split() if part}
    client = GitHubClient(token=token, dry_run=args.dry_run)
    stats = sync(config, client, org_filter)
    write_summary(stats, dry_run=args.dry_run)
    return 1 if stats.items_failed or stats.errors else 0


if __name__ == "__main__":
    sys.exit(main())
