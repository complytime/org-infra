# SPDX-License-Identifier: Apache-2.0

"""Regression tests for generate-crapload-comment.sh truncation logic.

Covers the truncation fix that ensures comments exceeding GitHub's
character limit are truncated with a trailer that fits within the limit.
See: TC-006 (bug fixes require regression tests).
"""

import json
import os
import subprocess
import tempfile
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent
SCRIPT_PATH = PROJECT_ROOT / "scripts" / "generate-crapload-comment.sh"


def _make_crap_json(tmp: str, total_functions: int = 5) -> str:
    """Write a minimal gaze crap JSON fixture and return its path."""
    path = os.path.join(tmp, "crapload-current.json")
    data = {
        "summary": {
            "total_functions": total_functions,
            "avg_complexity": 2,
            "avg_line_coverage": 80,
            "avg_crap": 5,
            "crap_threshold": 15,
            "crapload": 0,
            "avg_contract_coverage": 70,
            "avg_gaze_crap": 4,
            "gaze_crap_threshold": 15,
            "gaze_crapload": 0,
        },
        "comparison": {
            "regressions": 0,
            "improvements": 0,
            "new_functions": 0,
        },
        "scores": [],
    }
    with open(path, "w") as f:
        json.dump(data, f)
    return path


def _make_report_json(tmp: str) -> str:
    """Write a minimal gaze report JSON fixture and return its path."""
    path = os.path.join(tmp, "gaze-report.json")
    with open(path, "w") as f:
        json.dump({"errors": {}}, f)
    return path


def _make_baseline(tmp: str) -> str:
    """Write a minimal baseline file and return its path."""
    path = os.path.join(tmp, "baseline.json")
    with open(path, "w") as f:
        json.dump({"summary": {"crapload": 0}, "scores": []}, f)
    return path


def _run_script(
    crap_json: str,
    report_json: str,
    baseline: str,
    max_comment_size: str = "65536",
    comment_file: str | None = None,
) -> tuple[int, str]:
    """Run generate-crapload-comment.sh and return (returncode, comment_body).

    Uses an isolated COMMENT_FILE path per invocation to avoid
    cross-test interference via the shared /tmp default.
    """
    if comment_file is None:
        fd, comment_file = tempfile.mkstemp(suffix=".md", prefix="crapload-test-")
        os.close(fd)

    env = {
        **os.environ,
        "BASELINE": baseline,
        "GAZE_VERSION": "v0.0.0-test",
        "STATUS": "pass",
        "GITHUB_SERVER_URL": "https://github.com",
        "GITHUB_REPOSITORY": "test/repo",
        "GITHUB_RUN_ID": "12345",
        "MAX_COMMENT_SIZE": max_comment_size,
        "COMMENT_FILE": comment_file,
    }
    result = subprocess.run(
        ["bash", str(SCRIPT_PATH), crap_json, report_json],
        env=env,
        capture_output=True,
        text=True,
    )
    comment = ""
    if os.path.exists(comment_file):
        with open(comment_file) as f:
            comment = f.read()
        os.unlink(comment_file)
    return result.returncode, comment


class TestCraploadCommentTruncation:
    """Regression tests for comment truncation (off-by-one fix)."""

    def test_small_comment_not_truncated(self):
        """Comments under the limit are left unchanged."""
        with tempfile.TemporaryDirectory() as tmp:
            crap = _make_crap_json(tmp)
            report = _make_report_json(tmp)
            baseline = _make_baseline(tmp)

            rc, comment = _run_script(crap, report, baseline)

            assert rc == 0
            assert "Comment truncated" not in comment
            # Verify the comment has expected content
            assert "CRAP Load Analysis" in comment

    def test_oversized_comment_is_truncated(self):
        """Comments over the limit are truncated with a trailer."""
        with tempfile.TemporaryDirectory() as tmp:
            crap = _make_crap_json(tmp)
            report = _make_report_json(tmp)
            baseline = _make_baseline(tmp)

            # Use a very small limit to force truncation
            rc, comment = _run_script(
                crap, report, baseline, max_comment_size="200",
            )

            assert rc == 0
            assert "Comment truncated" in comment

    def test_truncated_comment_within_limit(self):
        """The final truncated file must not exceed MAX_COMMENT_SIZE."""
        with tempfile.TemporaryDirectory() as tmp:
            crap = _make_crap_json(tmp)
            report = _make_report_json(tmp)
            baseline = _make_baseline(tmp)

            limit = 300
            rc, comment = _run_script(
                crap, report, baseline, max_comment_size=str(limit),
            )

            assert rc == 0
            comment_bytes = len(comment.encode("utf-8"))
            assert comment_bytes <= limit, (
                f"Truncated comment is {comment_bytes} bytes, "
                f"exceeds limit of {limit}"
            )

    def test_trailer_present_after_truncation(self):
        """Truncation trailer includes byte counts for diagnostics."""
        with tempfile.TemporaryDirectory() as tmp:
            crap = _make_crap_json(tmp)
            report = _make_report_json(tmp)
            baseline = _make_baseline(tmp)

            rc, comment = _run_script(
                crap, report, baseline, max_comment_size="200",
            )

            assert rc == 0
            assert "limit 200" in comment
            assert "See full logs above" in comment
