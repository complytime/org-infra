#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0

"""Report completed-sprint velocity from a GitHub Project (v2).

Counts Done issues per Iteration, then averages those counts across
*completed* iterations. The open sprint is shown but excluded from averages
so in-flight work does not skew velocity.

Before any sprint has closed, the report still runs: it prints the current
sprint snapshot and explains that averages appear once GitHub moves an
Iteration into completedIterations.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from collections import Counter
from dataclasses import dataclass, field
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Iterable, Sequence

from lib.github_client import GitHubClient
from lib.project_config import load_project_target

DEFAULT_CONFIG = "project-sync-config.yml"
SIZE_ORDER = ("XS", "S", "M", "L", "XL")
UNSIZED = "Unsized"
UNSET = "Unset"

FIELDS_QUERY = """
query($owner: String!, $number: Int!) {
  organization(login: $owner) {
    projectV2(number: $number) {
      title
      url
      fields(first: 40) {
        nodes {
          __typename
          ... on ProjectV2IterationField {
            name
            configuration {
              iterations { id title startDate duration }
              completedIterations { id title startDate duration }
            }
          }
        }
      }
    }
  }
}
"""

ITEMS_QUERY = """
query($owner: String!, $number: Int!, $cursor: String) {
  organization(login: $owner) {
    projectV2(number: $number) {
      items(first: 100, after: $cursor) {
        pageInfo { hasNextPage endCursor }
        nodes {
          fieldValues(first: 25) {
            nodes {
              __typename
              ... on ProjectV2ItemFieldSingleSelectValue {
                name
                field { ... on ProjectV2FieldCommon { name } }
              }
              ... on ProjectV2ItemFieldIterationValue {
                title
                field { ... on ProjectV2FieldCommon { name } }
              }
              ... on ProjectV2ItemFieldMilestoneValue {
                milestone { title }
              }
            }
          }
          content {
            __typename
            ... on Issue {
              number
              title
              url
              labels(first: 20) { nodes { name } }
              repository { nameWithOwner }
            }
          }
        }
      }
    }
  }
}
"""


@dataclass(frozen=True)
class IterationInfo:
    """One Iteration field option (open or completed)."""

    title: str
    start_date: str
    duration: int
    completed: bool


@dataclass(frozen=True)
class DoneIssue:
    """A Done issue assigned to an Iteration."""

    title: str
    url: str
    number: int
    repo: str
    size: str
    organization: str
    milestone: str
    iteration: str
    is_story: bool


@dataclass
class SprintStats:
    """Done-issue counts for one sprint."""

    iteration: IterationInfo
    issues: int = 0
    stories: int = 0
    sizes: dict[str, int] = field(default_factory=Counter)
    organizations: dict[str, int] = field(default_factory=Counter)
    milestones: dict[str, int] = field(default_factory=Counter)
    story_sizes: dict[str, int] = field(default_factory=Counter)
    story_organizations: dict[str, int] = field(default_factory=Counter)
    story_milestones: dict[str, int] = field(default_factory=Counter)


@dataclass
class VelocityReport:
    """Full report payload (markdown + JSON)."""

    project_title: str
    project_url: str
    generated_at: str
    completed: list[SprintStats]
    current: list[SprintStats]
    done_without_iteration: int


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--config",
        default=DEFAULT_CONFIG,
        help=f"Project sync config (default: {DEFAULT_CONFIG})",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Write JSON instead of Markdown",
    )
    parser.add_argument(
        "--output",
        default="",
        help="Optional file path; defaults to stdout",
    )
    parser.add_argument(
        "--json-output",
        default="",
        help="Also write the JSON payload to this path",
    )
    return parser.parse_args()


def is_story(title: str, labels: Sequence[str]) -> bool:
    """User stories use the [Story] title prefix and/or type:story."""
    if title.startswith("[Story]"):
        return True
    return any(label.lower() == "type:story" for label in labels)


def is_done_status(name: str | None) -> bool:
    return bool(name) and name.startswith("Done")


def normalize_size(name: str | None) -> str:
    if name in SIZE_ORDER:
        return name
    return UNSIZED


def normalize_label(name: str | None) -> str:
    if name:
        return name
    return UNSET


def _field_name(node: dict[str, Any]) -> str:
    field = node.get("field") or {}
    return field.get("name") or ""


def parse_iterations(fields_nodes: Iterable[dict[str, Any]]) -> list[IterationInfo]:
    """Read Iteration options; completedIterations are closed sprints."""
    found: list[IterationInfo] = []
    for node in fields_nodes:
        config = node.get("configuration")
        if not config:
            continue
        for item in config.get("completedIterations") or []:
            found.append(
                IterationInfo(
                    title=item["title"],
                    start_date=item.get("startDate") or "",
                    duration=int(item.get("duration") or 0),
                    completed=True,
                )
            )
        for item in config.get("iterations") or []:
            found.append(
                IterationInfo(
                    title=item["title"],
                    start_date=item.get("startDate") or "",
                    duration=int(item.get("duration") or 0),
                    completed=False,
                )
            )
    return found


def parse_done_issue(item: dict[str, Any]) -> DoneIssue | None:
    """Return a Done issue with an Iteration, otherwise None."""
    content = item.get("content") or {}
    if content.get("__typename") != "Issue":
        return None
    status = None
    size = None
    organization = None
    milestone = None
    iteration = None
    for value in item.get("fieldValues", {}).get("nodes", []):
        kind = value.get("__typename")
        fname = _field_name(value)
        if kind == "ProjectV2ItemFieldSingleSelectValue":
            if fname == "Status":
                status = value.get("name")
            elif fname == "Size":
                size = value.get("name")
            elif fname == "Organization":
                organization = value.get("name")
        elif kind == "ProjectV2ItemFieldIterationValue" and fname == "Iteration":
            iteration = value.get("title")
        elif kind == "ProjectV2ItemFieldMilestoneValue":
            milestone_node = value.get("milestone") or {}
            milestone = milestone_node.get("title")
    if not is_done_status(status) or not iteration:
        return None
    labels = [n["name"] for n in (content.get("labels") or {}).get("nodes", [])]
    title = content.get("title") or ""
    repo = (content.get("repository") or {}).get("nameWithOwner") or ""
    return DoneIssue(
        title=title,
        url=content.get("url") or "",
        number=int(content.get("number") or 0),
        repo=repo,
        size=normalize_size(size),
        organization=normalize_label(organization),
        milestone=normalize_label(milestone),
        iteration=iteration,
        is_story=is_story(title, labels),
    )


def count_done_without_iteration(items: Iterable[dict[str, Any]]) -> int:
    """Done issues that never got an Iteration — excluded from velocity."""
    count = 0
    for item in items:
        content = item.get("content") or {}
        if content.get("__typename") != "Issue":
            continue
        status = None
        iteration = None
        for value in item.get("fieldValues", {}).get("nodes", []):
            fname = _field_name(value)
            if value.get("__typename") == "ProjectV2ItemFieldSingleSelectValue":
                if fname == "Status":
                    status = value.get("name")
            elif (
                value.get("__typename") == "ProjectV2ItemFieldIterationValue"
                and fname == "Iteration"
            ):
                iteration = value.get("title")
        if is_done_status(status) and not iteration:
            count += 1
    return count


def empty_stats(iteration: IterationInfo) -> SprintStats:
    return SprintStats(
        iteration=iteration,
        sizes=Counter(),
        organizations=Counter(),
        milestones=Counter(),
        story_sizes=Counter(),
        story_organizations=Counter(),
        story_milestones=Counter(),
    )


def bucket_sprints(
    iterations: Sequence[IterationInfo], issues: Sequence[DoneIssue]
) -> tuple[list[SprintStats], list[SprintStats]]:
    """Group Done issues onto known iterations. Empty completed sprints stay 0."""
    by_title: dict[str, SprintStats] = {it.title: empty_stats(it) for it in iterations}
    for issue in issues:
        stats = by_title.get(issue.iteration)
        if stats is None:
            continue
        stats.issues += 1
        stats.sizes[issue.size] += 1
        stats.organizations[issue.organization] += 1
        stats.milestones[issue.milestone] += 1
        if issue.is_story:
            stats.stories += 1
            stats.story_sizes[issue.size] += 1
            stats.story_organizations[issue.organization] += 1
            stats.story_milestones[issue.milestone] += 1
    completed = [by_title[it.title] for it in iterations if it.completed]
    current = [by_title[it.title] for it in iterations if not it.completed]
    completed.sort(key=lambda s: s.iteration.start_date)
    current.sort(key=lambda s: s.iteration.start_date)
    return completed, current


def mean(values: Sequence[int]) -> float | None:
    if not values:
        return None
    return sum(values) / len(values)


def fmt_mean(value: float | None) -> str:
    if value is None:
        return "—"
    if abs(value - round(value)) < 1e-9:
        return str(int(round(value)))
    return f"{value:.1f}"


def _union_keys(counters: Sequence[dict[str, int]], extra: Sequence[str] = ()) -> list[str]:
    keys = set(extra)
    for counter in counters:
        keys.update(counter)
    ordered = [k for k in extra if k in keys]
    rest = sorted(keys - set(extra))
    return ordered + rest


def breakdown_average(
    sprints: Sequence[SprintStats], attr: str
) -> list[tuple[str, list[int], float]]:
    """Per-key counts across sprints, missing keys treated as 0."""
    counters = [getattr(s, attr) for s in sprints]
    extra = SIZE_ORDER + (UNSIZED,) if attr in {"sizes", "story_sizes"} else ()
    rows: list[tuple[str, list[int], float]] = []
    for key in _union_keys(counters, extra):
        series = [int(c.get(key, 0)) for c in counters]
        avg = mean(series)
        if avg is None:
            raise RuntimeError("breakdown_average requires at least one sprint")
        rows.append((key, series, avg))
    return rows


def sanitize_md(value: str) -> str:
    """Neutralize user-controlled strings for markdown / Actions summaries.

    GitHub issue titles, sprint names, and project fields can contain pipes,
    newlines, or ``::workflow-command`` sequences. Those would otherwise
    break tables or inject into ``GITHUB_STEP_SUMMARY``.
    """
    text = str(value).replace("\r\n", " ").replace("\n", " ").replace("\r", " ")
    text = text.replace("::", "∶∶")
    text = text.replace("|", "\\|")
    text = text.replace("`", "'")
    return text


def md_cell(value: str) -> str:
    """Table cell for a user-controlled string (code span + sanitization)."""
    return f"`{sanitize_md(value)}`"


def sprint_label(stats: SprintStats) -> str:
    it = stats.iteration
    return f"{sanitize_md(it.title)} ({it.start_date}, {it.duration}d)"


def _report_date(generated_at: str) -> date:
    return date.fromisoformat(generated_at[:10])


def iteration_is_active(iteration: IterationInfo, today: date) -> bool:
    """True when today falls in [start, start+duration)."""
    if not iteration.start_date:
        return False
    start = date.fromisoformat(iteration.start_date)
    end = start + timedelta(days=iteration.duration)
    return start <= today < end


def visible_open_sprints(report: VelocityReport) -> list[SprintStats]:
    """Hide future empty iterations; keep the active sprint and any with Done work."""
    today = _report_date(report.generated_at)
    return [
        stats
        for stats in report.current
        if stats.issues > 0 or iteration_is_active(stats.iteration, today)
    ]


def _md_table(headers: Sequence[str], rows: Sequence[Sequence[str]]) -> str:
    line = "| " + " | ".join(headers) + " |"
    sep = "| " + " | ".join("---" for _ in headers) + " |"
    body = "\n".join("| " + " | ".join(row) + " |" for row in rows)
    return "\n".join([line, sep, body])


def _sprint_headers(sprints: Sequence[SprintStats]) -> list[str]:
    return [md_cell(s.iteration.title) for s in sprints] + ["Average"]


def render_breakdown_table(
    sprints: Sequence[SprintStats], attr: str, first_col: str
) -> str:
    headers = [first_col, *_sprint_headers(sprints)]
    rows: list[list[str]] = []
    for key, series, avg in breakdown_average(sprints, attr):
        if sum(series) == 0 and key == UNSIZED:
            continue
        rows.append([md_cell(key), *[str(n) for n in series], fmt_mean(avg)])
    if not rows:
        return ""
    return _md_table(headers, rows)


def render_markdown(report: VelocityReport) -> str:
    title = sanitize_md(report.project_title)
    lines: list[str] = [
        f"# Sprint velocity — {title}",
        "",
        f"Generated {report.generated_at}. Source: [{title}]({report.project_url}).",
        "",
        "Averages use **completed** Iterations only. The open sprint is listed",
        "separately so in-progress Done items do not pull the mean down.",
        "Done issues with no Iteration are excluded from velocity.",
        "",
    ]

    open_sprints = visible_open_sprints(report)
    if open_sprints:
        lines.append("## Open sprint (excluded from averages)")
        lines.append("")
        for stats in open_sprints:
            lines.append(
                f"**{sprint_label(stats)}** — {stats.issues} Done issues "
                f"({stats.stories} typed user stories)."
            )
            size_bits = [
                f"{size}: {stats.sizes.get(size, 0)}"
                for size in SIZE_ORDER
                if stats.sizes.get(size, 0)
            ]
            if stats.sizes.get(UNSIZED):
                size_bits.append(f"{UNSIZED}: {stats.sizes[UNSIZED]}")
            if size_bits:
                lines.append("")
                lines.append("Sizes: " + ", ".join(size_bits))
            lines.append("")

    lines.append("## Completed sprints")
    lines.append("")
    if not report.completed:
        lines.append(
            "None yet. After CA Sprint 1 closes (its dates elapse and GitHub "
            "moves it to completed Iterations), re-run this report. Averages "
            "will appear here automatically."
        )
        lines.append("")
    else:
        headers = ["Sprint", "Start", "Days", "Done issues", "Stories"]
        rows = [
            [
                md_cell(s.iteration.title),
                s.iteration.start_date,
                str(s.iteration.duration),
                str(s.issues),
                str(s.stories),
            ]
            for s in report.completed
        ]
        n = len(report.completed)
        issue_avg = mean([s.issues for s in report.completed])
        story_avg = mean([s.stories for s in report.completed])
        rows.append(
            [
                "**Average**",
                "—",
                "—",
                f"**{fmt_mean(issue_avg)}**",
                f"**{fmt_mean(story_avg)}**",
            ]
        )
        lines.append(_md_table(headers, rows))
        lines.append("")
        lines.append(f"Mean of {n} completed sprint(s). Empty completed sprints count as 0.")
        lines.append("")

        lines.append("### Done issues by size (average per sprint)")
        lines.append("")
        lines.append(render_breakdown_table(report.completed, "sizes", "Size"))
        lines.append("")
        lines.append("### Done issues by organization (average per sprint)")
        lines.append("")
        lines.append(render_breakdown_table(report.completed, "organizations", "Organization"))
        lines.append("")
        lines.append("### Done issues by milestone (average per sprint)")
        lines.append("")
        lines.append(render_breakdown_table(report.completed, "milestones", "Milestone"))
        lines.append("")

        story_size = render_breakdown_table(report.completed, "story_sizes", "Size")
        if any(s.stories for s in report.completed) and story_size:
            lines.append("### Typed user stories by size (average per sprint)")
            lines.append("")
            lines.append(story_size)
            lines.append("")
            lines.append("### Typed user stories by organization (average per sprint)")
            lines.append("")
            lines.append(
                render_breakdown_table(report.completed, "story_organizations", "Organization")
            )
            lines.append("")
            lines.append("### Typed user stories by milestone (average per sprint)")
            lines.append("")
            lines.append(
                render_breakdown_table(report.completed, "story_milestones", "Milestone")
            )
            lines.append("")

    lines.append("## Notes")
    lines.append("")
    lines.append(
        f"- {report.done_without_iteration} Done issues have no Iteration "
        "(older board work) and are not in these averages."
    )
    lines.append(
        "- Typed user stories are issues titled `[Story] …` or labeled `type:story`."
    )
    lines.append(
        "- Pull requests are ignored. Only issues with Status starting with `Done` count."
    )
    lines.append("")
    return "\n".join(lines)


def report_to_json(report: VelocityReport) -> dict[str, Any]:
    def sprint_obj(stats: SprintStats) -> dict[str, Any]:
        return {
            "title": stats.iteration.title,
            "start_date": stats.iteration.start_date,
            "duration": stats.iteration.duration,
            "completed": stats.iteration.completed,
            "issues": stats.issues,
            "stories": stats.stories,
            "sizes": dict(stats.sizes),
            "organizations": dict(stats.organizations),
            "milestones": dict(stats.milestones),
        }

    averages: dict[str, Any] | None = None
    if report.completed:
        averages = {
            "sprint_count": len(report.completed),
            "issues": mean([s.issues for s in report.completed]),
            "stories": mean([s.stories for s in report.completed]),
            "sizes": {
                key: avg for key, _series, avg in breakdown_average(report.completed, "sizes")
            },
            "organizations": {
                key: avg
                for key, _series, avg in breakdown_average(report.completed, "organizations")
            },
            "milestones": {
                key: avg
                for key, _series, avg in breakdown_average(report.completed, "milestones")
            },
        }
    return {
        "project_title": report.project_title,
        "project_url": report.project_url,
        "generated_at": report.generated_at,
        "done_without_iteration": report.done_without_iteration,
        "current": [sprint_obj(s) for s in report.current],
        "completed": [sprint_obj(s) for s in report.completed],
        "averages": averages,
    }


def fetch_items(client: GitHubClient, owner: str, number: int) -> list[dict[str, Any]]:
    items: list[dict[str, Any]] = []
    cursor: str | None = None
    while True:
        data = client.graphql(
            ITEMS_QUERY, {"owner": owner, "number": number, "cursor": cursor}
        )
        page = data["organization"]["projectV2"]["items"]
        items.extend(page["nodes"])
        if not page["pageInfo"]["hasNextPage"]:
            break
        cursor = page["pageInfo"]["endCursor"]
    return items


def build_report(
    *,
    project_title: str,
    project_url: str,
    generated_at: str,
    iterations: Sequence[IterationInfo],
    item_nodes: Sequence[dict[str, Any]],
) -> VelocityReport:
    issues = []
    for node in item_nodes:
        parsed = parse_done_issue(node)
        if parsed:
            issues.append(parsed)
    completed, current = bucket_sprints(iterations, issues)
    return VelocityReport(
        project_title=project_title,
        project_url=project_url,
        generated_at=generated_at,
        completed=completed,
        current=current,
        done_without_iteration=count_done_without_iteration(item_nodes),
    )


def main() -> None:
    args = parse_args()
    token = os.environ.get("GITHUB_TOKEN", "")
    if not token:
        raise SystemExit("GITHUB_TOKEN is required")
    owner, number = load_project_target(Path(args.config))
    client = GitHubClient(token, user_agent="complytime-sprint-velocity-report")
    meta = client.graphql(FIELDS_QUERY, {"owner": owner, "number": number})
    project = meta["organization"]["projectV2"]
    iterations = parse_iterations(project["fields"]["nodes"])
    if not iterations:
        raise SystemExit("No Iteration field found on the project")
    items = fetch_items(client, owner, number)
    generated_at = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    report = build_report(
        project_title=project["title"],
        project_url=project["url"],
        generated_at=generated_at,
        iterations=iterations,
        item_nodes=items,
    )
    if args.json:
        text = json.dumps(report_to_json(report), indent=2) + "\n"
    else:
        text = render_markdown(report)
    if args.json_output:
        Path(args.json_output).write_text(
            json.dumps(report_to_json(report), indent=2) + "\n", encoding="utf-8"
        )
        print(f"Wrote {args.json_output}", file=sys.stderr)
    if args.output:
        Path(args.output).write_text(text, encoding="utf-8")
        print(f"Wrote {args.output}", file=sys.stderr)
    else:
        sys.stdout.write(text)


if __name__ == "__main__":
    main()
