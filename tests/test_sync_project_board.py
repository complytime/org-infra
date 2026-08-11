# SPDX-License-Identifier: Apache-2.0

"""Tests for sync-project-board.py."""

from __future__ import annotations

import importlib
import sys
from pathlib import Path
from typing import Any, Dict, Optional
from unittest.mock import MagicMock, patch

import pytest
import requests
import yaml

sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

sync = importlib.import_module("sync-project-board")


def _minimal_config(**overrides: Any) -> Dict[str, Any]:
    config: Dict[str, Any] = {
        "project": {"owner": "complytime", "number": 14, "default_status": "Backlog"},
        "sync": {
            "issues": True,
            "pull_requests": True,
            "skip_archived": True,
            "link_repositories": True,
        },
        "organizations": [
            {"name": "complytime", "exclude_repos": ["roadmap", "complytime"]},
            {"name": "Agentic-SSDLC"},
        ],
    }
    config.update(overrides)
    return config


class TestLoadAndValidateConfig:
    def test_load_config_reads_yaml(self, tmp_path: Path):
        path = tmp_path / "cfg.yml"
        path.write_text(yaml.safe_dump(_minimal_config()), encoding="utf-8")
        loaded = sync.load_config(path)
        assert loaded["project"]["owner"] == "complytime"
        assert loaded["organizations"][0]["exclude_repos"] == ["roadmap", "complytime"]

    def test_validate_config_accepts_minimal(self):
        assert sync.validate_config(_minimal_config())["project"]["number"] == 14

    @pytest.mark.parametrize(
        "bad",
        [
            None,
            [],
            {"project": {"owner": "x"}},  # missing number + orgs
            {"project": {"owner": "x", "number": 1}, "organizations": []},
            {
                "project": {"owner": "x", "number": 1},
                "organizations": [{"exclude_repos": ["a"]}],
            },
        ],
    )
    def test_validate_config_rejects_invalid(self, bad: Any):
        with pytest.raises(ValueError):
            sync.validate_config(bad)


class TestListOrgRepos:
    def test_filters_exclude_and_archived(self):
        client = MagicMock()
        client.rest_paginate.return_value = [
            {"name": "keep", "archived": False},
            {"name": "roadmap", "archived": False},
            {"name": "old", "archived": True},
        ]
        repos = sync.list_org_repos(
            client, "complytime", exclude={"roadmap"}, skip_archived=True
        )
        assert [r["name"] for r in repos] == ["keep"]
        client.rest_paginate.assert_called_once_with(
            "/orgs/complytime/repos", {"type": "all", "sort": "full_name"}
        )

    def test_includes_archived_when_not_skipped(self):
        client = MagicMock()
        client.rest_paginate.return_value = [
            {"name": "keep", "archived": False},
            {"name": "old", "archived": True},
        ]
        repos = sync.list_org_repos(
            client, "complytime", exclude=set(), skip_archived=False
        )
        assert [r["name"] for r in repos] == ["keep", "old"]


class TestListOpenItems:
    def test_filters_issues_vs_prs(self):
        client = MagicMock()
        client.rest_paginate.return_value = [
            {"number": 1, "title": "issue", "node_id": "I_1"},
            {"number": 2, "title": "pr", "node_id": "PR_2", "pull_request": {}},
        ]
        issues_only = sync.list_open_items(
            client, "org/repo", include_issues=True, include_prs=False
        )
        prs_only = sync.list_open_items(
            client, "org/repo", include_issues=False, include_prs=True
        )
        both = sync.list_open_items(
            client, "org/repo", include_issues=True, include_prs=True
        )
        assert [i["number"] for i in issues_only] == [1]
        assert [i["number"] for i in prs_only] == [2]
        assert [i["number"] for i in both] == [1, 2]


class TestExistingContentIds:
    def test_paginates_until_exhausted(self):
        client = MagicMock()
        client.graphql.side_effect = [
            {
                "node": {
                    "items": {
                        "pageInfo": {"hasNextPage": True, "endCursor": "c1"},
                        "nodes": [
                            {"content": {"id": "I_1"}},
                            {"content": None},
                            {"content": {"id": "PR_2"}},
                        ],
                    }
                }
            },
            {
                "node": {
                    "items": {
                        "pageInfo": {"hasNextPage": False, "endCursor": "c2"},
                        "nodes": [{"content": {"id": "I_3"}}],
                    }
                }
            },
        ]
        ids = sync.existing_content_ids(client, "PROJECT_ID")
        assert ids == {"I_1", "PR_2", "I_3"}
        assert client.graphql.call_count == 2
        assert client.graphql.call_args_list[1].args[1]["cursor"] == "c1"


class TestFormatAndWriteSummary:
    def test_format_summary_includes_counts_and_errors(self):
        stats = sync.SyncStats(
            repos_considered=3,
            repos_linked=1,
            repos_link_skipped=2,
            items_seen=10,
            items_already_on_board=4,
            items_added=5,
            items_failed=1,
            errors=["boom"],
        )
        text = sync.format_summary(stats, dry_run=True)
        assert "dry-run" in text
        assert "**3**" in text
        assert "skipped/already linked: 2" in text
        assert "**5**" in text
        assert "`boom`" in text

    def test_write_summary_appends_step_summary(self, tmp_path: Path, monkeypatch):
        summary_path = tmp_path / "summary.md"
        monkeypatch.setenv("GITHUB_STEP_SUMMARY", str(summary_path))
        stats = sync.SyncStats(repos_considered=1, items_added=2)
        sync.write_summary(stats, dry_run=False)
        written = summary_path.read_text(encoding="utf-8")
        assert "Compliance Automation project sync" in written
        assert "Added: **2**" in written


class TestGitHubClientErrors:
    def _response(
        self,
        status: int,
        text: str = "",
        *,
        json_body: Optional[Any] = None,
        headers: Optional[Dict[str, str]] = None,
        links: Optional[Dict[str, Dict[str, str]]] = None,
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
        client = sync.GitHubClient("token")
        limited = self._response(
            403,
            "API rate limit exceeded",
            headers={"X-RateLimit-Reset": "1"},
        )
        ok = self._response(200, json_body=[{"name": "repo"}])
        with (
            patch.object(client.session, "request", side_effect=[limited, ok]) as req,
            patch.object(sync.time, "sleep") as sleeper,
        ):
            response = client._request("GET", "https://api.github.com/orgs/x/repos")
        assert response is ok
        assert req.call_count == 2
        sleeper.assert_called()

    def test_retries_server_errors(self):
        client = sync.GitHubClient("token")
        server = self._response(500, "nope")
        ok = self._response(200, json_body=[])
        with (
            patch.object(client.session, "request", side_effect=[server, ok]),
            patch.object(sync.time, "sleep") as sleeper,
        ):
            response = client._request("GET", "https://api.github.com/orgs/x/repos")
        assert response is ok
        sleeper.assert_called_once()

    def test_graphql_raises_runtime_error_on_errors_payload(self):
        client = sync.GitHubClient("token")
        ok = self._response(
            200,
            json_body={"errors": [{"message": "forbidden"}]},
        )
        with patch.object(client, "_request", return_value=ok):
            with pytest.raises(RuntimeError, match="GraphQL errors"):
                client.graphql("query { viewer { login } }")


class TestSyncErrorHandling:
    def _project_mocks(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setattr(
            sync,
            "get_project",
            lambda *_a, **_k: ("PROJECT", "STATUS_FIELD", {"Backlog": "OPT"}),
        )
        monkeypatch.setattr(sync, "existing_content_ids", lambda *_a, **_k: set())

    def test_per_org_request_errors_are_recorded(self, monkeypatch: pytest.MonkeyPatch):
        self._project_mocks(monkeypatch)
        client = MagicMock()
        monkeypatch.setattr(
            sync,
            "list_org_repos",
            MagicMock(side_effect=requests.Timeout("slow")),
        )
        stats = sync.sync(_minimal_config(), client, org_filter=set())
        assert stats.errors
        assert "Failed listing repos for" in stats.errors[0]

    def test_programming_errors_are_not_swallowed(self, monkeypatch: pytest.MonkeyPatch):
        self._project_mocks(monkeypatch)
        client = MagicMock()
        monkeypatch.setattr(
            sync,
            "list_org_repos",
            MagicMock(side_effect=TypeError("bug")),
        )
        with pytest.raises(TypeError, match="bug"):
            sync.sync(_minimal_config(), client, org_filter={"complytime"})

    def test_add_item_runtime_error_counts_as_failed(
        self, monkeypatch: pytest.MonkeyPatch
    ):
        self._project_mocks(monkeypatch)
        client = MagicMock(dry_run=False)
        monkeypatch.setattr(
            sync,
            "list_org_repos",
            MagicMock(
                return_value=[
                    {
                        "name": "demo",
                        "full_name": "complytime/demo",
                        "node_id": "R_1",
                        "archived": False,
                    }
                ]
            ),
        )
        monkeypatch.setattr(sync, "link_repository", MagicMock(return_value=True))
        monkeypatch.setattr(
            sync,
            "list_open_items",
            MagicMock(
                return_value=[
                    {"number": 7, "title": "work", "node_id": "I_7"},
                ]
            ),
        )
        monkeypatch.setattr(
            sync,
            "add_item",
            MagicMock(side_effect=RuntimeError("GraphQL errors: boom")),
        )
        stats = sync.sync(
            _minimal_config(),
            client,
            org_filter={"complytime"},
        )
        assert stats.items_failed == 1
        assert stats.items_added == 0
        assert any("Failed adding" in err for err in stats.errors)


class TestLinkRepository:
    def test_dry_run_does_not_call_graphql(self):
        client = MagicMock(dry_run=True)
        assert sync.link_repository(client, "P", "R") is True
        client.graphql.assert_not_called()

    def test_already_linked_is_idempotent(self):
        client = MagicMock(dry_run=False)
        client.graphql.side_effect = RuntimeError("already linked to project")
        assert sync.link_repository(client, "P", "R") is False
