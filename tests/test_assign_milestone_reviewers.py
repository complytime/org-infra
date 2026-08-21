# SPDX-License-Identifier: Apache-2.0

"""Tests for assign-milestone-reviewers.py."""

from __future__ import annotations

import importlib
import sys
from pathlib import Path
from unittest.mock import patch

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

assign = importlib.import_module("assign-milestone-reviewers")

PERIBOLOS = {
    "orgs": {
        "complytime": {
            "teams": {
                "evidence-locker-mvp-reviewers": {
                    "members": ["hbraswelrh", "sedonnel", "trevor-vaughan"],
                    "maintainers": ["gxmiranda", "jpower432", "marcusburghardt"],
                }
            }
        }
    }
}


class TestExtractTeamMembers:
    def test_returns_members_not_maintainers(self):
        members = assign.extract_team_members(
            PERIBOLOS, "complytime", "evidence-locker-mvp-reviewers"
        )
        assert members == ["hbraswelrh", "sedonnel", "trevor-vaughan"]

    def test_missing_team_exits(self):
        with pytest.raises(SystemExit, match="not found"):
            assign.extract_team_members(PERIBOLOS, "complytime", "nope")

    def test_empty_members_exits(self):
        data = {
            "orgs": {
                "complytime": {
                    "teams": {"empty-team": {"members": [], "maintainers": ["gxmiranda"]}}
                }
            }
        }
        with pytest.raises(SystemExit, match="no members"):
            assign.extract_team_members(data, "complytime", "empty-team")


class TestLoginsToAdd:
    def test_skips_author_and_existing_casefold(self):
        result = assign.logins_to_add(
            ["hbraswelrh", "sedonnel", "trevor-vaughan"],
            ["Trevor-Vaughan", "author"],
        )
        assert result == ["hbraswelrh", "sedonnel"]

    def test_preserves_peribolos_order(self):
        result = assign.logins_to_add(["sedonnel", "hbraswelrh"], [])
        assert result == ["sedonnel", "hbraswelrh"]

    def test_empty_when_all_skipped(self):
        result = assign.logins_to_add(["sedonnel"], ["sedonnel"])
        assert result == []


class TestMilestoneMatching:
    def test_normalizes_whitespace_and_case(self):
        titles = assign.matching_titles(["Evidence Locker MVP", "Internal Evidence Locker MVP"])
        matched = assign.matching_milestones(
            [
                {"title": "evidence  locker mvp", "number": 1},
                {"title": "ComplyTime improvements", "number": 2},
                {"title": "Internal Evidence Locker MVP", "number": 3},
            ],
            titles,
        )
        assert [item["number"] for item in matched] == [1, 3]


class TestIsPullRequest:
    def test_issue_without_pull_request_key(self):
        assert assign.is_pull_request({"number": 1}) is False

    def test_pull_request_payload(self):
        assert assign.is_pull_request({"number": 2, "pull_request": {"url": "https://x"}}) is True


class TestProcessItem:
    def test_assigns_issue_and_skips_author(self):
        item = {
            "number": 10,
            "html_url": "https://github.com/complytime/nunya/issues/10",
            "user": {"login": "hbraswelrh"},
            "assignees": [],
        }
        with patch.object(assign, "assign_issue") as mocked:
            message = assign.process_item(
                "token",
                "complytime",
                "nunya",
                item,
                ["hbraswelrh", "sedonnel", "trevor-vaughan"],
                dry_run=False,
            )
        mocked.assert_called_once_with(
            "token", "complytime", "nunya", 10, ["sedonnel", "trevor-vaughan"]
        )
        assert "assign sedonnel, trevor-vaughan" in message

    def test_dry_run_does_not_write_issue(self):
        item = {
            "number": 11,
            "html_url": "https://github.com/complytime/nunya/issues/11",
            "user": {"login": "someone"},
            "assignees": [],
        }
        with patch.object(assign, "assign_issue") as mocked:
            message = assign.process_item(
                "token",
                "complytime",
                "nunya",
                item,
                ["sedonnel"],
                dry_run=True,
            )
        mocked.assert_not_called()
        assert message.startswith("assign")

    def test_requests_pr_reviewers(self):
        item = {
            "number": 12,
            "html_url": "https://github.com/complytime/nunya/pull/12",
            "user": {"login": "author"},
            "pull_request": {"url": "https://api.github.com/repos/complytime/nunya/pulls/12"},
        }
        with patch.object(
            assign, "gh_request", return_value={"users": [{"login": "sedonnel"}]}
        ), patch.object(assign, "request_reviewers") as mocked:
            message = assign.process_item(
                "token",
                "complytime",
                "nunya",
                item,
                ["hbraswelrh", "sedonnel", "trevor-vaughan"],
                dry_run=False,
            )
        mocked.assert_called_once_with(
            "token", "complytime", "nunya", 12, ["hbraswelrh", "trevor-vaughan"]
        )
        assert "request reviewers hbraswelrh, trevor-vaughan" in message

    def test_skips_when_nothing_to_add(self):
        item = {
            "number": 13,
            "html_url": "https://github.com/complytime/nunya/issues/13",
            "user": {"login": "sedonnel"},
            "assignees": [{"login": "hbraswelrh"}, {"login": "trevor-vaughan"}],
        }
        with patch.object(assign, "assign_issue") as mocked:
            message = assign.process_item(
                "token",
                "complytime",
                "nunya",
                item,
                ["hbraswelrh", "sedonnel", "trevor-vaughan"],
                dry_run=False,
            )
        mocked.assert_not_called()
        assert message.startswith("skip")
