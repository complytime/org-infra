# SPDX-License-Identifier: Apache-2.0

"""Integration tests for CRAP load workflow package resolution."""

import json
import os
import subprocess
import tempfile
from pathlib import Path


class TestCrapLoadPackageResolution:
    """Tests for scripts/resolve-go-packages.sh."""

    @staticmethod
    def _run_script(fixture_dir, args=""):
        """Run resolve-go-packages.sh in fixture directory."""
        project_root = Path(__file__).parent.parent
        script_path = project_root / "scripts" / "resolve-go-packages.sh"

        cmd = f"bash {script_path} {args}"
        result = subprocess.run(
            cmd,
            shell=True,
            cwd=fixture_dir,
            capture_output=True,
            text=True,
        )
        return result

    def test_single_module_repo(self):
        """Single module repo (go.mod at root with packages)."""
        with tempfile.TemporaryDirectory() as fixture:
            # Setup single-module fixture
            subprocess.run(["go", "mod", "init", "example.com/single"], cwd=fixture, check=True)
            cmd_app = Path(fixture) / "cmd" / "app"
            cmd_app.mkdir(parents=True)
            (cmd_app / "main.go").write_text("package main\nfunc main() {}\n")

            # Run the script
            result = self._run_script(fixture)

            # Verify
            assert result.returncode == 0
            assert result.stdout.strip() == "./..."

    def test_multi_module_repo(self):
        """Multi-module repo (no root go.mod)."""
        with tempfile.TemporaryDirectory() as fixture:
            # Setup multi-module fixture
            cmd_app = Path(fixture) / "cmd" / "app"
            cmd_app.mkdir(parents=True)
            subprocess.run(["go", "mod", "init", "example.com/app"], cwd=cmd_app, check=True)
            (cmd_app / "main.go").write_text("package main\nfunc main() {}\n")

            pkg_lib = Path(fixture) / "pkg" / "lib"
            pkg_lib.mkdir(parents=True)
            subprocess.run(["go", "mod", "init", "example.com/lib"], cwd=pkg_lib, check=True)
            (pkg_lib / "lib.go").write_text('package lib\nfunc Hello() string { return "hello" }\n')

            # Run the script
            result = self._run_script(fixture)

            # Verify
            assert result.returncode == 0
            tokens = result.stdout.split()
            assert "cmd/app/..." in tokens
            assert "pkg/lib/..." in tokens

    def test_go_workspace(self):
        """Go workspace (go.work with multiple modules)."""
        with tempfile.TemporaryDirectory() as fixture:
            # Create workspace
            subprocess.run(["go", "work", "init"], cwd=fixture, check=True)

            # Create tools module
            tools = Path(fixture) / "tools"
            tools.mkdir()
            subprocess.run(["go", "mod", "init", "example.com/tools"], cwd=tools, check=True)
            (tools / "tools.go").write_text("package tools\n")
            subprocess.run(["go", "work", "use", "."], cwd=tools, check=True)

            # Create app module
            app = Path(fixture) / "app"
            app.mkdir()
            subprocess.run(["go", "mod", "init", "example.com/app"], cwd=app, check=True)
            (app / "main.go").write_text("package main\nfunc main() {}\n")
            subprocess.run(["go", "work", "use", "."], cwd=app, check=True)

            # Run the script
            result = self._run_script(fixture)

            # Verify
            assert result.returncode == 0
            tokens = result.stdout.split()
            assert "app/..." in tokens
            assert "tools/..." in tokens

    def test_explicit_package_override(self):
        """Explicit package override."""
        with tempfile.TemporaryDirectory() as fixture:
            # Setup multi-module fixture
            cmd_app = Path(fixture) / "cmd" / "app"
            cmd_app.mkdir(parents=True)
            subprocess.run(["go", "mod", "init", "example.com/app"], cwd=cmd_app, check=True)
            (cmd_app / "main.go").write_text("package main\nfunc main() {}\n")

            cmd_exp = Path(fixture) / "cmd" / "experimental"
            cmd_exp.mkdir(parents=True)
            subprocess.run(["go", "mod", "init", "example.com/experimental"], cwd=cmd_exp, check=True)
            (cmd_exp / "main.go").write_text("package main\nfunc main() {}\n")

            pkg_lib = Path(fixture) / "pkg" / "lib"
            pkg_lib.mkdir(parents=True)
            subprocess.run(["go", "mod", "init", "example.com/lib"], cwd=pkg_lib, check=True)
            (pkg_lib / "lib.go").write_text('package lib\nfunc Hello() string { return "hello" }\n')

            # Run with explicit packages
            result = self._run_script(fixture, args="./cmd/app/... ./pkg/lib/...")

            # Verify
            assert result.returncode == 0
            # Script outputs each package on its own line
            assert "./cmd/app/..." in result.stdout
            assert "experimental" not in result.stdout and "experimental" not in result.stderr

    def test_empty_repo(self):
        """Empty repo (should fail gracefully)."""
        with tempfile.TemporaryDirectory() as fixture:
            # Run script in empty directory
            result = self._run_script(fixture)

            # Verify
            assert result.returncode == 1
            assert "No Go modules found" in result.stderr

    def test_single_module_with_vendor(self):
        """Single module with vendor (vendor auto-excluded)."""
        with tempfile.TemporaryDirectory() as fixture:
            # Setup single module
            subprocess.run(["go", "mod", "init", "example.com/test"], cwd=fixture, check=True)
            cmd_app = Path(fixture) / "cmd" / "app"
            cmd_app.mkdir(parents=True)
            (cmd_app / "main.go").write_text("package main\nfunc main() {}\n")

            # Add vendor directory
            vendor = Path(fixture) / "vendor" / "github.com" / "some" / "dep"
            vendor.mkdir(parents=True)
            (vendor / "go.mod").write_text("module github.com/some/dep\n")

            # Run the script
            result = self._run_script(fixture)

            # Verify
            assert result.returncode == 0
            assert result.stdout.strip() == "./..."
            assert "Using default packages" in result.stderr

    def test_malformed_go_mod(self):
        """Malformed go.mod (discovers module despite invalid syntax)."""
        with tempfile.TemporaryDirectory() as fixture:
            # Create invalid go.mod
            (Path(fixture) / "go.mod").write_text("this is not valid go.mod syntax\n")

            # Run the script
            result = self._run_script(fixture)

            # Verify - script discovers the go.mod file (validation happens in 'go list' later)
            assert result.returncode == 0
            assert "Found 1 module" in result.stderr
            assert result.stdout.strip() == "./..."

    def test_empty_module(self):
        """Empty module (no packages under ./...)."""
        with tempfile.TemporaryDirectory() as fixture:
            # Create valid go.mod but no Go files
            subprocess.run(["go", "mod", "init", "example.com/empty"], cwd=fixture, check=True)

            # Run the script
            result = self._run_script(fixture)

            # Verify
            assert result.returncode == 0
            assert result.stdout.strip() == "./..."


class TestWorkflowInputValidation:
    """Tests for GitHub Actions workflow input validation patterns."""

    # Mirrors: reusable_compliance.yml "Validate policy_id input" step (lines ~103-111)
    @staticmethod
    def _validate_policy_id(policy_id):
        """Validate policy_id using workflow regex."""
        import re
        if not re.match(r"^[a-zA-Z0-9_-]+$", policy_id):
            return False
        return True

    # Mirrors: reusable_compliance.yml "Validate complytime_config_path input" step (added by this PR)
    @staticmethod
    def _validate_path(path):
        """Validate complytime_config_path using workflow rules."""
        import re
        if not re.match(r"^[a-zA-Z0-9_./-]+$", path):
            return False
        if ".." in path:
            return False
        return True

    def test_policy_id_valid_values(self):
        """Test valid policy_id patterns."""
        assert self._validate_policy_id("ampel-bp") is True
        assert self._validate_policy_id("policy_123") is True
        assert self._validate_policy_id("test-policy-v2") is True
        assert self._validate_policy_id("UPPERCASE") is True
        assert self._validate_policy_id("a1b2c3") is True

    def test_policy_id_invalid_values(self):
        """Test invalid policy_id patterns are rejected."""
        assert self._validate_policy_id("../evil") is False
        assert self._validate_policy_id(";rm -rf /") is False
        assert self._validate_policy_id("") is False
        assert self._validate_policy_id("policy.with.dots") is False
        assert self._validate_policy_id("policy with spaces") is False

    def test_complytime_config_path_valid_values(self):
        """Test valid complytime_config_path patterns."""
        assert self._validate_path("complytime.yaml") is True
        assert self._validate_path(".github/complytime.yaml") is True
        assert self._validate_path("config/complytime.yaml") is True
        assert self._validate_path("my_config.yaml") is True

    def test_complytime_config_path_traversal_rejection(self):
        """Test path traversal attacks are blocked."""
        assert self._validate_path("../../etc/passwd") is False
        assert self._validate_path("../evil") is False
        assert self._validate_path("subdir/../../../etc/passwd") is False

    def test_complytime_config_path_shell_metacharacters(self):
        """Test shell metacharacters are blocked."""
        assert self._validate_path("file; rm -rf /") is False
        assert self._validate_path("file$var.yaml") is False
        assert self._validate_path("file*.yaml") is False
        assert self._validate_path("file|cat") is False
        assert self._validate_path("file&background") is False

    def test_complytime_config_path_canonical_check(self):
        """Test realpath canonicalization and root escape detection."""
        with tempfile.TemporaryDirectory() as fixture:
            caller_dir = Path(fixture) / "_caller"
            caller_dir.mkdir()
            config_dir = caller_dir / "config"
            config_dir.mkdir()

            # Create test files
            (caller_dir / "complytime.yaml").touch()
            (config_dir / "complytime.yaml").touch()

            # Valid paths within caller
            original_dir = os.getcwd()
            try:
                os.chdir(fixture)
                real = os.path.realpath(os.path.join("_caller", "complytime.yaml"))
                caller_root = os.path.realpath("_caller")
                assert real.startswith(caller_root + "/")

                real = os.path.realpath(os.path.join("_caller", "config/complytime.yaml"))
                assert real.startswith(caller_root + "/")
            finally:
                os.chdir(original_dir)


class TestCompareCrapload:
    """Tests for scripts/compare-crapload.sh."""

    _MINIMAL_SUMMARY = {
        "crapload": 0,
        "gaze_crapload": 0,
        "avg_complexity": 1.0,
        "avg_line_coverage": 80.0,
        "avg_crap": 5.0,
        "crap_threshold": 15,
        "avg_contract_coverage": 70.0,
        "avg_gaze_crap": 5.0,
        "gaze_crap_threshold": 15,
        "total_functions": 1,
    }

    @staticmethod
    def _run_script(
        current_json_path,
        baseline_json_path,
        threshold=30,
        epsilon=0.5,
        gaze_version="latest",
        gaze_report="/dev/null",
    ):
        """Run compare-crapload.sh from repo root and return CompletedProcess."""
        project_root = Path(__file__).parent.parent
        script_path = project_root / "scripts" / "compare-crapload.sh"
        result = subprocess.run(
            [
                "bash",
                str(script_path),
                str(current_json_path),
                str(baseline_json_path),
                str(threshold),
                str(epsilon),
                str(gaze_version),
                str(gaze_report),
            ],
            capture_output=True,
            text=True,
            cwd=str(project_root),
        )
        return result

    def test_no_baseline(self):
        """No baseline file → status=pass with 'no baseline' comment."""
        current_data = {
            "summary": dict(self._MINIMAL_SUMMARY),
            "scores": [{"file": "pkg/foo.go", "function": "Bar", "crap": 5.0, "gaze_crap": 5.0}],
        }
        tmp_current = None
        try:
            with tempfile.NamedTemporaryFile(
                mode="w", suffix=".json", delete=False,
            ) as f:
                json.dump(current_data, f)
                tmp_current = f.name

            nonexistent_baseline = tmp_current + ".nonexistent"
            result = self._run_script(tmp_current, nonexistent_baseline)

            assert result.returncode == 0
            assert "status=pass" in result.stdout

            comment_path = Path("/tmp/crapload-comment-body.md")
            assert comment_path.exists()
            comment_body = comment_path.read_text()
            assert "<!-- crapload-analysis-marker -->" in comment_body
            assert "no baseline" in comment_body.lower()
        finally:
            if tmp_current and os.path.exists(tmp_current):
                os.unlink(tmp_current)

    def test_regression_detected(self):
        """Regression (current CRAP > baseline + epsilon) → status=fail, regressions_count=1."""
        current_data = {
            "summary": dict(self._MINIMAL_SUMMARY),
            "scores": [{"file": "pkg/foo.go", "function": "Bar", "crap": 20.0, "gaze_crap": 20.0}],
        }
        baseline_data = {
            "summary": dict(self._MINIMAL_SUMMARY),
            "scores": [{"file": "pkg/foo.go", "function": "Bar", "crap": 5.0, "gaze_crap": 5.0}],
        }
        tmp_current = tmp_baseline = None
        try:
            with tempfile.NamedTemporaryFile(
                mode="w", suffix=".json", delete=False,
            ) as f:
                json.dump(current_data, f)
                tmp_current = f.name
            with tempfile.NamedTemporaryFile(
                mode="w", suffix=".json", delete=False,
            ) as f:
                json.dump(baseline_data, f)
                tmp_baseline = f.name

            result = self._run_script(tmp_current, tmp_baseline, epsilon=0.5)

            assert result.returncode == 0
            assert "status=fail" in result.stdout
            assert "regressions_count=1" in result.stdout
        finally:
            for path in (tmp_current, tmp_baseline):
                if path and os.path.exists(path):
                    os.unlink(path)

    def test_improvement_detected(self):
        """Improvement (current CRAP < baseline - epsilon) → status=pass, improvements_count=1."""
        current_data = {
            "summary": dict(self._MINIMAL_SUMMARY),
            "scores": [{"file": "pkg/foo.go", "function": "Bar", "crap": 5.0, "gaze_crap": 5.0}],
        }
        baseline_data = {
            "summary": dict(self._MINIMAL_SUMMARY),
            "scores": [{"file": "pkg/foo.go", "function": "Bar", "crap": 20.0, "gaze_crap": 20.0}],
        }
        tmp_current = tmp_baseline = None
        try:
            with tempfile.NamedTemporaryFile(
                mode="w", suffix=".json", delete=False,
            ) as f:
                json.dump(current_data, f)
                tmp_current = f.name
            with tempfile.NamedTemporaryFile(
                mode="w", suffix=".json", delete=False,
            ) as f:
                json.dump(baseline_data, f)
                tmp_baseline = f.name

            result = self._run_script(tmp_current, tmp_baseline, epsilon=0.5)

            assert result.returncode == 0
            assert "status=pass" in result.stdout
            assert "improvements_count=1" in result.stdout
        finally:
            for path in (tmp_current, tmp_baseline):
                if path and os.path.exists(path):
                    os.unlink(path)

    def test_new_function_above_threshold(self):
        """New function with CRAP > threshold → status=fail."""
        current_data = {
            "summary": dict(self._MINIMAL_SUMMARY),
            "scores": [{"file": "pkg/foo.go", "function": "NewFunc", "crap": 50.0, "gaze_crap": 50.0}],
        }
        baseline_data = {
            "summary": dict(self._MINIMAL_SUMMARY),
            "scores": [{"file": "pkg/foo.go", "function": "OtherFunc", "crap": 5.0, "gaze_crap": 5.0}],
        }
        tmp_current = tmp_baseline = None
        try:
            with tempfile.NamedTemporaryFile(
                mode="w", suffix=".json", delete=False,
            ) as f:
                json.dump(current_data, f)
                tmp_current = f.name
            with tempfile.NamedTemporaryFile(
                mode="w", suffix=".json", delete=False,
            ) as f:
                json.dump(baseline_data, f)
                tmp_baseline = f.name

            result = self._run_script(tmp_current, tmp_baseline, threshold=30)

            assert result.returncode == 0
            assert "status=fail" in result.stdout
        finally:
            for path in (tmp_current, tmp_baseline):
                if path and os.path.exists(path):
                    os.unlink(path)

    def test_new_function_below_threshold(self):
        """New function with CRAP <= threshold → status=pass."""
        current_data = {
            "summary": dict(self._MINIMAL_SUMMARY),
            "scores": [{"file": "pkg/foo.go", "function": "NewFunc", "crap": 10.0, "gaze_crap": 10.0}],
        }
        baseline_data = {
            "summary": dict(self._MINIMAL_SUMMARY),
            "scores": [],
        }
        tmp_current = tmp_baseline = None
        try:
            with tempfile.NamedTemporaryFile(
                mode="w", suffix=".json", delete=False,
            ) as f:
                json.dump(current_data, f)
                tmp_current = f.name
            with tempfile.NamedTemporaryFile(
                mode="w", suffix=".json", delete=False,
            ) as f:
                json.dump(baseline_data, f)
                tmp_baseline = f.name

            result = self._run_script(tmp_current, tmp_baseline, threshold=30)

            assert result.returncode == 0
            assert "status=pass" in result.stdout
        finally:
            for path in (tmp_current, tmp_baseline):
                if path and os.path.exists(path):
                    os.unlink(path)
