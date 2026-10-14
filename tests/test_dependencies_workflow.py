# SPDX-License-Identifier: Apache-2.0
"""Contract and logic-mirror tests for the Dependencies consumer workflow.

Validates structural contracts (permissions, constants, action pins, step
conditions) by parsing the workflow YAML, and mirrors inline bash/JS logic
as Python functions with parametrized test cases.

IMPORTANT: Mirror functions replicate the GitHub Actions expression and
JavaScript logic in ``.github/workflows/ci_dependencies.yml``. If the
workflow implementation changes, the corresponding mirror MUST be updated
to match. Line references are from the branch ``opsx/dependabot-org-precedent``.

See also: #662 (extract GitHubActionsLoader to conftest.py)
"""

import re
from pathlib import Path
from typing import Any

import pytest
import yaml

WORKFLOW_PATH = (
    Path(__file__).resolve().parents[1]
    / ".github"
    / "workflows"
    / "ci_dependencies.yml"
)
YAML_BOOLEAN_TAG = "tag:yaml.org,2002:bool"


class GitHubActionsLoader(yaml.SafeLoader):
    """Load YAML without treating the GitHub Actions ``on`` key as true."""


GitHubActionsLoader.yaml_implicit_resolvers = {
    first_character: [
        (tag, pattern)
        for tag, pattern in resolvers
        if tag != YAML_BOOLEAN_TAG
    ]
    for first_character, resolvers in (
        yaml.SafeLoader.yaml_implicit_resolvers.items()
    )
}
GitHubActionsLoader.add_implicit_resolver(
    YAML_BOOLEAN_TAG,
    re.compile(r"^(?:true|True|TRUE|false|False|FALSE)$"),
    list("tTfF"),
)


@pytest.fixture
def workflow() -> dict[str, Any]:
    """Parse the Dependencies consumer workflow."""
    with WORKFLOW_PATH.open(encoding="utf-8") as f:
        return yaml.load(f, Loader=GitHubActionsLoader)


@pytest.fixture
def comment_job(workflow: dict[str, Any]) -> dict[str, Any]:
    """Extract the comment_on_dependabot_prs job."""
    return workflow["jobs"]["comment_on_dependabot_prs"]


@pytest.fixture
def approve_job(workflow: dict[str, Any]) -> dict[str, Any]:
    """Extract the approve_dependabot_prs job."""
    return workflow["jobs"]["approve_dependabot_prs"]


@pytest.fixture
def approve_steps(
    approve_job: dict[str, Any],
) -> list[dict[str, Any]]:
    """Extract the approve job steps."""
    return approve_job["steps"]


# ── YAML Contract Tests ────────────────────────────────────────────


class TestWorkflowContract:
    """Structural contract tests for ci_dependencies.yml."""

    def test_workflow_permissions_deny_writes(
        self, workflow: dict[str, Any],
    ) -> None:
        """Workflow-level permissions must be read-only."""
        assert workflow["permissions"] == {
            "contents": "read",
            "issues": "none",
            "pull-requests": "none",
        }

    def test_min_release_age_constant_is_24(
        self, workflow: dict[str, Any],
    ) -> None:
        """MIN_RELEASE_AGE_HOURS must be 24."""
        assert workflow["env"]["MIN_RELEASE_AGE_HOURS"] == 24

    def test_comment_job_requires_both_reviewers(
        self, comment_job: dict[str, Any],
    ) -> None:
        """Comment job must depend on both reviewer jobs."""
        needs = comment_job["needs"]
        assert "call_deps_reviewer" in needs
        assert "call_dependabot_reviewer" in needs

    def test_comment_job_permissions_scoped(
        self, comment_job: dict[str, Any],
    ) -> None:
        """Comment job must have exactly issues:read + pull-requests:write."""
        assert comment_job["permissions"] == {
            "issues": "read",
            "pull-requests": "write",
        }

    def test_approve_job_permissions_scoped(
        self, approve_job: dict[str, Any],
    ) -> None:
        """Approve job must have exactly contents:write + pull-requests:write."""
        assert approve_job["permissions"] == {
            "contents": "write",
            "pull-requests": "write",
        }

    def test_all_action_refs_are_sha_pinned(
        self, workflow: dict[str, Any],
    ) -> None:
        """Every non-local uses: reference must be a 40-char SHA."""
        for _job_name, job in workflow["jobs"].items():
            uses = job.get("uses", "")
            if uses and not uses.startswith("./"):
                assert re.match(r"^[^@]+@[0-9a-f]{40}", uses), (
                    f"Job ref not SHA-pinned: {uses}"
                )
            for step in job.get("steps", []):
                step_uses = step.get("uses")
                if step_uses and not step_uses.startswith("./"):
                    assert re.match(
                        r"^[^@]+@[0-9a-f]{40}", step_uses,
                    ), f"Action ref not SHA-pinned: {step_uses}"

    def test_auto_merge_step_continues_on_error(
        self, approve_steps: list[dict[str, Any]],
    ) -> None:
        """Auto-merge step must have continue-on-error: true."""
        merge_steps = [
            s for s in approve_steps
            if "Auto-merge" in s.get("name", "")
        ]
        assert len(merge_steps) == 1
        assert merge_steps[0].get("continue-on-error") is True

    def test_auto_merge_step_name(
        self, approve_steps: list[dict[str, Any]],
    ) -> None:
        """Auto-merge step name must reflect broadened scope."""
        merge_steps = [
            s for s in approve_steps
            if "Auto-merge" in s.get("name", "")
        ]
        assert len(merge_steps) == 1
        assert merge_steps[0]["name"] == "Enable Auto-merge"


# ── Logic Mirror Tests ─────────────────────────────────────────────


class TestApprovalCondition:
    """Mirrors the 3-path disjunction in Auto-approve step (lines 93-110).

    Path A: third-party (risk != high, review success, age known, age >= 24h)
    Path B: org-owned (risk != high, review success) — no age gate
    Path C: org-precedent (risk != high, review success, age known, age >= 24h)
    """

    @staticmethod
    def should_approve(
        risk: str,
        review: str,
        age_hours: int,
        is_org_owned: str,
        org_precedent: str,
        min_age: int = 24,
    ) -> bool:
        """Mirror: lines 93-110 of ci_dependencies.yml."""
        # Path A: third-party
        path_a = (
            risk != "high"
            and review == "success"
            and age_hours != -1
            and age_hours >= min_age
        )
        # Path B: org-owned (no release age gate)
        path_b = (
            is_org_owned == "true"
            and risk != "high"
            and review == "success"
        )
        # Path C: org-precedent
        path_c = (
            org_precedent == "true"
            and risk != "high"
            and review == "success"
            and age_hours != -1
            and age_hours >= min_age
        )
        return path_a or path_b or path_c

    @pytest.mark.parametrize(
        "risk,review,age,org_owned,precedent,expected,desc",
        [
            ("low", "success", 48, "false", "false", True, "path-a"),
            ("medium", "success", 48, "false", "false", True, "path-a-med"),
            ("high", "success", 48, "false", "false", False, "high-blocks"),
            ("low", "failure", 48, "false", "false", False, "review-fail"),
            ("low", "success", -1, "false", "false", False, "unknown-age"),
            ("low", "success", 12, "false", "false", False, "age-under"),
            ("low", "success", 24, "false", "false", True, "age-boundary"),
            ("low", "success", -1, "true", "false", True, "path-b"),
            ("high", "success", 48, "true", "false", False, "org-high"),
            ("low", "failure", 48, "true", "false", False, "org-review"),
            ("low", "success", 48, "false", "true", True, "path-c"),
            ("high", "success", 48, "false", "true", False, "prec-high"),
            ("low", "success", -1, "false", "true", False, "prec-no-age"),
            ("low", "success", 12, "false", "true", False, "prec-under"),
            ("low", "success", 48, "true", "true", True, "both-true"),
            ("high", "failure", -1, "false", "false", False, "all-fail"),
        ],
        ids=lambda val: val if isinstance(val, str) and "-" in val
        else None,
    )
    def test_approval(
        self, risk, review, age, org_owned, precedent, expected, desc,
    ):
        assert self.should_approve(
            risk, review, age, org_owned, precedent,
        ) is expected


class TestAutoMergeCondition:
    """Mirrors the auto-merge step if-condition (lines 141-144).

    ``steps.auto_approve.outcome == 'success' &&
     (is_org_owned == 'true' || org_precedent == 'true')``
    """

    @staticmethod
    def should_auto_merge(
        approve_outcome: str,
        is_org_owned: str,
        org_precedent: str,
    ) -> bool:
        """Mirror: lines 141-144 of ci_dependencies.yml."""
        return (
            approve_outcome == "success"
            and (
                is_org_owned == "true"
                or org_precedent == "true"
            )
        )

    @pytest.mark.parametrize(
        "outcome,org_owned,precedent,expected",
        [
            ("success", "true", "false", True),
            ("success", "false", "true", True),
            ("success", "true", "true", True),
            ("success", "false", "false", False),
            ("failure", "true", "true", False),
            ("skipped", "true", "false", False),
        ],
        ids=[
            "org-owned", "precedent", "both",
            "third-party-no-precedent",
            "approve-failed", "approve-skipped",
        ],
    )
    def test_merge(self, outcome, org_owned, precedent, expected):
        assert self.should_auto_merge(
            outcome, org_owned, precedent,
        ) is expected


class TestCommentOwnershipDisplay:
    """Mirrors ownership table row ternary (line 70).

    Status: ``is_org_owned == 'true' && 'org-owned' || 'third-party'``
    Detail: ``is_org_owned == 'true' && 'Same organization...' || 'External...'``
    """

    @staticmethod
    def ownership_display(
        is_org_owned: str,
    ) -> tuple[str, str]:
        """Mirror: line 70 of ci_dependencies.yml."""
        if is_org_owned == "true":
            return (
                "org-owned",
                "Same organization \u2014 trusted source",
            )
        return ("third-party", "External dependency")

    @pytest.mark.parametrize(
        "is_org_owned,exp_status,exp_detail",
        [
            ("true", "org-owned",
             "Same organization \u2014 trusted source"),
            ("false", "third-party", "External dependency"),
            ("", "third-party", "External dependency"),
        ],
        ids=["org-owned", "third-party", "empty-string"],
    )
    def test_display(self, is_org_owned, exp_status, exp_detail):
        status, detail = self.ownership_display(is_org_owned)
        assert status == exp_status
        assert detail == exp_detail


class TestCommentPrecedentDisplay:
    """Mirrors org precedent table row ternary (line 71).

    Status: ``org_precedent == 'true' && 'found' || 'none'``
    Detail: ``org_precedent == 'true' && precedent_detail || 'No prior...'``
    """

    @staticmethod
    def precedent_display(
        org_precedent: str, precedent_detail: str,
    ) -> tuple[str, str]:
        """Mirror: line 71 of ci_dependencies.yml."""
        if org_precedent == "true":
            return ("found", precedent_detail)
        return (
            "none",
            "No prior merge found in the organization",
        )

    def test_found_with_detail(self):
        status, detail = self.precedent_display(
            "true", "Reviewed by alice in org/repo#1",
        )
        assert status == "found"
        assert detail == "Reviewed by alice in org/repo#1"

    def test_not_found(self):
        status, detail = self.precedent_display("false", "")
        assert status == "none"
        assert detail == (
            "No prior merge found in the organization"
        )

    def test_empty_precedent(self):
        status, detail = self.precedent_display("", "")
        assert status == "none"
        assert detail == (
            "No prior merge found in the organization"
        )


class TestCommentApprovalSummary:
    """Mirrors the 4-branch auto-approval summary ternary (line 74).

    Branch 1: org-owned + approved
    Branch 2: org-precedent + approved + age ok
    Branch 3: third-party + approved + age ok
    Branch 4: default (manual review)
    """

    @staticmethod
    def approval_summary(
        is_org_owned: str,
        org_precedent: str,
        risk: str,
        review: str,
        age_hours: int,
        min_age: int = 24,
    ) -> str:
        """Mirror: line 74 of ci_dependencies.yml.

        Returns the display text without the emoji prefix.
        """
        # Branch 1: org-owned
        if (
            is_org_owned == "true"
            and risk != "high"
            and review == "success"
        ):
            return "Approved + auto-merge requested (org-owned)"
        # Branch 2: org-precedent
        if (
            org_precedent == "true"
            and risk != "high"
            and review == "success"
            and age_hours != -1
            and age_hours >= min_age
        ):
            return "Approved + auto-merge requested (org precedent)"
        # Branch 3: third-party
        if (
            risk != "high"
            and review == "success"
            and age_hours != -1
            and age_hours >= min_age
        ):
            return "Approved"
        # Branch 4: default
        return "Manual review required"

    @pytest.mark.parametrize(
        "org_owned,precedent,risk,review,age,expected",
        [
            ("true", "false", "low", "success", 48,
             "Approved + auto-merge requested (org-owned)"),
            ("false", "true", "low", "success", 48,
             "Approved + auto-merge requested (org precedent)"),
            ("false", "false", "low", "success", 48,
             "Approved"),
            ("false", "false", "high", "success", 48,
             "Manual review required"),
            ("true", "true", "low", "success", 48,
             "Approved + auto-merge requested (org-owned)"),
            ("false", "true", "low", "success", 12,
             "Manual review required"),
            ("false", "true", "low", "success", -1,
             "Manual review required"),
            ("false", "false", "low", "failure", 48,
             "Manual review required"),
        ],
        ids=[
            "org-owned", "precedent", "third-party",
            "high-risk", "org-owned-takes-priority",
            "precedent-age-under", "precedent-age-unknown",
            "review-failure",
        ],
    )
    def test_summary(
        self, org_owned, precedent, risk, review, age, expected,
    ):
        assert self.approval_summary(
            org_owned, precedent, risk, review, age,
        ) == expected


class TestApprovalMessageBody:
    """Mirrors JS approval body construction (lines 120-138).

    ``ownership = isOrgOwned === 'true' ? 'org-owned' : 'third-party'``
    ``ageInfo = isOrgOwned === 'true' ? 'skipped (org-owned)' : releaseAge+'h'``
    ``precedentInfo = orgPrecedent === 'true' ? ', precedent='+detail : ''``
    ``body = 'Automatically approved: risk=...release_age=...'+precedentInfo+'.'``
    """

    @staticmethod
    def format_body(
        risk: str,
        review: str,
        is_org_owned: str,
        release_age: str,
        org_precedent: str,
        precedent_detail: str,
    ) -> str:
        """Mirror: lines 121-136 of ci_dependencies.yml."""
        ownership = (
            "org-owned" if is_org_owned == "true"
            else "third-party"
        )
        age_info = (
            "skipped (org-owned)" if is_org_owned == "true"
            else f"{release_age}h"
        )
        precedent_info = (
            f", precedent={precedent_detail}"
            if org_precedent == "true" else ""
        )
        return (
            f"Automatically approved: risk={risk}, "
            f"review={review}, ownership={ownership}, "
            f"release_age={age_info}{precedent_info}."
        )

    def test_org_owned_body(self):
        body = self.format_body(
            "low", "success", "true", "48", "false", "",
        )
        assert "ownership=org-owned" in body
        assert "release_age=skipped (org-owned)" in body
        assert "precedent=" not in body

    def test_third_party_body(self):
        body = self.format_body(
            "low", "success", "false", "48", "false", "",
        )
        assert "ownership=third-party" in body
        assert "release_age=48h" in body
        assert "precedent=" not in body

    def test_with_precedent(self):
        body = self.format_body(
            "low", "success", "false", "48", "true",
            "Reviewed by alice in org/repo#1",
        )
        assert "precedent=Reviewed by alice in org/repo#1" in body
        assert body.endswith(".")

    def test_no_precedent_no_extra_comma(self):
        body = self.format_body(
            "low", "success", "false", "48", "false", "",
        )
        assert ", precedent=" not in body
