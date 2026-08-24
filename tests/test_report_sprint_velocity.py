# SPDX-License-Identifier: Apache-2.0

"""Tests for report-sprint-velocity.py."""

from __future__ import annotations

import importlib
import sys
from pathlib import Path

import yaml

sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

report = importlib.import_module("report-sprint-velocity")


def _iteration(title: str, start: str, completed: bool, duration: int = 14) -> report.IterationInfo:
    return report.IterationInfo(
        title=title, start_date=start, duration=duration, completed=completed
    )


def _issue(
    *,
    iteration: str,
    size: str = "S",
    organization: str = "unbound-force",
    milestone: str = "release v0.16.0",
    is_story: bool = False,
    title: str = "work",
) -> report.DoneIssue:
    return report.DoneIssue(
        title=title,
        url="https://github.com/example/repo/issues/1",
        number=1,
        repo="example/repo",
        size=size,
        organization=organization,
        milestone=milestone,
        iteration=iteration,
        is_story=is_story,
    )


def _item(
    *,
    typename: str = "Issue",
    status: str = "Done ✔️",
    size: str = "S",
    organization: str = "unbound-force",
    milestone: str = "release v0.16.0",
    iteration: str | None = "CA Sprint 1",
    title: str = "work",
    labels: list[str] | None = None,
) -> dict:
    values = [
        {
            "__typename": "ProjectV2ItemFieldSingleSelectValue",
            "name": status,
            "field": {"name": "Status"},
        },
        {
            "__typename": "ProjectV2ItemFieldSingleSelectValue",
            "name": size,
            "field": {"name": "Size"},
        },
        {
            "__typename": "ProjectV2ItemFieldSingleSelectValue",
            "name": organization,
            "field": {"name": "Organization"},
        },
        {
            "__typename": "ProjectV2ItemFieldMilestoneValue",
            "milestone": {"title": milestone} if milestone else None,
        },
    ]
    if iteration:
        values.append(
            {
                "__typename": "ProjectV2ItemFieldIterationValue",
                "title": iteration,
                "field": {"name": "Iteration"},
            }
        )
    return {
        "fieldValues": {"nodes": values},
        "content": {
            "__typename": typename,
            "number": 1,
            "title": title,
            "url": "https://example.test/1",
            "labels": {"nodes": [{"name": n} for n in (labels or [])]},
            "repository": {"nameWithOwner": "example/repo"},
        },
    }


class TestStoryDetection:
    def test_title_prefix(self):
        assert report.is_story("[Story] Do the thing", []) is True

    def test_type_story_label(self):
        assert report.is_story("Do the thing", ["bug", "type:story"]) is True

    def test_plain_issue(self):
        assert report.is_story("fix: typo", ["bug"]) is False


class TestParseIterations:
    def test_splits_completed_and_open(self):
        nodes = [
            {
                "configuration": {
                    "completedIterations": [
                        {
                            "title": "CA Sprint 0",
                            "startDate": "2026-08-03",
                            "duration": 14,
                        }
                    ],
                    "iterations": [
                        {
                            "title": "CA Sprint 1",
                            "startDate": "2026-08-17",
                            "duration": 16,
                        }
                    ],
                }
            }
        ]
        parsed = report.parse_iterations(nodes)
        assert [i.title for i in parsed] == ["CA Sprint 0", "CA Sprint 1"]
        assert parsed[0].completed is True
        assert parsed[1].completed is False


class TestParseDoneIssue:
    def test_requires_done_and_iteration(self):
        issue = report.parse_done_issue(_item())
        assert issue is not None
        assert issue.iteration == "CA Sprint 1"
        assert issue.size == "S"

    def test_skips_pull_requests(self):
        assert report.parse_done_issue(_item(typename="PullRequest")) is None

    def test_skips_in_progress(self):
        assert report.parse_done_issue(_item(status="In progress 📋")) is None

    def test_skips_done_without_iteration(self):
        assert report.parse_done_issue(_item(iteration=None)) is None

    def test_unsized_and_story_label(self):
        issue = report.parse_done_issue(
            _item(size=None, title="[Story] Ship it", labels=["type:story"])
        )
        assert issue is not None
        assert issue.size == "Unsized"
        assert issue.is_story is True


class TestCountDoneWithoutIteration:
    def test_counts_only_done_issues_missing_iteration(self):
        items = [
            _item(iteration=None),
            _item(iteration="CA Sprint 1"),
            _item(status="Backlog", iteration=None),
            _item(typename="PullRequest", iteration=None),
        ]
        assert report.count_done_without_iteration(items) == 1


class TestAverages:
    def test_open_sprint_excluded_and_empty_completed_is_zero(self):
        iterations = [
            _iteration("CA Sprint 1", "2026-08-17", completed=True),
            _iteration("CA Sprint 2", "2026-09-02", completed=True),
            _iteration("CA Sprint 3", "2026-09-16", completed=False),
        ]
        issues = [
            _issue(iteration="CA Sprint 1", size="S"),
            _issue(iteration="CA Sprint 1", size="M", organization="complytime"),
            _issue(iteration="CA Sprint 3", size="L"),  # open sprint
        ]
        completed, current = report.bucket_sprints(iterations, issues)
        assert [s.iteration.title for s in completed] == ["CA Sprint 1", "CA Sprint 2"]
        assert completed[0].issues == 2
        assert completed[1].issues == 0  # closed with no Done work
        assert current[0].issues == 1
        assert report.mean([s.issues for s in completed]) == 1.0

        org_rows = {
            key: avg for key, _series, avg in report.breakdown_average(completed, "organizations")
        }
        assert org_rows["unbound-force"] == 0.5  # 1 then 0
        assert org_rows["complytime"] == 0.5

    def test_size_average_treats_missing_as_zero(self):
        iterations = [
            _iteration("CA Sprint 1", "2026-08-17", completed=True),
            _iteration("CA Sprint 2", "2026-09-02", completed=True),
        ]
        issues = [
            _issue(iteration="CA Sprint 1", size="S"),
            _issue(iteration="CA Sprint 1", size="S"),
            _issue(iteration="CA Sprint 2", size="M"),
        ]
        completed, _current = report.bucket_sprints(iterations, issues)
        sizes = {
            key: (series, avg)
            for key, series, avg in report.breakdown_average(completed, "sizes")
        }
        assert sizes["S"] == ([2, 0], 1.0)
        assert sizes["M"] == ([0, 1], 0.5)

    def test_no_completed_sprints_means_no_average(self):
        iterations = [_iteration("CA Sprint 1", "2026-08-17", completed=False)]
        issues = [_issue(iteration="CA Sprint 1")]
        completed, current = report.bucket_sprints(iterations, issues)
        assert completed == []
        assert current[0].issues == 1
        assert report.mean([]) is None


class TestMarkdownPlaceholder:
    def test_explains_averages_will_appear_later(self):
        built = report.build_report(
            project_title="Compliance Automation planning",
            project_url="https://github.com/orgs/complytime/projects/14",
            generated_at="2026-08-24 11:00 UTC",
            iterations=[_iteration("CA Sprint 1", "2026-08-17", completed=False, duration=16)],
            item_nodes=[_item()],
        )
        markdown = report.render_markdown(built)
        assert "None yet" in markdown
        assert "Open sprint" in markdown
        assert "CA Sprint 1" in markdown
        payload = report.report_to_json(built)
        assert payload["averages"] is None
        assert payload["current"][0]["issues"] == 1

    def test_hides_future_empty_open_sprints(self):
        built = report.build_report(
            project_title="Compliance Automation planning",
            project_url="https://github.com/orgs/complytime/projects/14",
            generated_at="2026-08-24 11:00 UTC",
            iterations=[
                _iteration("CA Sprint 1", "2026-08-17", completed=False, duration=16),
                _iteration("CA Sprint 2", "2026-09-02", completed=False),
            ],
            item_nodes=[_item()],
        )
        markdown = report.render_markdown(built)
        assert "CA Sprint 1" in markdown
        assert "CA Sprint 2" not in markdown

    def test_completed_sprints_include_average_row(self):
        built = report.build_report(
            project_title="Compliance Automation planning",
            project_url="https://github.com/orgs/complytime/projects/14",
            generated_at="2026-09-20 11:00 UTC",
            iterations=[
                _iteration("CA Sprint 1", "2026-08-17", completed=True, duration=16),
                _iteration("CA Sprint 2", "2026-09-02", completed=True),
            ],
            item_nodes=[
                _item(iteration="CA Sprint 1", size="S"),
                _item(
                    iteration="CA Sprint 2",
                    size="M",
                    organization="complytime",
                    milestone="Evidence Locker MVP",
                    title="[Story] Ship locker",
                    labels=["type:story"],
                ),
            ],
        )
        markdown = report.render_markdown(built)
        assert "**Average**" in markdown
        assert "Done issues by organization" in markdown
        assert "Typed user stories by milestone" in markdown
        payload = report.report_to_json(built)
        assert payload["averages"]["sprint_count"] == 2
        assert payload["averages"]["issues"] == 1.0
        assert payload["averages"]["stories"] == 0.5


class TestLoadProjectTarget:
    def test_reads_owner_and_number(self, tmp_path: Path):
        path = tmp_path / "cfg.yml"
        path.write_text(
            yaml.safe_dump({"project": {"owner": "complytime", "number": 14}}),
            encoding="utf-8",
        )
        assert report.load_project_target(path) == ("complytime", 14)
