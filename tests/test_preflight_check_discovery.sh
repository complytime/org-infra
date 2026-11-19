#!/usr/bin/env bash

# SPDX-License-Identifier: Apache-2.0

set -euo pipefail

# Behavioral tests for the "Discover CI checks" step in reusable_release_preflight.yml.
#
# Grepping the workflow source is not enough here: a source-text assertion passes
# while the expected statement is commented out or unreachable, and it breaks on
# harmless renaming. These tests execute the real step body against throwaway
# fixture repositories and assert on the check names it emits, which is exactly
# what the Checks API lookup below consumes.
#
# Naming rules under test:
#   * direct job            -> "<job name>", falling back to the job key
#   * reusable workflow job -> "<caller job name> / <called job name>"
#   * a workflow's top-level `name:` is never part of a check name

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
CI_LOCAL_NAME="Local CI"

# Resolve paths relative to the repository root so the script also works when it
# is invoked from another directory.
cd "$REPO_ROOT"

TESTS=0
FAILURES=0
WORK_DIR=""

pass() {
	TESTS=$((TESTS + 1))
	echo "PASS: $1"
}

fail() {
	TESTS=$((TESTS + 1))
	FAILURES=$((FAILURES + 1))
	echo "FAIL: $1"
}

trap 'rm -rf "$WORK_DIR"' EXIT

if ! command -v yq > /dev/null 2>&1; then
	echo "ERROR: yq is required by these tests (the discovery step uses it)" >&2
	exit 1
fi
if ! command -v jq > /dev/null 2>&1; then
	echo "ERROR: jq is required by these tests" >&2
	exit 1
fi

WORK_DIR="$(mktemp -d)"
DISCOVERY_SCRIPT="$WORK_DIR/discover-checks.sh"

# Pull the live step body out of the workflow so these tests cannot drift away
# from the code they protect. Runs from the repository root so the path handed to
# yq stays relative and portable across platforms.
yq -r '.jobs.preflight.steps[] | select(.id == "discover_checks") | .run' \
	.github/workflows/reusable_release_preflight.yml > "$DISCOVERY_SCRIPT"

# run_discovery <fixture-dir> [ci_checks-input]
#
# Runs the extracted step inside the fixture directory and prints the
# required_checks JSON array it reports.
run_discovery() {
	local fixture_dir="$1"
	local ci_checks_input="${2:-}"
	local output_file="$fixture_dir/GITHUB_OUTPUT.txt"

	(
		cd "$fixture_dir"
		CI_CHECKS_INPUT="$ci_checks_input" GITHUB_OUTPUT="$output_file" \
			bash "$DISCOVERY_SCRIPT" > "$fixture_dir/discovery.log" 2>&1
	)

	sed -n 's/^required_checks=//p' "$output_file"
}

# new_fixture <case-name> -> prints the fixture directory path
new_fixture() {
	local fixture_dir="$WORK_DIR/$1"
	mkdir -p "$fixture_dir/.github/workflows"
	printf '%s\n' "$fixture_dir"
}

# write_ci_local <fixture-dir>
#
# Fixture with two named jobs and one job without a `name`, so discovery has to
# fall back to the job key.
write_ci_local() {
	cat > "$1/.github/workflows/ci_local.yml" <<'YAML'
name: Local CI
on: push
jobs:
  unit-test:
    name: Unit Tests
  integration-test:
    name: Integration Tests
  smoke: {}
YAML
}

normalize_checks() {
	jq -c 'sort'
}

has_caller_prefix() {
	local checks="$1"
	local prefix="$2"

	echo "$checks" | jq -e --arg prefix "${prefix} / " \
		'any(.[]; startswith($prefix))' > /dev/null
}

assert_same_checks() {
	local description="$1"
	local expected="$2"
	local actual="$3"

	if [[ "$(printf '%s' "$actual" | normalize_checks)" == "$(printf '%s' "$expected" | normalize_checks)" ]]; then
		pass "$description"
	else
		fail "$description (expected $(printf '%s' "$expected" | normalize_checks), got $(printf '%s' "$actual" | normalize_checks))"
	fi
}

# ---------------------------------------------------------------------------
# 5.1 ci_checks.yml discovery uses the bare reusable-workflow check name
# ---------------------------------------------------------------------------

FIXTURE="$(new_fixture ci-checks-only)"
touch "$FIXTURE/.github/workflows/ci_checks.yml"
CHECKS="$(run_discovery "$FIXTURE")"

assert_same_checks \
	"5.1 ci_checks.yml discovery adds the bare 'Standardized CI / Run linters' check" \
	'["Standardized CI / Run linters"]' "$CHECKS"

if echo "$CHECKS" | jq -e 'index("CI / Standardized CI / Run linters") != null' > /dev/null; then
	fail "5.1b the shared linter check is still prefixed with 'CI /'"
else
	pass "5.1b the shared linter check is not prefixed with 'CI /'"
fi

# ---------------------------------------------------------------------------
# 5.2 ci_local.yml discovery uses job names, falling back to the job key
# ---------------------------------------------------------------------------

FIXTURE="$(new_fixture ci-local)"
write_ci_local "$FIXTURE"
CHECKS="$(run_discovery "$FIXTURE")"

assert_same_checks \
	"5.2 ci_local.yml discovery uses job names and falls back to the job key" \
	'["Unit Tests", "Integration Tests", "smoke"]' "$CHECKS"

# ---------------------------------------------------------------------------
# 5.3 Combined discovery keeps every bare name, with no workflow prefix
# ---------------------------------------------------------------------------

FIXTURE="$(new_fixture combined)"
touch "$FIXTURE/.github/workflows/ci_checks.yml"
write_ci_local "$FIXTURE"
CHECKS="$(run_discovery "$FIXTURE")"

assert_same_checks \
	"5.3 combined discovery reports every check without a workflow prefix" \
	'["Standardized CI / Run linters", "Unit Tests", "Integration Tests", "smoke"]' "$CHECKS"

if has_caller_prefix "$CHECKS" "$CI_LOCAL_NAME"; then
	fail "5.3b a discovered check still carries the ci_local.yml workflow name as a prefix"
else
	pass "5.3b no discovered check carries the ci_local.yml workflow name as a prefix"
fi

# ---------------------------------------------------------------------------
# 5.4 An explicit ci_checks input still bypasses auto-discovery
# ---------------------------------------------------------------------------

FIXTURE="$(new_fixture override)"
touch "$FIXTURE/.github/workflows/ci_checks.yml"
write_ci_local "$FIXTURE"
CHECKS="$(run_discovery "$FIXTURE" '["custom-a", "Build and test"]')"

assert_same_checks \
	"5.4 an explicit ci_checks input overrides auto-discovery" \
	'["custom-a", "Build and test"]' "$CHECKS"

# ---------------------------------------------------------------------------
# Summary
# ---------------------------------------------------------------------------

echo ""
echo "========================================="
echo "Results: $((TESTS - FAILURES))/$TESTS passed"
if [[ "$FAILURES" -gt 0 ]]; then
	echo "$FAILURES FAILED"
	exit 1
else
	echo "All assertions passed"
	exit 0
fi
