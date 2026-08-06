#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
"""Synchronize GitHub labels across organization repositories.

This tool intentionally supports three behaviors:
1. Ensure a core set of standard labels exists everywhere.
2. Rename legacy labels in-place only where they already exist.
3. Delete only explicitly-listed labels, leaving all other local labels alone.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import urllib.error
import urllib.parse
import urllib.request
from typing import Dict, Iterable, List, Tuple


API_ROOT = "https://api.github.com"
REPO_NAME_RE = re.compile(r"^[A-Za-z0-9._-]+$")
HTTP_ERROR_DETAIL_LIMIT = 500


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Sync labels across GitHub repositories")
    parser.add_argument("--policy", default="labels-policy.json", help="Path to the label policy JSON file")
    parser.add_argument("--org", help="GitHub organization to manage; defaults to policy value")
    parser.add_argument(
        "--repos",
        nargs="*",
        help="Optional subset of repos to target (space- or comma-separated names)",
    )
    parser.add_argument("--dry-run", action="store_true", help="Show intended changes without applying them")
    parser.add_argument(
        "--token-env",
        default="GITHUB_TOKEN",
        help="Environment variable that contains the GitHub token",
    )
    return parser.parse_args()


def expand_repo_args(repos: Iterable[str] | None) -> List[str] | None:
    """Expand space/comma-separated repo names and validate each token."""
    if not repos:
        return None

    expanded: List[str] = []
    for item in repos:
        for part in item.split(","):
            name = part.strip()
            if not name:
                continue
            if not REPO_NAME_RE.fullmatch(name):
                raise SystemExit(
                    f"Invalid repo name {name!r}: only alphanumeric, dots, hyphens, "
                    "and underscores are allowed"
                )
            expanded.append(name)
    return expanded


def load_policy(path: str) -> dict:
    with open(path, "r", encoding="utf-8") as handle:
        return json.load(handle)


def get_token(name: str) -> str:
    token = os.getenv(name)
    if not token:
        raise SystemExit(f"Missing required token environment variable: {name}")
    return token


def gh_request(
    token: str,
    method: str,
    path: str,
    body: dict | None = None,
    query: dict | None = None,
) -> dict | list | None:
    url = f"{API_ROOT}{path}"
    if query:
        url = f"{url}?{urllib.parse.urlencode(query)}"
    data = None if body is None else json.dumps(body).encode("utf-8")
    request = urllib.request.Request(
        url=url,
        data=data,
        method=method,
        headers={
            "Accept": "application/vnd.github+json",
            "Authorization": f"Bearer {token}",
            "X-GitHub-Api-Version": "2022-11-28",
            "Content-Type": "application/json",
        },
    )
    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            payload = response.read()
            if not payload:
                return None
            return json.loads(payload.decode("utf-8"))
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        if len(detail) > HTTP_ERROR_DETAIL_LIMIT:
            detail = detail[:HTTP_ERROR_DETAIL_LIMIT] + "...(truncated)"
        raise RuntimeError(f"{method} {path} failed: HTTP {exc.code}: {detail}") from exc


def gh_paginate(token: str, path: str) -> List[dict]:
    items: List[dict] = []
    page = 1
    while True:
        batch = gh_request(token, "GET", path, query={"per_page": 100, "page": page})
        if not isinstance(batch, list):
            raise TypeError(f"Expected list from {path}, got {type(batch).__name__}")
        if not batch:
            break
        items.extend(batch)
        page += 1
    return items


def normalize(name: str) -> str:
    return name.strip().casefold()


def list_repos(token: str, org: str, include: Iterable[str] | None, exclude: Iterable[str]) -> List[str]:
    include_set = {repo.strip() for repo in include or [] if repo.strip()}
    exclude_set = {repo.strip() for repo in exclude if repo.strip()}
    repos = [
        repo["name"]
        for repo in gh_paginate(token, f"/orgs/{org}/repos")
        if repo.get("name") not in exclude_set
    ]
    repos.sort()
    if include_set:
        repos = [repo for repo in repos if repo in include_set]
    return repos


def list_labels(token: str, org: str, repo: str) -> List[dict]:
    return gh_paginate(token, f"/repos/{org}/{repo}/labels")


def patch_label(
    token: str,
    org: str,
    repo: str,
    current_name: str,
    desired: dict,
    dry_run: bool,
) -> None:
    print(f"  update label: {current_name!r} -> {desired['name']!r}")
    if dry_run:
        return
    gh_request(
        token,
        "PATCH",
        f"/repos/{org}/{repo}/labels/{urllib.parse.quote(current_name, safe='')}",
        body=desired,
    )


def create_label(token: str, org: str, repo: str, desired: dict, dry_run: bool) -> None:
    print(f"  create label: {desired['name']!r}")
    if dry_run:
        return
    gh_request(token, "POST", f"/repos/{org}/{repo}/labels", body=desired)


def delete_label(token: str, org: str, repo: str, name: str, dry_run: bool) -> None:
    print(f"  delete label: {name!r}")
    if dry_run:
        return
    gh_request(
        token,
        "DELETE",
        f"/repos/{org}/{repo}/labels/{urllib.parse.quote(name, safe='')}",
    )


def ensure_standard_labels(
    token: str,
    org: str,
    repo: str,
    labels_by_norm: Dict[str, dict],
    policy_labels: List[dict],
    dry_run: bool,
) -> None:
    for desired in policy_labels:
        key = normalize(desired["name"])
        existing = labels_by_norm.get(key)
        if existing is None:
            create_label(token, org, repo, desired, dry_run)
            labels_by_norm[key] = {"name": desired["name"], **desired}
            continue

        needs_update = (
            existing.get("name") != desired["name"]
            or normalize(existing.get("color", "")) != normalize(desired["color"])
            or (existing.get("description") or "") != desired["description"]
        )
        if needs_update:
            patch_label(token, org, repo, existing["name"], desired, dry_run)
            labels_by_norm[key] = {"name": desired["name"], **desired}


def apply_rename_only_labels(
    token: str,
    org: str,
    repo: str,
    labels_by_norm: Dict[str, dict],
    rename_rules: List[dict],
    dry_run: bool,
) -> None:
    for rule in rename_rules:
        desired = rule["to"]
        destination_key = normalize(desired["name"])
        destination = labels_by_norm.get(destination_key)

        sources: List[Tuple[str, dict]] = []
        for legacy_name in rule["from"]:
            source = labels_by_norm.get(normalize(legacy_name))
            if source is not None:
                sources.append((legacy_name, source))

        if not sources and destination is None:
            continue

        if destination is not None:
            needs_update = (
                destination.get("name") != desired["name"]
                or normalize(destination.get("color", "")) != normalize(desired["color"])
                or (destination.get("description") or "") != desired["description"]
            )
            if needs_update:
                patch_label(token, org, repo, destination["name"], desired, dry_run)
                labels_by_norm[destination_key] = {"name": desired["name"], **desired}

        if destination is None and sources:
            source_name = sources[0][1]["name"]
            patch_label(token, org, repo, source_name, desired, dry_run)
            labels_by_norm[destination_key] = {"name": desired["name"], **desired}
            del labels_by_norm[normalize(source_name)]
            sources = sources[1:]

        for _, source in sources:
            if normalize(source["name"]) == destination_key:
                continue
            delete_label(token, org, repo, source["name"], dry_run)
            labels_by_norm.pop(normalize(source["name"]), None)


def apply_deletes(
    token: str,
    org: str,
    repo: str,
    labels_by_norm: Dict[str, dict],
    names: List[str],
    dry_run: bool,
) -> None:
    for name in names:
        existing = labels_by_norm.get(normalize(name))
        if existing is None:
            continue
        delete_label(token, org, repo, existing["name"], dry_run)
        labels_by_norm.pop(normalize(existing["name"]), None)


def main() -> int:
    args = parse_args()
    policy = load_policy(args.policy)
    token = get_token(args.token_env)
    org = args.org or policy["org"]
    selected_repos = expand_repo_args(args.repos)
    repos = list_repos(token, org, selected_repos, policy["exclude_repos"])

    if not repos:
        print("No repositories selected.")
        return 0

    print(f"Target repositories ({len(repos)}): {', '.join(repos)}")
    for repo in repos:
        print(f"\n== {repo} ==")
        labels = list_labels(token, org, repo)
        labels_by_norm = {normalize(label["name"]): label for label in labels}
        apply_rename_only_labels(
            token,
            org,
            repo,
            labels_by_norm,
            policy["rename_only_labels"],
            args.dry_run,
        )
        ensure_standard_labels(
            token,
            org,
            repo,
            labels_by_norm,
            policy["standard_labels"],
            args.dry_run,
        )
        apply_deletes(
            token,
            org,
            repo,
            labels_by_norm,
            policy["delete_labels"],
            args.dry_run,
        )

    print("\nDone.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
