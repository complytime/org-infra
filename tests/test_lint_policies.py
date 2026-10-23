# SPDX-License-Identifier: Apache-2.0
"""Regression tests for the lint-policies validation logic.

Validates the jq-based consistency check between policy when.expression
guards and tenets[].predicates.types URLs. Tests exercise the same jq
filter used in the Makefile lint-policies target against temporary
policy fixtures.

Addresses review feedback from PR #686: add automated positive/negative
regression coverage for the when-guard lint.
"""

import json
import shutil
import subprocess
from pathlib import Path
from typing import Any

import pytest

POLICY_DIR = (
    Path(__file__).resolve().parents[1]
    / "compliance"
    / "ampel"
    / "branch-protection"
)

# The jq filter used in the Makefile lint-policies target.
# Extracts single-quoted URLs from when.expression via regex and checks
# that every tenet predicate type URL appears as an exact match.
JQ_FILTER = (
    "[.when.expression "
    "| match(\"'([^']+)'\"; \"g\") "
    "| .captures[0].string] as $expr_urls "
    "| [.tenets[].predicates.types[]] "
    "| unique[] "
    "| select(. as $url | $expr_urls | index($url) | not)"
)

GITHUB_BRANCH_RULES_URL = (
    "http://github.com/carabiner-dev/snappy"
    "/specs/github/branch-rules.yaml"
)
GITLAB_BRANCH_PROTECTION_URL = (
    "http://github.com/carabiner-dev/snappy"
    "/specs/gitlab/branch-protection.yaml"
)
GITLAB_PROJECT_APPROVALS_URL = (
    "http://github.com/carabiner-dev/snappy"
    "/specs/gitlab/project-approvals.yaml"
)


def _make_policy(
    predicate_urls: list[str],
    expression_urls: list[str] | None = None,
) -> dict[str, Any]:
    """Build a minimal policy fixture.

    Args:
        predicate_urls: URLs for tenets[].predicates.types.
        expression_urls: URLs embedded in when.expression.
            Defaults to predicate_urls when None.
    """
    if expression_urls is None:
        expression_urls = predicate_urls

    conditions = " || ".join(
        f"p.predicate_type == '{url}'" for url in expression_urls
    )
    expression = f"predicates.exists(p, {conditions})"

    return {
        "id": "test-policy",
        "when": {"expression": expression},
        "meta": {"description": "test fixture"},
        "tenets": [
            {
                "id": "01",
                "code": "true",
                "predicates": {"types": predicate_urls},
                "assessment": {"message": "ok"},
                "error": {"message": "fail"},
            }
        ],
    }


def _run_jq_filter(policy_path: Path) -> subprocess.CompletedProcess[str]:
    """Run the lint-policies jq filter against a policy file."""
    return subprocess.run(
        ["jq", "-r", JQ_FILTER, str(policy_path)],
        capture_output=True,
        text=True,
        check=False,
    )


def _run_jq_valid(policy_path: Path) -> subprocess.CompletedProcess[str]:
    """Run jq empty to validate JSON syntax."""
    return subprocess.run(
        ["jq", "empty", str(policy_path)],
        capture_output=True,
        text=True,
        check=False,
    )


@pytest.fixture(autouse=True)
def _require_jq() -> None:
    """Skip all tests if jq is not installed."""
    if shutil.which("jq") is None:
        pytest.skip("jq is not installed")


# -- Positive tests -------------------------------------------------------


class TestValidPolicies:
    """Verify that all real policy files pass the lint filter."""

    @pytest.mark.parametrize(
        "policy_file",
        sorted(POLICY_DIR.glob("*.json")),
        ids=lambda p: p.stem,
    )
    def test_real_policy_passes_lint(self, policy_file: Path) -> None:
        """Each committed policy file must pass the when-guard lint."""
        result = _run_jq_filter(policy_file)
        assert result.returncode == 0, (
            f"jq failed on {policy_file.name}: {result.stderr}"
        )
        assert result.stdout.strip() == "", (
            f"{policy_file.name}: predicate types missing from "
            f"when.expression: {result.stdout.strip()}"
        )

    def test_matching_urls_pass(self, tmp_path: Path) -> None:
        """A policy with matching expression and tenet URLs passes."""
        policy = _make_policy([
            GITHUB_BRANCH_RULES_URL,
            GITLAB_BRANCH_PROTECTION_URL,
        ])
        policy_file = tmp_path / "valid.json"
        policy_file.write_text(json.dumps(policy), encoding="utf-8")

        result = _run_jq_filter(policy_file)
        assert result.returncode == 0
        assert result.stdout.strip() == ""


# -- Negative tests --------------------------------------------------------


class TestMissingUrl:
    """Verify that missing predicate-type URLs are detected."""

    def test_missing_url_detected(self, tmp_path: Path) -> None:
        """A tenet URL absent from when.expression is reported."""
        policy = _make_policy(
            predicate_urls=[
                GITHUB_BRANCH_RULES_URL,
                GITLAB_BRANCH_PROTECTION_URL,
            ],
            expression_urls=[GITHUB_BRANCH_RULES_URL],
        )
        policy_file = tmp_path / "missing-url.json"
        policy_file.write_text(json.dumps(policy), encoding="utf-8")

        result = _run_jq_filter(policy_file)
        assert result.returncode == 0
        assert GITLAB_BRANCH_PROTECTION_URL in result.stdout.strip()


class TestSubstringMatching:
    """Regression tests for the substring matching bug (PR #686 issue 2).

    The original jq filter used contains() which is substring-based.
    Appending a suffix to a URL in when.expression still matched the
    shorter tenet URL. The fixed filter uses exact URL extraction and
    index() comparison.
    """

    def test_url_suffix_detected(self, tmp_path: Path) -> None:
        """A URL with an appended suffix must not match the original."""
        policy = _make_policy(
            predicate_urls=[
                GITHUB_BRANCH_RULES_URL,
                GITLAB_BRANCH_PROTECTION_URL,
            ],
            expression_urls=[
                GITHUB_BRANCH_RULES_URL + ".invalid",
                GITLAB_BRANCH_PROTECTION_URL,
            ],
        )
        policy_file = tmp_path / "suffix.json"
        policy_file.write_text(json.dumps(policy), encoding="utf-8")

        result = _run_jq_filter(policy_file)
        assert GITHUB_BRANCH_RULES_URL in result.stdout.strip(), (
            "Suffixed URL should not match the original predicate type"
        )

    def test_url_prefix_sharing_detected(self, tmp_path: Path) -> None:
        """Distinct URLs sharing a common prefix must not cross-match."""
        policy = _make_policy(
            predicate_urls=[
                GITLAB_BRANCH_PROTECTION_URL,
            ],
            expression_urls=[
                GITLAB_PROJECT_APPROVALS_URL,
            ],
        )
        policy_file = tmp_path / "prefix-sharing.json"
        policy_file.write_text(json.dumps(policy), encoding="utf-8")

        result = _run_jq_filter(policy_file)
        assert GITLAB_BRANCH_PROTECTION_URL in result.stdout.strip(), (
            "branch-protection URL must not match project-approvals URL"
        )


class TestMalformedJson:
    """Verify that invalid JSON is rejected."""

    def test_invalid_json_fails(self, tmp_path: Path) -> None:
        """Malformed JSON must cause jq to exit non-zero."""
        policy_file = tmp_path / "malformed.json"
        policy_file.write_text("{invalid json", encoding="utf-8")

        result = _run_jq_valid(policy_file)
        assert result.returncode != 0

    def test_missing_when_key(self, tmp_path: Path) -> None:
        """A policy without a when key has no URLs to extract."""
        policy = {"id": "no-when", "tenets": []}
        policy_file = tmp_path / "no-when.json"
        policy_file.write_text(json.dumps(policy), encoding="utf-8")

        # The Makefile skips files without "when" via has("when") check.
        # The jq filter itself would fail on missing .when.expression,
        # which is expected -- the Makefile guards against this.
        result = subprocess.run(
            ["jq", 'has("when")', str(policy_file)],
            capture_output=True,
            text=True,
            check=False,
        )
        assert result.returncode == 0
        assert result.stdout.strip() == "false"


class TestMakeLintPolicies:
    """Integration test: verify the full make lint-policies target."""

    def test_make_lint_policies_passes(self) -> None:
        """The make lint-policies target must pass on current policies."""
        project_root = Path(__file__).resolve().parents[1]
        result = subprocess.run(
            ["make", "lint-policies"],
            capture_output=True,
            text=True,
            check=False,
            cwd=str(project_root),
        )
        assert result.returncode == 0, (
            f"make lint-policies failed:\n{result.stdout}\n{result.stderr}"
        )
