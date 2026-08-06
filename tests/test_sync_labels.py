# SPDX-License-Identifier: Apache-2.0

"""Tests for sync-labels.py."""

from __future__ import annotations

import importlib
import io
import sys
from pathlib import Path
from unittest.mock import patch

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

sync_labels = importlib.import_module("sync-labels")


class TestNormalize:
    def test_strips_and_casefolds(self):
        assert sync_labels.normalize("  Bug ") == "bug"
        assert sync_labels.normalize("ENHANCEMENT") == "enhancement"


class TestExpandRepoArgs:
    def test_none_returns_none(self):
        assert sync_labels.expand_repo_args(None) is None

    def test_splits_comma_separated_single_arg(self):
        assert sync_labels.expand_repo_args(["complyctl,org-infra"]) == ["complyctl", "org-infra"]

    def test_accepts_space_separated_args(self):
        assert sync_labels.expand_repo_args(["complyctl", "org-infra"]) == ["complyctl", "org-infra"]

    def test_rejects_shell_metacharacters(self):
        with pytest.raises(SystemExit, match="Invalid repo name"):
            sync_labels.expand_repo_args(["complyctl;rm -rf /"])


class TestGhRequestErrors:
    def test_truncates_http_error_body(self):
        long_body = "x" * 800
        error = sync_labels.urllib.error.HTTPError(
            url="https://api.github.com/repos/org/repo/labels",
            code=500,
            msg="Server Error",
            hdrs=None,
            fp=io.BytesIO(long_body.encode("utf-8")),
        )
        with patch.object(sync_labels.urllib.request, "urlopen", side_effect=error):
            with pytest.raises(RuntimeError) as exc_info:
                sync_labels.gh_request("token", "GET", "/repos/org/repo/labels")

        message = str(exc_info.value)
        assert "truncated" in message
        assert len(message) < 800


class TestGhPaginate:
    def test_raises_when_response_is_not_list(self):
        with patch.object(sync_labels, "gh_request", return_value={"message": "nope"}):
            with pytest.raises(TypeError, match="Expected list"):
                sync_labels.gh_paginate("token", "/orgs/complytime/repos")

    def test_collects_pages(self):
        pages = [
            [{"name": "a"}, {"name": "b"}],
            [{"name": "c"}],
            [],
        ]

        with patch.object(sync_labels, "gh_request", side_effect=pages) as mocked:
            items = sync_labels.gh_paginate("token", "/orgs/complytime/repos")

        assert [item["name"] for item in items] == ["a", "b", "c"]
        assert mocked.call_count == 3


class TestListRepos:
    def test_filters_exclude_and_include(self):
        api_repos = [{"name": "keep"}, {"name": "skip"}, {"name": "other"}]

        with patch.object(sync_labels, "gh_paginate", return_value=api_repos):
            repos = sync_labels.list_repos(
                "token",
                "complytime",
                include=["keep", "other"],
                exclude=["skip"],
            )

        assert repos == ["keep", "other"]


class TestEnsureStandardLabels:
    def test_creates_missing_label(self):
        labels_by_norm: dict = {}
        desired = {"name": "bug", "color": "d73a4a", "description": "Something broken"}

        with patch.object(sync_labels, "create_label") as create_label:
            sync_labels.ensure_standard_labels(
                "token",
                "complytime",
                "demo",
                labels_by_norm,
                [desired],
                dry_run=True,
            )

        create_label.assert_called_once()
        assert "bug" in labels_by_norm

    def test_updates_mismatched_label(self):
        labels_by_norm = {
            "bug": {"name": "bug", "color": "000000", "description": "old"},
        }
        desired = {"name": "bug", "color": "d73a4a", "description": "Something broken"}

        with patch.object(sync_labels, "patch_label") as patch_label:
            sync_labels.ensure_standard_labels(
                "token",
                "complytime",
                "demo",
                labels_by_norm,
                [desired],
                dry_run=True,
            )

        patch_label.assert_called_once()


class TestApplyRenameOnlyLabels:
    def test_renames_legacy_label_when_destination_missing(self):
        labels_by_norm = {
            "enhancement": {"name": "enhancement", "color": "a2eeef", "description": "old"},
        }
        rules = [
            {
                "from": ["enhancement"],
                "to": {"name": "type:enhancement", "color": "a2eeef", "description": "new"},
            }
        ]

        with patch.object(sync_labels, "patch_label") as patch_label:
            sync_labels.apply_rename_only_labels(
                "token",
                "complytime",
                "demo",
                labels_by_norm,
                rules,
                dry_run=True,
            )

        patch_label.assert_called_once()
        assert "type:enhancement" in labels_by_norm
        assert "enhancement" not in labels_by_norm


class TestApplyDeletes:
    def test_deletes_matching_label(self):
        labels_by_norm = {
            "stale": {"name": "stale", "color": "ffffff", "description": ""},
        }

        with patch.object(sync_labels, "delete_label") as delete_label:
            sync_labels.apply_deletes(
                "token",
                "complytime",
                "demo",
                labels_by_norm,
                ["stale"],
                dry_run=True,
            )

        delete_label.assert_called_once_with("token", "complytime", "demo", "stale", True)
        assert "stale" not in labels_by_norm

    def test_skips_missing_label(self):
        labels_by_norm: dict = {}

        with patch.object(sync_labels, "delete_label") as delete_label:
            sync_labels.apply_deletes(
                "token",
                "complytime",
                "demo",
                labels_by_norm,
                ["missing"],
                dry_run=True,
            )

        delete_label.assert_not_called()
