# SPDX-License-Identifier: Apache-2.0
"""Contract and logic-mirror tests for the reusable Dependabot reviewer.

Validates structural contracts (permissions, outputs, action pins, step
ordering) by parsing the workflow YAML, and mirrors inline bash logic as
Python functions with parametrized test cases.

IMPORTANT: Mirror functions replicate the bash logic in
``.github/workflows/reusable_dependabot_reviewer.yml``. If the bash
implementation changes, the corresponding mirror MUST be updated to
match. Line references are from the branch ``opsx/dependabot-org-precedent``.
"""

import re
from pathlib import Path
from typing import Any

import pytest
import yaml

from tests.conftest import GitHubActionsLoader

WORKFLOW_PATH = (
    Path(__file__).resolve().parents[1]
    / ".github"
    / "workflows"
    / "reusable_dependabot_reviewer.yml"
)
JOB_NAME = "dependabot_review"

EXPECTED_OUTPUTS = {
    "risk_level",
    "updates_count",
    "dep_name",
    "dep_version",
    "release_age_hours",
    "is_org_owned",
    "org_precedent",
    "precedent_detail",
}


@pytest.fixture
def workflow() -> dict[str, Any]:
    """Parse the reusable Dependabot reviewer workflow."""
    with WORKFLOW_PATH.open(encoding="utf-8") as f:
        return yaml.load(f, Loader=GitHubActionsLoader)


@pytest.fixture
def job(workflow: dict[str, Any]) -> dict[str, Any]:
    """Extract the dependabot_review job."""
    return workflow["jobs"][JOB_NAME]


@pytest.fixture
def steps(job: dict[str, Any]) -> list[dict[str, Any]]:
    """Extract the job steps."""
    return job["steps"]


# ── YAML Contract Tests ────────────────────────────────────────────


class TestWorkflowContract:
    """Structural contract tests for reusable_dependabot_reviewer.yml."""

    def test_workflow_permissions_are_read_only(
        self, workflow: dict[str, Any],
    ) -> None:
        """Workflow must declare minimal read-only permissions."""
        assert workflow["permissions"] == {
            "contents": "read",
            "issues": "none",
            "pull-requests": "none",
        }

    def test_no_write_permissions_anywhere(
        self, workflow: dict[str, Any],
    ) -> None:
        """No permission value in the workflow may be 'write'."""
        for _scope, level in workflow["permissions"].items():
            assert level != "write", (
                f"Write permission found: {_scope}={level}"
            )

    def test_job_runs_only_for_dependabot_prs(
        self, job: dict[str, Any],
    ) -> None:
        """Job if-guard must restrict to dependabot[bot] PRs."""
        condition = job.get("if", "")
        assert "dependabot[bot]" in condition

    def test_all_action_refs_are_sha_pinned(
        self, steps: list[dict[str, Any]],
    ) -> None:
        """Every uses: reference must be a 40-char SHA."""
        for step in steps:
            uses = step.get("uses")
            if uses is None:
                continue
            assert re.match(r"^[^@]+@[0-9a-f]{40}", uses), (
                f"Action ref not SHA-pinned: {uses}"
            )

    def test_checkout_does_not_persist_credentials(
        self, steps: list[dict[str, Any]],
    ) -> None:
        """Checkout step must set persist-credentials: false."""
        checkout = [
            s for s in steps
            if "checkout" in s.get("uses", "").lower()
        ]
        assert len(checkout) == 1
        assert checkout[0].get("with", {}).get(
            "persist-credentials",
        ) is False

    def test_all_eight_outputs_declared_at_workflow_level(
        self, workflow: dict[str, Any],
    ) -> None:
        """workflow_call must declare all 8 outputs."""
        outputs = workflow["on"]["workflow_call"]["outputs"]
        assert set(outputs.keys()) == EXPECTED_OUTPUTS

    def test_all_eight_outputs_declared_at_job_level(
        self, job: dict[str, Any],
    ) -> None:
        """The job must declare all 8 outputs."""
        assert set(job["outputs"].keys()) == EXPECTED_OUTPUTS

    def test_output_wiring_job_to_workflow(
        self, workflow: dict[str, Any], job: dict[str, Any],
    ) -> None:
        """Each workflow output must reference the job output."""
        wf_outputs = workflow["on"]["workflow_call"]["outputs"]
        job_outputs = job["outputs"]
        for key in EXPECTED_OUTPUTS:
            wf_value = wf_outputs[key]["value"]
            assert f"jobs.{JOB_NAME}.outputs.{key}" in wf_value, (
                f"Workflow output '{key}' does not reference "
                f"job output: {wf_value}"
            )
            job_value = job_outputs[key]
            assert f".outputs.{key}" in job_value, (
                f"Job output '{key}' does not reference "
                f"step output: {job_value}"
            )

    def test_precedent_step_after_popularity_step(
        self, steps: list[dict[str, Any]],
    ) -> None:
        """Check Org Precedent must come after Search GitHub."""
        names = [s.get("name", "") for s in steps]
        pop_idx = [
            i for i, n in enumerate(names)
            if "Search GitHub" in n
        ]
        prec_idx = [
            i for i, n in enumerate(names)
            if "Check Org Precedent" in n
        ]
        assert len(pop_idx) == 1, "Expected one popularity step"
        assert len(prec_idx) == 1, "Expected one precedent step"
        assert prec_idx[0] > pop_idx[0]

    def test_precedent_step_uses_only_github_token(
        self, steps: list[dict[str, Any]],
    ) -> None:
        """Precedent step must only reference secrets.GITHUB_TOKEN."""
        prec_steps = [
            s for s in steps
            if "Check Org Precedent" in s.get("name", "")
        ]
        assert len(prec_steps) == 1
        env = prec_steps[0].get("env", {})
        for var_name, var_value in env.items():
            if "secrets." in str(var_value):
                assert "secrets.GITHUB_TOKEN" in str(var_value), (
                    f"Precedent step references non-GITHUB_TOKEN "
                    f"secret in {var_name}: {var_value}"
                )


# ── Logic Mirror Tests ─────────────────────────────────────────────


class TestDepNameExtraction:
    """Mirrors dep_name extraction from Get Dependency Information step.

    Source 1 (lines 78-84): commit metadata ``dependency-name:`` field.
    Source 2 (lines 87-92): title fallback via Bump/Update regex.
    """

    @staticmethod
    def extract_dep_name(
        commit_body: str, commit_subject: str,
    ) -> str:
        """Mirror: lines 78-92 of reusable_dependabot_reviewer.yml."""
        dep_name = ""

        # Source 1: commit metadata
        for line in commit_body.splitlines():
            if "dependency-name:" in line:
                dep_name = line.split("dependency-name:")[-1].strip()
                break

        # Source 2: title fallback (only if Source 1 empty)
        if not dep_name:
            m = re.search(
                r"[Bb]ump\s+(\S+)\s", commit_subject,
            )
            if not m:
                m = re.search(
                    r"[Uu]pdate\s+(\S+)\s", commit_subject,
                )
            if m:
                candidate = m.group(1)
                if candidate != commit_subject:
                    dep_name = candidate

        return dep_name

    def test_metadata_present(self):
        body = "...\ndependency-name: actions/checkout\n..."
        assert self.extract_dep_name(body, "") == "actions/checkout"

    def test_metadata_with_extra_spaces(self):
        body = "dependency-name:  actions/checkout "
        assert self.extract_dep_name(body, "") == "actions/checkout"

    def test_bump_title_fallback(self):
        subj = "Bump actions/checkout from 3.0.0 to 4.0.0"
        assert self.extract_dep_name("", subj) == "actions/checkout"

    def test_update_title_fallback(self):
        subj = "Update golang.org/x/text requirement from 0.1 to 0.2"
        assert self.extract_dep_name("", subj) == "golang.org/x/text"

    def test_no_match_in_title(self):
        subj = "Fix CI pipeline"
        assert self.extract_dep_name("", subj) == ""

    def test_both_empty(self):
        assert self.extract_dep_name("", "") == ""

    def test_metadata_takes_priority_over_title(self):
        body = "dependency-name: pkg-from-metadata"
        subj = "Bump pkg-from-title from 1.0 to 2.0"
        assert self.extract_dep_name(body, subj) == "pkg-from-metadata"


class TestVersionExtraction:
    """Mirrors version extraction from Get Dependency Information step.

    Source 1 (lines 95-101): commit subject semver regex.
    Source 2b (lines 105-112): commit body ``from vX to vY`` regex.
    Source 2c (lines 115-121): PR title semver regex.
    """

    VERSION_RE = re.compile(r"v?(\d+\.\d+\.\d+)")
    BODY_FROM_TO_RE = re.compile(
        r"from\s+v?(\d+\.\d+\.\d+)\s+to\s+v?(\d+\.\d+\.\d+)",
    )

    @classmethod
    def extract_versions(
        cls,
        commit_subject: str,
        commit_body: str = "",
        pr_title: str = "",
    ) -> tuple[str, str]:
        """Mirror: lines 95-121 of reusable_dependabot_reviewer.yml.

        Returns (from_version, to_version).
        """
        from_version = ""
        to_version = ""

        # Source 1: commit subject
        versions = cls.VERSION_RE.findall(commit_subject)[:2]
        if len(versions) >= 2:
            from_version = versions[0]
            to_version = versions[1]
        elif len(versions) == 1:
            to_version = versions[0]

        # Source 2b: commit body fallback (only if < 2 from subject)
        if len(versions) < 2:
            m = cls.BODY_FROM_TO_RE.search(commit_body)
            if m:
                from_version = m.group(1)
                if not to_version:
                    to_version = m.group(2)

        # Source 2c: PR title fallback (only if < 2 from previous)
        if len(versions) < 2 and pr_title:
            title_versions = cls.VERSION_RE.findall(pr_title)[:2]
            if len(title_versions) >= 2:
                from_version = title_versions[0]
                if not to_version:
                    to_version = title_versions[1]

        return from_version, to_version

    def test_subject_two_versions(self):
        assert self.extract_versions(
            "Bump X from 1.2.3 to 4.5.6",
        ) == ("1.2.3", "4.5.6")

    def test_subject_v_prefix_stripped(self):
        assert self.extract_versions(
            "Bump X from v1.2.3 to v4.5.6",
        ) == ("1.2.3", "4.5.6")

    def test_subject_one_version(self):
        assert self.extract_versions("Bump X to 4.5.6") == ("", "4.5.6")

    def test_body_fallback_grouped_pr(self):
        assert self.extract_versions(
            "Bump multiple deps",
            commit_body="Updates from 1.0.0 to 2.0.0",
        ) == ("1.0.0", "2.0.0")

    def test_pr_title_fallback(self):
        assert self.extract_versions(
            "No versions here",
            commit_body="",
            pr_title="Bump X from 1.0.0 to 2.0.0",
        ) == ("1.0.0", "2.0.0")

    def test_no_versions_anywhere(self):
        assert self.extract_versions("Fix CI", "", "") == ("", "")

    def test_large_version_numbers(self):
        assert self.extract_versions(
            "Bump X from v10.20.30 to v11.21.31",
        ) == ("10.20.30", "11.21.31")

    def test_subject_wins_over_body(self):
        assert self.extract_versions(
            "Bump X from 1.0.0 to 2.0.0",
            commit_body="from 3.0.0 to 4.0.0",
        ) == ("1.0.0", "2.0.0")


class TestDepVersionCoalesce:
    """Mirrors dep_version_final coalesce (line 149).

    ``dep_version_final="${dep_version:-$to_version}"``
    """

    @staticmethod
    def coalesce(dep_version: str, to_version: str) -> str:
        """Mirror: bash ``${dep_version:-$to_version}``."""
        return dep_version if dep_version else to_version

    def test_metadata_present(self):
        assert self.coalesce("1.2.3", "4.5.6") == "1.2.3"

    def test_metadata_empty_uses_to(self):
        assert self.coalesce("", "4.5.6") == "4.5.6"

    def test_both_empty(self):
        assert self.coalesce("", "") == ""


class TestUpdateTypeDerivation:
    """Mirrors update_type derivation from versions (lines 123-137)."""

    @staticmethod
    def derive_update_type(
        from_version: str, to_version: str,
    ) -> str:
        """Mirror: lines 124-137 of reusable_dependabot_reviewer.yml."""
        if not from_version or not to_version:
            return ""
        from_parts = from_version.split(".")
        to_parts = to_version.split(".")
        if from_parts[0] != to_parts[0]:
            return "version-update:semver-major"
        if from_parts[1] != to_parts[1]:
            return "version-update:semver-minor"
        return "version-update:semver-patch"

    @pytest.mark.parametrize(
        "from_v,to_v,expected",
        [
            ("1.0.0", "1.0.1", "version-update:semver-patch"),
            ("1.0.0", "1.1.0", "version-update:semver-minor"),
            ("1.0.0", "2.0.0", "version-update:semver-major"),
            ("1.2.3", "2.0.0", "version-update:semver-major"),
            ("1.0.0", "1.1.1", "version-update:semver-minor"),
            ("1.0.0", "1.0.0", "version-update:semver-patch"),
        ],
        ids=[
            "patch", "minor", "major",
            "major-with-minor-change",
            "minor-with-patch-change",
            "same-version",
        ],
    )
    def test_derivation(self, from_v, to_v, expected):
        assert self.derive_update_type(from_v, to_v) == expected

    def test_empty_from_returns_empty(self):
        assert self.derive_update_type("", "1.0.0") == ""

    def test_empty_to_returns_empty(self):
        assert self.derive_update_type("1.0.0", "") == ""


class TestRiskClassification:
    """Mirrors Classify Risk Based on Semantic Version step (lines 196-227).

    Two-tier logic: metadata update_type first, then version comparison.
    """

    @staticmethod
    def classify_risk(
        update_type: str,
        from_version: str = "",
        to_version: str = "",
    ) -> str:
        """Mirror: lines 200-227 of reusable_dependabot_reviewer.yml."""
        if update_type:
            if "semver-patch" in update_type:
                return "low"
            if "semver-minor" in update_type:
                return "medium"
            if "semver-major" in update_type:
                return "high"
        elif from_version and to_version:
            f_parts = from_version.split(".")
            t_parts = to_version.split(".")
            f_major, f_minor = int(f_parts[0]), int(f_parts[1])
            t_major, t_minor = int(t_parts[0]), int(t_parts[1])
            if f_major == t_major and f_minor == t_minor:
                return "low"
            if f_major == t_major and f_minor < t_minor:
                return "medium"
            return "high"
        return "high"

    @pytest.mark.parametrize(
        "update_type,expected",
        [
            ("version-update:semver-patch", "low"),
            ("version-update:semver-minor", "medium"),
            ("version-update:semver-major", "high"),
        ],
        ids=["metadata-patch", "metadata-minor", "metadata-major"],
    )
    def test_from_metadata(self, update_type, expected):
        assert self.classify_risk(update_type) == expected

    @pytest.mark.parametrize(
        "from_v,to_v,expected",
        [
            ("1.0.0", "1.0.1", "low"),
            ("1.0.0", "1.1.0", "medium"),
            ("1.0.0", "2.0.0", "high"),
        ],
        ids=["fallback-patch", "fallback-minor", "fallback-major"],
    )
    def test_from_version_fallback(self, from_v, to_v, expected):
        assert self.classify_risk("", from_v, to_v) == expected

    def test_no_info_defaults_high(self):
        assert self.classify_risk("") == "high"


class TestOrgOwnershipDetection:
    """Mirrors Detect Org Ownership step (lines 165-194).

    ``dep_owner="$(echo "$dep" | cut -d'/' -f1)"``
    """

    @staticmethod
    def detect_org_ownership(
        dep_name: str, repo_owner: str,
    ) -> bool:
        """Mirror: lines 171-194 of reusable_dependabot_reviewer.yml."""
        if not dep_name:
            return False
        dep_owner = dep_name.split("/")[0]
        return dep_owner == repo_owner

    @pytest.mark.parametrize(
        "dep,owner,expected",
        [
            ("complytime/complyctl", "complytime", True),
            ("actions/checkout", "complytime", False),
            ("", "complytime", False),
            ("somepkg", "somepkg", True),
            ("other/repo", "complytime", False),
        ],
        ids=[
            "same-org", "different-org", "empty-dep",
            "no-slash-matches", "explicit-mismatch",
        ],
    )
    def test_ownership(self, dep, owner, expected):
        assert self.detect_org_ownership(dep, owner) is expected


class TestEcosystemDetection:
    """Mirrors Detect Ecosystem step (lines 233-255).

    Checks changed file list for known ecosystem indicators.
    """

    @staticmethod
    def detect_ecosystem(changed_files: str) -> str:
        """Mirror: lines 239-252 of reusable_dependabot_reviewer.yml."""
        if "go.mod" in changed_files:
            return "go"
        if any(
            f in changed_files
            for f in (
                "requirements.txt", "pyproject.toml",
                "setup.cfg", "poetry.lock",
            )
        ):
            return "python"
        if (
            ".github/workflows/" in changed_files
            or ".github/actions/" in changed_files
        ):
            return "github_actions"
        return "unknown"

    @pytest.mark.parametrize(
        "files,expected",
        [
            ("go.mod go.sum", "go"),
            ("requirements.txt", "python"),
            ("pyproject.toml", "python"),
            ("setup.cfg", "python"),
            ("poetry.lock", "python"),
            (".github/workflows/ci.yml", "github_actions"),
            (".github/actions/my-action", "github_actions"),
            ("README.md", "unknown"),
            ("go.mod .github/workflows/ci.yml", "go"),
        ],
        ids=[
            "go", "python-requirements", "python-pyproject",
            "python-setup-cfg", "python-poetry",
            "actions-workflows", "actions-custom",
            "unknown", "go-takes-priority",
        ],
    )
    def test_detection(self, files, expected):
        assert self.detect_ecosystem(files) == expected


class TestReleaseAgeCalculation:
    """Mirrors release age arithmetic (lines 303-317).

    ``age_hours=$(( (now_epoch - release_epoch) / 3600 ))``
    """

    @staticmethod
    def calculate_age_hours(
        release_epoch: int, now_epoch: int,
    ) -> int:
        """Mirror: line 307 of reusable_dependabot_reviewer.yml."""
        return (now_epoch - release_epoch) // 3600

    @pytest.mark.parametrize(
        "release,now,expected",
        [
            (1000000, 1086400, 24),
            (1000000, 1003600, 1),
            (1000000, 1000000, 0),
            (1000000, 1360000, 100),
            (1000000, 1005399, 1),
        ],
        ids=[
            "exactly-24h", "1-hour", "zero-hours",
            "100-hours", "truncation-1h29m",
        ],
    )
    def test_age(self, release, now, expected):
        assert self.calculate_age_hours(release, now) == expected


class TestOrgPrecedentHumanApproval:
    """Mirrors the jq expression for human approval verification (line 462).

    ``[.[] | select(.state == "APPROVED" and .user.type != "Bot")]
     [0].user.login``
    """

    @staticmethod
    def find_human_reviewer(
        reviews: list[dict[str, Any]],
    ) -> str | None:
        """Mirror: jq expression at line 462."""
        approved = [
            r for r in reviews
            if (
                r.get("state") == "APPROVED"
                and r.get("user", {}).get("type") != "Bot"
            )
        ]
        if not approved:
            return None
        login = approved[0].get("user", {}).get("login")
        return login if login else None

    def test_single_human_approval(self):
        reviews = [
            {"state": "APPROVED",
             "user": {"login": "alice", "type": "User"}},
        ]
        assert self.find_human_reviewer(reviews) == "alice"

    def test_bot_only_returns_none(self):
        reviews = [
            {"state": "APPROVED",
             "user": {"login": "mybot", "type": "Bot"}},
        ]
        assert self.find_human_reviewer(reviews) is None

    def test_empty_reviews_returns_none(self):
        assert self.find_human_reviewer([]) is None

    def test_mixed_bot_and_human_returns_first_human(self):
        reviews = [
            {"state": "APPROVED",
             "user": {"login": "autobot", "type": "Bot"}},
            {"state": "APPROVED",
             "user": {"login": "alice", "type": "User"}},
            {"state": "APPROVED",
             "user": {"login": "bob", "type": "User"}},
        ]
        assert self.find_human_reviewer(reviews) == "alice"

    def test_non_approved_human_returns_none(self):
        reviews = [
            {"state": "CHANGES_REQUESTED",
             "user": {"login": "alice", "type": "User"}},
        ]
        assert self.find_human_reviewer(reviews) is None

    def test_approved_bot_plus_non_approved_human(self):
        reviews = [
            {"state": "APPROVED",
             "user": {"login": "bot", "type": "Bot"}},
            {"state": "COMMENTED",
             "user": {"login": "alice", "type": "User"}},
        ]
        assert self.find_human_reviewer(reviews) is None

    def test_multiple_states_only_approved_counted(self):
        reviews = [
            {"state": "DISMISSED",
             "user": {"login": "alice", "type": "User"}},
            {"state": "APPROVED",
             "user": {"login": "bob", "type": "User"}},
        ]
        assert self.find_human_reviewer(reviews) == "bob"


class TestPrecedentDetail:
    """Mirrors precedent_detail format (line 467).

    ``precedent_detail="Reviewed by ${reviewer} in ${repo}#${pr_number}"``
    """

    @staticmethod
    def format_detail(
        reviewer: str, repo: str, pr_number: int,
    ) -> str:
        """Mirror: line 467 of reusable_dependabot_reviewer.yml."""
        return f"Reviewed by {reviewer} in {repo}#{pr_number}"

    def test_normal_format(self):
        result = self.format_detail("alice", "org/repo", 123)
        assert result == "Reviewed by alice in org/repo#123"

    def test_no_at_mention(self):
        result = self.format_detail("alice", "org/repo", 123)
        assert "@alice" not in result, (
            "Precedent detail must not @-mention the reviewer "
            "to avoid notification spam"
        )

    def test_contains_repo_and_pr(self):
        result = self.format_detail("bob", "complytime/complyctl", 42)
        assert "complytime/complyctl#42" in result


# ── Mutation-Resistant Step Integrity Tests ────────────────────────


class TestOrgPrecedentStepIntegrity:
    """Mutation-resistant assertions against the Check Org Precedent step.

    These tests parse the actual workflow YAML and inspect the step's
    properties and ``run`` script verbatim, so that logic mutations in
    the bash implementation surface as test failures without requiring
    Python mirrors of every branch.
    """

    @pytest.fixture
    def precedent_step(self, steps: list[dict[str, Any]]) -> dict[str, Any]:
        """Extract the Check Org Precedent step from the workflow."""
        matches = [
            s for s in steps if "Check Org Precedent" in s.get("name", "")
        ]
        assert len(matches) == 1, "Expected exactly one 'Check Org Precedent' step"
        return matches[0]

    @pytest.fixture
    def run_block(self, precedent_step: dict[str, Any]) -> str:
        """Return the run: script of the Check Org Precedent step."""
        return precedent_step.get("run", "")

    def test_step_has_continue_on_error_true(
        self, precedent_step: dict[str, Any],
    ) -> None:
        """Step must declare continue-on-error: true at the step level."""
        assert precedent_step.get("continue-on-error") is True

    def test_search_command_does_not_mix_stderr_into_stdout(
        self, run_block: str,
    ) -> None:
        """Search command must not redirect stderr into stdout (no 2>&1).

        Mixing stderr into stdout would pollute the result variable with
        error messages and produce false positives.
        """
        assert "2>&1" not in run_block

    def test_jq_filter_uses_test_for_title_verification(
        self, run_block: str,
    ) -> None:
        """jq filter must use test( for regex title matching.

        A literal string equality check would not handle case-insensitive
        version patterns, so test() is required.
        """
        assert "test(" in run_block

    def test_reviews_api_call_uses_paginate(
        self, run_block: str,
    ) -> None:
        """Reviews API call must include --paginate to avoid missing approvals."""
        assert "--paginate" in run_block

    def test_default_org_precedent_false_written_before_search(
        self, run_block: str,
    ) -> None:
        """org_precedent=false must be written as default before the loop.

        Ensures graceful degradation: if the search loop is skipped or
        all candidates are exhausted, the output defaults to false.
        """
        default_pos = run_block.find("org_precedent=false")
        loop_pos = run_block.find("for idx in")
        assert default_pos != -1, "org_precedent=false not found in run block"
        assert loop_pos != -1, "Candidate loop not found in run block"
        assert default_pos < loop_pos, (
            "org_precedent=false default must appear before the candidate loop"
        )

    def test_search_command_does_not_use_review_approved_flag(
        self, run_block: str,
    ) -> None:
        """gh search must NOT use --review approved.

        Human approval is verified separately via the Reviews API; the
        --review flag only checks whether any review exists and would
        conflate bot approvals with qualifying human approvals.
        """
        assert "--review approved" not in run_block
