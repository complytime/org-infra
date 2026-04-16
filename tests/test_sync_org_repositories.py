# SPDX-License-Identifier: Apache-2.0

"""Tests for sync-org-repositories.py."""

import importlib
import sys
from pathlib import Path
from unittest.mock import patch

import yaml

# Add scripts to path for import
sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

sync_module = importlib.import_module("sync-org-repositories")

GITHUB_API = sync_module.GITHUB_API


class TestValidateGithubApiRequest:
    """Tests for validate_github_api_request."""

    def test_allowed_get_repo(self):
        assert (
            sync_module.validate_github_api_request(f"{GITHUB_API}/repos/org/repo", "GET") is True
        )

    def test_allowed_get_pulls(self):
        assert (
            sync_module.validate_github_api_request(f"{GITHUB_API}/repos/org/repo/pulls", "GET")
            is True
        )

    def test_allowed_post_pulls(self):
        assert (
            sync_module.validate_github_api_request(f"{GITHUB_API}/repos/org/repo/pulls", "POST")
            is True
        )

    def test_allowed_get_contents(self):
        assert (
            sync_module.validate_github_api_request(
                f"{GITHUB_API}/repos/org/repo/contents/.github/dependabot.yml",
                "GET",
            )
            is True
        )

    def test_allowed_get_contents_nested_path(self):
        assert (
            sync_module.validate_github_api_request(
                f"{GITHUB_API}/repos/org/repo/contents/a/b/c.yml", "GET"
            )
            is True
        )

    def test_disallowed_delete_repo(self):
        result = sync_module.validate_github_api_request(f"{GITHUB_API}/repos/org/repo", "DELETE")
        assert not result

    def test_disallowed_post_forks(self):
        result = sync_module.validate_github_api_request(
            f"{GITHUB_API}/repos/org/repo/forks", "POST"
        )
        assert not result

    def test_disallowed_arbitrary_endpoint(self):
        result = sync_module.validate_github_api_request(f"{GITHUB_API}/orgs/org/members", "GET")
        assert not result

    def test_disallowed_post_to_get_only_endpoint(self):
        result = sync_module.validate_github_api_request(f"{GITHUB_API}/repos/org/repo", "POST")
        assert not result

    def test_disallowed_delete_branch_ref(self):
        result = sync_module.validate_github_api_request(
            f"{GITHUB_API}/repos/org/repo/git/refs/heads/main", "DELETE"
        )
        assert not result

    def test_disallowed_get_user(self):
        result = sync_module.validate_github_api_request(f"{GITHUB_API}/user", "GET")
        assert not result

    def test_disallowed_get_app(self):
        result = sync_module.validate_github_api_request(f"{GITHUB_API}/app", "GET")
        assert not result


class TestValidateBranchName:
    """Tests for validate_branch_name."""

    def test_valid_prefix(self):
        assert sync_module.validate_branch_name("sync-repo-standards-20260416120000") is True

    def test_valid_prefix_minimal(self):
        assert sync_module.validate_branch_name("sync-repo-standards-x") is True

    def test_invalid_prefix(self):
        assert sync_module.validate_branch_name("feature/my-branch") is False

    def test_main_rejected(self):
        assert sync_module.validate_branch_name("main") is False

    def test_empty_string_rejected(self):
        assert sync_module.validate_branch_name("") is False

    def test_partial_prefix_rejected(self):
        assert sync_module.validate_branch_name("sync-repo-") is False


class TestGenerateDependabotConfig:
    """Tests for generate_dependabot_config."""

    def _make_config(self, common=None, overrides=None, exclude=None):
        """Build a minimal sync config with dependabot section."""
        dependabot = {}
        if common is not None:
            dependabot["common"] = common
        if overrides is not None:
            dependabot["overrides"] = overrides
        if exclude is not None:
            dependabot["exclude_repos"] = exclude
        return {"dependabot": dependabot}

    def test_common_only(self):
        common = [
            {"package-ecosystem": "github-actions", "directory": "/"},
            {"package-ecosystem": "pre-commit", "directory": "/"},
        ]
        config = self._make_config(common=common)
        result = sync_module.generate_dependabot_config("my-repo", config)
        assert len(result) == 2
        ecosystems = [e["package-ecosystem"] for e in result]
        assert "github-actions" in ecosystems
        assert "pre-commit" in ecosystems

    def test_override_adds_ecosystem(self):
        common = [
            {"package-ecosystem": "github-actions", "directory": "/"},
        ]
        overrides = {
            "my-repo": [
                {"package-ecosystem": "gomod", "directory": "/"},
            ],
        }
        config = self._make_config(common=common, overrides=overrides)
        result = sync_module.generate_dependabot_config("my-repo", config)
        assert len(result) == 2
        ecosystems = [e["package-ecosystem"] for e in result]
        assert "github-actions" in ecosystems
        assert "gomod" in ecosystems

    def test_override_replaces_common_for_same_ecosystem(self):
        common = [
            {
                "package-ecosystem": "github-actions",
                "directory": "/",
                "schedule": {"interval": "daily"},
            },
        ]
        overrides = {
            "my-repo": [
                {
                    "package-ecosystem": "github-actions",
                    "directories": ["/", "/.github/actions/custom"],
                    "schedule": {"interval": "weekly"},
                },
            ],
        }
        config = self._make_config(common=common, overrides=overrides)
        result = sync_module.generate_dependabot_config("my-repo", config)
        assert len(result) == 1
        entry = result[0]
        assert entry["package-ecosystem"] == "github-actions"
        assert entry["directories"] == ["/", "/.github/actions/custom"]
        assert entry["schedule"]["interval"] == "weekly"

    def test_excluded_repo_returns_none(self):
        common = [
            {"package-ecosystem": "github-actions", "directory": "/"},
        ]
        config = self._make_config(common=common, exclude=["excluded-repo"])
        result = sync_module.generate_dependabot_config("excluded-repo", config)
        assert result is None

    def test_no_override_for_repo(self):
        common = [
            {"package-ecosystem": "github-actions", "directory": "/"},
        ]
        overrides = {
            "other-repo": [
                {"package-ecosystem": "gomod", "directory": "/"},
            ],
        }
        config = self._make_config(common=common, overrides=overrides)
        result = sync_module.generate_dependabot_config("my-repo", config)
        assert len(result) == 1
        assert result[0]["package-ecosystem"] == "github-actions"

    def test_no_dependabot_section_returns_none(self):
        config = {}
        result = sync_module.generate_dependabot_config("my-repo", config)
        assert result is None


class TestMergeDependabotEntries:
    """Tests for merge_dependabot_entries."""

    def test_no_existing_file(self, tmp_path):
        managed = [
            {"package-ecosystem": "github-actions", "directory": "/"},
        ]
        nonexistent = str(tmp_path / "missing.yml")
        result = sync_module.merge_dependabot_entries(managed, nonexistent)
        parsed = yaml.safe_load(result)
        assert parsed["version"] == 2
        assert len(parsed["updates"]) == 1
        assert parsed["updates"][0]["package-ecosystem"] == "github-actions"

    def test_unmanaged_entries_preserved(self, tmp_path):
        managed = [
            {"package-ecosystem": "github-actions", "directory": "/"},
        ]
        existing = {
            "version": 2,
            "updates": [
                {"package-ecosystem": "github-actions", "directory": "/"},
                {"package-ecosystem": "docker", "directory": "/"},
            ],
        }
        existing_path = tmp_path / "dependabot.yml"
        existing_path.write_text(yaml.dump(existing))

        result = sync_module.merge_dependabot_entries(managed, str(existing_path))
        parsed = yaml.safe_load(result)
        assert len(parsed["updates"]) == 2
        ecosystems = [e["package-ecosystem"] for e in parsed["updates"]]
        assert "github-actions" in ecosystems
        assert "docker" in ecosystems

    def test_managed_replaces_existing(self, tmp_path):
        managed = [
            {
                "package-ecosystem": "gomod",
                "directories": ["/", "/submod"],
                "schedule": {"interval": "weekly"},
            },
        ]
        existing = {
            "version": 2,
            "updates": [
                {
                    "package-ecosystem": "gomod",
                    "directory": "/",
                    "schedule": {"interval": "daily"},
                },
            ],
        }
        existing_path = tmp_path / "dependabot.yml"
        existing_path.write_text(yaml.dump(existing))

        result = sync_module.merge_dependabot_entries(managed, str(existing_path))
        parsed = yaml.safe_load(result)
        assert len(parsed["updates"]) == 1
        entry = parsed["updates"][0]
        assert entry["directories"] == ["/", "/submod"]
        assert entry["schedule"]["interval"] == "weekly"

    def test_all_unmanaged_preserved_when_no_overlap(self, tmp_path):
        managed = [
            {"package-ecosystem": "github-actions", "directory": "/"},
        ]
        existing = {
            "version": 2,
            "updates": [
                {"package-ecosystem": "docker", "directory": "/"},
                {"package-ecosystem": "npm", "directory": "/frontend"},
            ],
        }
        existing_path = tmp_path / "dependabot.yml"
        existing_path.write_text(yaml.dump(existing))

        result = sync_module.merge_dependabot_entries(managed, str(existing_path))
        parsed = yaml.safe_load(result)
        assert len(parsed["updates"]) == 3
        ecosystems = [e["package-ecosystem"] for e in parsed["updates"]]
        assert ecosystems == ["github-actions", "docker", "npm"]


class TestCheckExistingSyncPr:
    """Tests for check_existing_sync_pr."""

    @patch.object(sync_module, "github_api_request")
    def test_no_existing_pr(self, mock_api):
        mock_api.return_value = (200, [])
        result = sync_module.check_existing_sync_pr("org", "repo")
        assert result is None

    @patch.object(sync_module, "github_api_request")
    def test_existing_pr_found(self, mock_api):
        mock_api.return_value = (
            200,
            [
                {
                    "title": "chore: sync repository standards",
                    "html_url": "https://github.com/org/repo/pull/42",
                },
            ],
        )
        result = sync_module.check_existing_sync_pr("org", "repo")
        assert result == "https://github.com/org/repo/pull/42"

    @patch.object(sync_module, "github_api_request")
    def test_non_matching_pr_ignored(self, mock_api):
        mock_api.return_value = (
            200,
            [
                {
                    "title": "feat: add new feature",
                    "html_url": "https://github.com/org/repo/pull/1",
                },
            ],
        )
        result = sync_module.check_existing_sync_pr("org", "repo")
        assert result is None

    @patch.object(sync_module, "github_api_request")
    def test_api_failure_returns_none(self, mock_api):
        mock_api.return_value = (500, {"error": "internal"})
        result = sync_module.check_existing_sync_pr("org", "repo")
        assert result is None


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

    def test_dependabot_section_present(self):
        config = sync_module.load_sync_config("sync-config.yml")
        assert "dependabot" in config
        dependabot = config["dependabot"]
        assert "common" in dependabot
        assert "overrides" in dependabot
        assert len(dependabot["common"]) > 0


class TestExtractRepositories:
    """Tests for extract_repositories."""

    def test_extracts_repos(self):
        data = {
            "orgs": {
                "testorg": {"repos": {"repo1": {}, "repo2": {}}},
            },
        }
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
