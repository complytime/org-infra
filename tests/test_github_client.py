# SPDX-License-Identifier: Apache-2.0

"""Tests for the shared GitHub client."""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any
from unittest.mock import MagicMock, patch

import pytest
import requests

sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

import lib.github_client as github_client  # noqa: E402
from lib.github_client import GitHubClient  # noqa: E402


class TestGitHubClientErrors:
    def _response(
        self,
        status: int,
        text: str = "",
        *,
        json_body: Any | None = None,
        headers: dict[str, str] | None = None,
        links: dict[str, dict[str, str]] | None = None,
    ) -> MagicMock:
        response = MagicMock(spec=requests.Response)
        response.status_code = status
        response.text = text
        response.headers = headers or {}
        response.links = links or {}
        if json_body is not None:
            response.json.return_value = json_body
        response.raise_for_status = MagicMock()
        if status >= 400:
            response.raise_for_status.side_effect = requests.HTTPError(response=response)
        return response

    def test_retries_rate_limit_then_succeeds(self):
        client = GitHubClient("token")
        limited = self._response(
            403,
            "API rate limit exceeded",
            headers={"X-RateLimit-Reset": "1"},
        )
        ok = self._response(200, json_body=[{"name": "repo"}])
        with (
            patch.object(client.session, "request", side_effect=[limited, ok]) as req,
            patch.object(github_client.time, "sleep") as sleeper,
        ):
            response = client._request("GET", "https://api.github.com/orgs/x/repos")
        assert response is ok
        assert req.call_count == 2
        sleeper.assert_called()

    def test_retries_server_errors(self):
        client = GitHubClient("token")
        server = self._response(500, "nope")
        ok = self._response(200, json_body=[])
        with (
            patch.object(client.session, "request", side_effect=[server, ok]),
            patch.object(github_client.time, "sleep") as sleeper,
        ):
            response = client._request("GET", "https://api.github.com/orgs/x/repos")
        assert response is ok
        sleeper.assert_called_once()

    def test_exhausted_retries_return_last_response(self):
        client = GitHubClient("token")
        server = self._response(500, "nope")
        with (
            patch.object(client.session, "request", return_value=server),
            patch.object(github_client.time, "sleep"),
        ):
            response = client._request(
                "GET", "https://api.github.com/orgs/x/repos", max_retries=3
            )
        assert response is server

    def test_zero_retries_raises_runtime_error(self):
        client = GitHubClient("token")
        with pytest.raises(RuntimeError, match="failed after retries"):
            client._request("GET", "https://api.github.com/orgs/x/repos", max_retries=0)

    def test_graphql_raises_runtime_error_on_errors_payload(self):
        client = GitHubClient("token")
        ok = self._response(
            200,
            json_body={"errors": [{"message": "forbidden"}]},
        )
        with patch.object(client, "_request", return_value=ok):
            with pytest.raises(RuntimeError, match="GraphQL errors"):
                client.graphql("query { viewer { login } }")

    def test_user_agent_is_configurable(self):
        client = GitHubClient("token", user_agent="complytime-sprint-velocity-report")
        assert client.session.headers["User-Agent"] == "complytime-sprint-velocity-report"
