# SPDX-License-Identifier: Apache-2.0

"""Shared GitHub REST + GraphQL client with retries."""

from __future__ import annotations

import time
from typing import Any

import requests

GITHUB_API = "https://api.github.com"
GITHUB_GRAPHQL = f"{GITHUB_API}/graphql"
DEFAULT_USER_AGENT = "complytime-org-infra"


class GitHubClient:
    """Thin GitHub REST + GraphQL client."""

    def __init__(
        self,
        token: str,
        dry_run: bool = False,
        user_agent: str = DEFAULT_USER_AGENT,
    ) -> None:
        self.dry_run = dry_run
        self.session = requests.Session()
        self.session.headers.update(
            {
                "Authorization": f"Bearer {token}",
                "Accept": "application/vnd.github+json",
                "X-GitHub-Api-Version": "2022-11-28",
                "User-Agent": user_agent,
            }
        )

    def _request(
        self,
        method: str,
        url: str,
        *,
        params: dict[str, Any] | None = None,
        json_body: dict[str, Any] | None = None,
        max_retries: int = 5,
    ) -> requests.Response:
        response: requests.Response | None = None
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
                time.sleep(2**attempt)
                continue
            return response
        if response is None:
            raise RuntimeError("GitHub request failed after retries")
        return response

    def rest_paginate(self, path: str, params: dict[str, Any] | None = None) -> list[dict[str, Any]]:
        """Paginate a REST collection endpoint."""
        url = f"{GITHUB_API}{path}"
        query = dict(params or {})
        query.setdefault("per_page", 100)
        items: list[dict[str, Any]] = []
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

    def graphql(self, query: str, variables: dict[str, Any] | None = None) -> dict[str, Any]:
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
