# SPDX-License-Identifier: Apache-2.0

"""Tests for sync-org-repositories.py."""

import importlib
import sys
from pathlib import Path

import pytest

# Add scripts to path for import
sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

sync_module = importlib.import_module("sync-org-repositories")

GITHUB_API = sync_module.GITHUB_API


class TestValidateGithubApiRequest:
    """Tests for validate_github_api_request."""

    def test_allowed_get_user(self):
        assert sync_module.validate_github_api_request(
            f"{GITHUB_API}/user", "GET"
        ) is True

    def test_allowed_get_app(self):
        assert sync_module.validate_github_api_request(
            f"{GITHUB_API}/app", "GET"
        ) is True

    def test_allowed_get_repo(self):
        assert sync_module.validate_github_api_request(
            f"{GITHUB_API}/repos/org/repo", "GET"
        ) is True

    def test_allowed_post_forks(self):
        assert sync_module.validate_github_api_request(
            f"{GITHUB_API}/repos/org/repo/forks", "POST"
        ) is True

    def test_allowed_post_pulls(self):
        assert sync_module.validate_github_api_request(
            f"{GITHUB_API}/repos/org/repo/pulls", "POST"
        ) is True

    def test_allowed_delete_branch_ref(self):
        assert sync_module.validate_github_api_request(
            f"{GITHUB_API}/repos/org/repo/git/refs/heads/my-branch", "DELETE"
        ) is True

    def test_disallowed_delete_repo(self):
        result = sync_module.validate_github_api_request(
            f"{GITHUB_API}/repos/org/repo", "DELETE"
        )
        assert not result

    def test_disallowed_wrong_method_for_user(self):
        result = sync_module.validate_github_api_request(
            f"{GITHUB_API}/user", "DELETE"
        )
        assert not result

    def test_disallowed_arbitrary_endpoint(self):
        result = sync_module.validate_github_api_request(
            f"{GITHUB_API}/orgs/org/members", "GET"
        )
        assert not result

    def test_disallowed_post_to_get_only_endpoint(self):
        result = sync_module.validate_github_api_request(
            f"{GITHUB_API}/user", "POST"
        )
        assert not result


class TestCompareFiles:
    """Tests for compare_files."""

    def test_identical_files(self, tmp_path):
        f1 = tmp_path / "a.txt"
        f2 = tmp_path / "b.txt"
        f1.write_text("hello")
        f2.write_text("hello")
        assert sync_module.compare_files(str(f1), str(f2)) is True

    def test_different_files(self, tmp_path):
        f1 = tmp_path / "a.txt"
        f2 = tmp_path / "b.txt"
        f1.write_text("hello")
        f2.write_text("world")
        assert sync_module.compare_files(str(f1), str(f2)) is False

    def test_missing_dest_file(self, tmp_path):
        f1 = tmp_path / "a.txt"
        f1.write_text("hello")
        assert sync_module.compare_files(str(f1), str(tmp_path / "missing.txt")) is False


class TestSyncFile:
    """Tests for sync_file."""

    def test_copies_missing_file(self, tmp_path):
        src = tmp_path / "src" / "file.yml"
        src.parent.mkdir()
        src.write_text("content")
        dest = tmp_path / "dest" / "file.yml"
        result = sync_module.sync_file(str(src), str(dest), "file.yml")
        assert result is True
        assert dest.read_text() == "content"

    def test_skips_identical_file(self, tmp_path):
        src = tmp_path / "src.yml"
        dest = tmp_path / "dest.yml"
        src.write_text("same")
        dest.write_text("same")
        result = sync_module.sync_file(str(src), str(dest), "file.yml")
        assert result is False

    def test_updates_different_file(self, tmp_path):
        src = tmp_path / "src.yml"
        dest = tmp_path / "dest.yml"
        src.write_text("new")
        dest.write_text("old")
        result = sync_module.sync_file(str(src), str(dest), "file.yml")
        assert result is True
        assert dest.read_text() == "new"


class TestLoadSyncConfig:
    """Tests for load_sync_config."""

    def test_loads_valid_config(self):
        config = sync_module.load_sync_config("sync-config.yml")
        assert "files_to_sync" in config
        assert "exclude_repos" in config

    def test_exclude_repos_contains_org_infra(self):
        config = sync_module.load_sync_config("sync-config.yml")
        assert "org-infra" in config["exclude_repos"]


class TestExtractRepositories:
    """Tests for extract_repositories."""

    def test_extracts_repos(self):
        data = {"orgs": {"testorg": {"repos": {"repo1": {}, "repo2": {}}}}}
        repos = sync_module.extract_repositories(data, "testorg")
        assert sorted(repos) == ["repo1", "repo2"]

    def test_empty_org(self):
        data = {"orgs": {"testorg": {}}}
        repos = sync_module.extract_repositories(data, "testorg")
        assert repos == []

    def test_missing_org(self):
        data = {"orgs": {"other": {"repos": {"repo1": {}}}}}
        repos = sync_module.extract_repositories(data, "testorg")
        assert repos == []
