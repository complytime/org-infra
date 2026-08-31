#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
"""Assign peribolos-team members to open issues/PRs with matching milestones.

Reads team membership from complytime/.github peribolos.yaml so reviewer
changes are a single peribolos PR. Issues get those members as assignees;
pull requests get them as requested reviewers. Existing assignees/reviewers
are left in place. The item author is skipped.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import urllib.error
import urllib.parse
import urllib.request
from typing import Any, Dict, Iterable, List, Optional, Sequence, Set

import yaml

API_ROOT = "https://api.github.com"
HTTP_ERROR_DETAIL_LIMIT = 500


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Assign milestone reviewers from a peribolos team"
    )
    parser.add_argument(
        "--config",
        default="milestone-reviewers-config.yml",
        help="Path to the assignment config YAML file",
    )
    parser.add_argument(
        "--peribolos-file",
        help="Read peribolos YAML from disk instead of the GitHub API",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show intended changes without applying them",
    )
    parser.add_argument(
        "--token-env",
        default="GITHUB_TOKEN",
        help="Environment variable that contains the GitHub token",
    )
    return parser.parse_args()


def get_token(name: str) -> str:
    token = os.getenv(name)
    if not token:
        raise SystemExit(f"Missing required token environment variable: {name}")
    return token


def load_yaml_file(path: str) -> dict:
    with open(path, "r", encoding="utf-8") as handle:
        data = yaml.safe_load(handle)
    if not isinstance(data, dict):
        raise SystemExit(f"Expected mapping in {path}")
    return data


def load_config(path: str) -> dict:
    config = load_yaml_file(path)
    for required in ("org", "team", "milestone_titles", "peribolos_repo", "peribolos_path"):
        if required not in config:
            raise SystemExit(f"Config {path} is missing required key: {required}")
    titles = config["milestone_titles"]
    if not isinstance(titles, list) or not titles:
        raise SystemExit("milestone_titles must be a non-empty list")
    config.setdefault("peribolos_ref", "main")
    config.setdefault("exclude_repos", [])
    return config


def normalize_title(title: str) -> str:
    return " ".join(title.strip().split()).casefold()


def matching_titles(configured: Sequence[str]) -> Set[str]:
    return {normalize_title(title) for title in configured if str(title).strip()}


def extract_team_members(peribolos: dict, org: str, team: str) -> List[str]:
    """Return the reviewer pool from peribolos team members (not maintainers)."""
    orgs = peribolos.get("orgs")
    if not isinstance(orgs, dict) or org not in orgs:
        raise SystemExit(f"Organization {org!r} not found in peribolos config")
    teams = orgs[org].get("teams")
    if not isinstance(teams, dict) or team not in teams:
        raise SystemExit(f"Team {team!r} not found in peribolos config for {org}")
    members = teams[team].get("members") or []
    if not isinstance(members, list):
        raise SystemExit(f"Team {team!r} members must be a list")
    cleaned = [str(login).strip() for login in members if str(login).strip()]
    if not cleaned:
        raise SystemExit(f"Team {team!r} has no members to assign")
    return cleaned


def logins_to_add(candidates: Sequence[str], skip: Iterable[str]) -> List[str]:
    """Preserve peribolos order; drop skipped logins case-insensitively."""
    skipped = {login.casefold() for login in skip if login}
    seen: Set[str] = set()
    result: List[str] = []
    for login in candidates:
        key = login.casefold()
        if key in skipped or key in seen:
            continue
        seen.add(key)
        result.append(login)
    return result


def is_pull_request(item: dict) -> bool:
    return bool(item.get("pull_request")) or "pull_request" in item


def gh_request(
    token: str,
    method: str,
    path: str,
    body: dict | None = None,
    query: dict | None = None,
    extra_headers: Optional[Dict[str, str]] = None,
    raw: bool = False,
) -> Any:
    url = f"{API_ROOT}{path}"
    if query:
        url = f"{url}?{urllib.parse.urlencode(query)}"
    data = None if body is None else json.dumps(body).encode("utf-8")
    headers = {
        "Accept": "application/vnd.github.raw" if raw else "application/vnd.github+json",
        "Authorization": f"Bearer {token}",
        "X-GitHub-Api-Version": "2022-11-28",
        "User-Agent": "complytime-milestone-reviewers",
    }
    if body is not None:
        headers["Content-Type"] = "application/json"
    if extra_headers:
        headers.update(extra_headers)
    request = urllib.request.Request(url=url, data=data, method=method, headers=headers)
    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            payload = response.read()
            if not payload:
                return None
            if raw:
                return payload.decode("utf-8")
            return json.loads(payload.decode("utf-8"))
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        if len(detail) > HTTP_ERROR_DETAIL_LIMIT:
            detail = detail[:HTTP_ERROR_DETAIL_LIMIT] + "...(truncated)"
        raise RuntimeError(f"{method} {path} failed: HTTP {exc.code}: {detail}") from exc


def gh_paginate(token: str, path: str, query: Optional[dict] = None) -> List[dict]:
    items: List[dict] = []
    page = 1
    base_query = dict(query or {})
    while True:
        page_query = {**base_query, "per_page": 100, "page": page}
        batch = gh_request(token, "GET", path, query=page_query)
        if not isinstance(batch, list):
            raise TypeError(f"Expected list from {path}, got {type(batch).__name__}")
        if not batch:
            break
        items.extend(batch)
        page += 1
    return items


def fetch_peribolos(token: str, org: str, repo: str, path: str, ref: str) -> dict:
    raw = gh_request(
        token,
        "GET",
        f"/repos/{org}/{urllib.parse.quote(repo)}/contents/{path}",
        query={"ref": ref},
        raw=True,
    )
    if not isinstance(raw, str) or not raw.strip():
        raise SystemExit(f"Empty peribolos file at {org}/{repo}/{path}@{ref}")
    data = yaml.safe_load(raw)
    if not isinstance(data, dict):
        raise SystemExit("peribolos.yaml is not a mapping")
    return data


def list_repos(token: str, org: str, exclude: Sequence[str]) -> List[dict]:
    exclude_set = {name.strip() for name in exclude if str(name).strip()}
    repos = []
    for repo in gh_paginate(token, f"/orgs/{org}/repos", query={"type": "all"}):
        name = repo.get("name")
        if not name or name in exclude_set or repo.get("archived"):
            continue
        repos.append(repo)
    repos.sort(key=lambda item: item["name"])
    return repos


def matching_milestones(milestones: Sequence[dict], titles: Set[str]) -> List[dict]:
    matched = []
    for milestone in milestones:
        title = milestone.get("title") or ""
        if normalize_title(title) in titles:
            matched.append(milestone)
    return matched


def current_assignees(item: dict) -> Set[str]:
    return {
        (assignee.get("login") or "")
        for assignee in item.get("assignees") or []
        if assignee.get("login")
    }


def current_reviewers(review_payload: dict) -> Set[str]:
    users = {
        (user.get("login") or "")
        for user in review_payload.get("users") or []
        if user.get("login")
    }
    return users


def assign_issue(token: str, org: str, repo: str, number: int, logins: Sequence[str]) -> None:
    gh_request(
        token,
        "POST",
        f"/repos/{org}/{repo}/issues/{number}/assignees",
        body={"assignees": list(logins)},
    )


def request_reviewers(
    token: str, org: str, repo: str, number: int, logins: Sequence[str]
) -> None:
    gh_request(
        token,
        "POST",
        f"/repos/{org}/{repo}/pulls/{number}/requested_reviewers",
        body={"reviewers": list(logins)},
    )


def process_item(
    token: str,
    org: str,
    repo: str,
    item: dict,
    members: Sequence[str],
    dry_run: bool,
) -> str:
    number = item["number"]
    author = ((item.get("user") or {}).get("login")) or ""
    html_url = item.get("html_url") or f"{org}/{repo}#{number}"

    if is_pull_request(item):
        requested = gh_request(
            token, "GET", f"/repos/{org}/{repo}/pulls/{number}/requested_reviewers"
        ) or {"users": []}
        if not isinstance(requested, dict):
            requested = {"users": []}
        skip = {author, *current_reviewers(requested)}
        to_add = logins_to_add(members, skip)
        if not to_add:
            return f"skip PR {html_url}: reviewers already requested"
        action = f"request reviewers {', '.join(to_add)} on PR {html_url}"
        if not dry_run:
            request_reviewers(token, org, repo, number, to_add)
        return action

    skip = {author, *current_assignees(item)}
    to_add = logins_to_add(members, skip)
    if not to_add:
        return f"skip issue {html_url}: assignees already set"
    action = f"assign {', '.join(to_add)} on issue {html_url}"
    if not dry_run:
        assign_issue(token, org, repo, number, to_add)
    return action


def run(config: dict, token: str, peribolos: dict, dry_run: bool) -> int:
    org = config["org"]
    team = config["team"]
    members = extract_team_members(peribolos, org, team)
    titles = matching_titles(config["milestone_titles"])
    repos = list_repos(token, org, config.get("exclude_repos") or [])

    print(f"Team {team} members: {', '.join(members)}")
    print(f"Milestone titles: {', '.join(config['milestone_titles'])}")
    print(f"Repositories: {len(repos)}")
    if dry_run:
        print("Dry run: no assignments will be written")

    actions = 0
    errors = 0
    for repo in repos:
        name = repo["name"]
        try:
            milestones = gh_paginate(token, f"/repos/{org}/{name}/milestones", query={"state": "open"})
            matched = matching_milestones(milestones, titles)
            if not matched:
                continue
            for milestone in matched:
                issues = gh_paginate(
                    token,
                    f"/repos/{org}/{name}/issues",
                    query={"state": "open", "milestone": milestone["number"]},
                )
                for item in issues:
                    try:
                        message = process_item(token, org, name, item, members, dry_run)
                    except RuntimeError as exc:
                        errors += 1
                        print(f"ERROR {name}#{item.get('number')}: {exc}", file=sys.stderr)
                        continue
                    print(message)
                    if not message.startswith("skip "):
                        actions += 1
        except RuntimeError as exc:
            errors += 1
            print(f"ERROR repo {name}: {exc}", file=sys.stderr)
            continue

    print(f"Done. applied={actions} errors={errors}")
    return 1 if errors else 0


def main() -> int:
    args = parse_args()
    config = load_config(args.config)
    token = get_token(args.token_env)
    if args.peribolos_file:
        peribolos = load_yaml_file(args.peribolos_file)
    else:
        peribolos = fetch_peribolos(
            token,
            config["org"],
            config["peribolos_repo"],
            config["peribolos_path"],
            config["peribolos_ref"],
        )
    return run(config, token, peribolos, args.dry_run)


if __name__ == "__main__":
    raise SystemExit(main())
