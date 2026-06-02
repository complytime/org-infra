#!/usr/bin/env bash
# Compare CRAP scores against baseline and generate PR comment
# Usage: compare-crapload.sh <current-json> <baseline-json> <new-func-threshold> <epsilon> <gaze-version> [<gaze-report>]
#   <current-json>        Path to current CRAP JSON (required)
#   <baseline-json>       Path to baseline CRAP JSON (required)
#   <new-func-threshold>  CRAP ceiling for new functions (default: 30)
#   <epsilon>             Minimum delta to flag regression (default: 0.5)
#   <gaze-version>        Gaze version string for display (default: latest)
#   <gaze-report>         Path to full gaze JSON report (default: /tmp/gaze-report.json)
# Outputs: GitHub Actions outputs written to stdout; comment body written to /tmp/crapload-comment-body.md

set -euo pipefail

CURRENT="${1:?Missing current JSON file}"
BASELINE="${2:?Missing baseline JSON file}"
NEW_FUNC_THRESHOLD="${3:-30}"
EPSILON="${4:-0.5}"
GAZE_VERSION="${5:-latest}"
GAZE_REPORT="${6:-/tmp/gaze-report.json}"

# GitHub Actions environment variables (set by runner)
GITHUB_SERVER_URL="${GITHUB_SERVER_URL:-}"
GITHUB_REPOSITORY="${GITHUB_REPOSITORY:-}"
GITHUB_RUN_ID="${GITHUB_RUN_ID:-}"

# Temporary files — cleaned up on exit
BASELINE_TSV=$(mktemp /tmp/baseline-lookup.XXXXXX.tsv)
CURRENT_TSV=$(mktemp /tmp/current-scores.XXXXXX.tsv)
trap 'rm -f "$BASELINE_TSV" "$CURRENT_TSV"' EXIT

REGRESSIONS=""
IMPROVEMENTS=""
NEW_FUNCTIONS=""
REG_COUNT=0
IMP_COUNT=0
NEW_COUNT=0
NEW_VIOLATIONS=0

# Extract summary counts
CRAPLOAD=$(jq -r '.summary.crapload // 0' "$CURRENT")
GAZE_CRAPLOAD=$(jq -r '.summary.gaze_crapload // 0' "$CURRENT")

echo "crapload_count=$CRAPLOAD"
echo "gaze_crapload_count=$GAZE_CRAPLOAD"

if [[ ! -f "$BASELINE" ]]; then
	# No baseline - show current scores only
	echo "status=pass"
	echo "regressions_count=0"
	echo "improvements_count=0"

	# Generate no-baseline comment
	AVG_COMPLEXITY=$(jq -r '(.summary.avg_complexity // 0) * 10 | round / 10' "$CURRENT")
	AVG_LINE_COV=$(jq -r '(.summary.avg_line_coverage // 0) * 10 | round / 10' "$CURRENT")
	AVG_CRAP=$(jq -r '(.summary.avg_crap // 0) * 10 | round / 10' "$CURRENT")
	CRAP_THRESH=$(jq -r '.summary.crap_threshold // 15' "$CURRENT")
	AVG_CONTRACT_COV=$(jq -r '(.summary.avg_contract_coverage // 0) * 10 | round / 10' "$CURRENT")
	AVG_GAZE_CRAP=$(jq -r '(.summary.avg_gaze_crap // 0) * 10 | round / 10' "$CURRENT")
	GAZE_CRAP_THRESH=$(jq -r '.summary.gaze_crap_threshold // 15' "$CURRENT")
	TOTAL_FUNCS=$(jq -r '.summary.total_functions // 0' "$CURRENT")

	cat >/tmp/crapload-comment-body.md <<EOF
<!-- crapload-analysis-marker -->
## &#x2705; CRAP Load Analysis: PASS (no baseline)

No baseline file found at \`$BASELINE\`. Showing current scores without regression detection.

### How to Enable Regression Detection

Generate and commit a baseline file to track CRAP score changes over time:

\`\`\`bash
# 1. Install gaze
go install github.com/unbound-force/gaze/cmd/gaze@${GAZE_VERSION}

# 2. Auto-detect packages (works for single and multi-module repos)
PACKAGES=\$(find . -name go.mod -not -path '*/vendor/*' | xargs dirname | sed 's|^\./||;s|^$|.|;s|$|/...|' | paste -sd ' ')
[ -f go.mod ] && PACKAGES="./..."

# 3. Run tests and generate baseline
go test -coverprofile=coverage.out \$PACKAGES
mkdir -p .gaze
gaze report --format=json --coverprofile=coverage.out \$PACKAGES | jq '.crap' > .gaze/baseline.json

# 4. Commit the baseline
git add .gaze/baseline.json
git commit -m "chore: add CRAP baseline for regression detection"
\`\`\`

**Note**: The workflow auto-detects all modules when \`./...\` doesn't work. To analyze specific modules only, set the \`packages\` input.

**For more information**:
- [Gaze README](https://github.com/unbound-force/gaze/blob/main/README.md)
- [CI Integration Guide](https://github.com/unbound-force/gaze/blob/main/docs/guides/ci-integration.md)

### Summary

| Metric | Value |
|--------|-------|
| Functions analysed | ${TOTAL_FUNCS} |
| Avg complexity | ${AVG_COMPLEXITY} |
| Avg line coverage | ${AVG_LINE_COV}% |
| Avg CRAP score | ${AVG_CRAP} |
| CRAPload (>= ${CRAP_THRESH}) | ${CRAPLOAD} |
| Avg contract coverage | ${AVG_CONTRACT_COV}% |
| Avg GazeCRAP score | ${AVG_GAZE_CRAP} |
| GazeCRAPload (>= ${GAZE_CRAP_THRESH}) | ${GAZE_CRAPLOAD} |

[View full analysis logs](${GITHUB_SERVER_URL}/${GITHUB_REPOSITORY}/actions/runs/${GITHUB_RUN_ID})
EOF
	exit 0
fi

# Build lookup from baseline
jq -r '.scores[] | "\(.file):\(.function)\t\(.crap)\t\(.gaze_crap // 0)"' "$BASELINE" | sort >"$BASELINE_TSV"

# Extract current scores to temp file
jq -r '.scores[] | "\(.file):\(.function)\t\(.crap)\t\(.gaze_crap // 0)"' "$CURRENT" | sort >"$CURRENT_TSV"

# Process current scores
while IFS=$'\t' read -r key crap gaze_crap; do
	baseline_line=$(grep -F "${key}	" "$BASELINE_TSV" || true)
	# Validate numeric before bc arithmetic — non-numeric values from tampered JSON
	# could cause bc's system() to execute shell commands (injection risk)
	if ! [[ "$crap" =~ ^[0-9]+(\.[0-9]+)?$ ]] || ! [[ "$gaze_crap" =~ ^[0-9]+(\.[0-9]+)?$ ]]; then
		echo "::warning::Skipping non-numeric CRAP values for ${key}: crap=${crap} gaze_crap=${gaze_crap}" >&2
		continue
	fi
	if [[ -z "$baseline_line" ]]; then
		# New function
		NEW_COUNT=$((NEW_COUNT + 1))
		status_icon="+"
		crap_exceeds_threshold=$(echo "$crap > $NEW_FUNC_THRESHOLD" | bc -l)
		if ((crap_exceeds_threshold)); then
			NEW_VIOLATIONS=$((NEW_VIOLATIONS + 1))
			status_icon="!+"
		fi
		NEW_FUNCTIONS="${NEW_FUNCTIONS}| ${status_icon} | \`${key}\` | ${crap} | ${gaze_crap} | new (threshold: ${NEW_FUNC_THRESHOLD}) |"$'\n'
	else
		b_crap=$(echo "$baseline_line" | cut -f2)
		b_gaze=$(echo "$baseline_line" | cut -f3)
		# Validate baseline numeric values before bc arithmetic
		if ! [[ "$b_crap" =~ ^[0-9]+(\.[0-9]+)?$ ]] || ! [[ "$b_gaze" =~ ^[0-9]+(\.[0-9]+)?$ ]]; then
			echo "::warning::Skipping non-numeric baseline CRAP values for ${key}: b_crap=${b_crap} b_gaze=${b_gaze}" >&2
			continue
		fi
		crap_diff=$(echo "$crap - $b_crap" | bc -l)
		gaze_diff=$(echo "$gaze_crap - $b_gaze" | bc -l)
		has_regression=false
		has_improvement=false

		crap_regressed=$(echo "$crap - $b_crap > $EPSILON" | bc -l)
		crap_improved=$(echo "$b_crap - $crap > $EPSILON" | bc -l)
		if ((crap_regressed)); then
			has_regression=true
		elif ((crap_improved)); then
			has_improvement=true
		fi
		# Only evaluate GazeCRAP regression when baseline had contract
		# coverage (b_gaze > 0). A baseline of 0 means GazeCRAP was not
		# computable — no contract coverage existed for the function.
		# Transitioning from 0 to any positive value represents new
		# measurement (tests were added), not quality degradation.
		if [[ "$b_gaze" != "0" ]]; then
			gaze_regressed=$(echo "$gaze_crap - $b_gaze > $EPSILON" | bc -l)
			gaze_improved=$(echo "$b_gaze - $gaze_crap > $EPSILON" | bc -l)
			if ((gaze_regressed)); then
				has_regression=true
			elif ((gaze_improved)); then
				has_improvement=true
			fi
		fi

		if [[ "$has_regression" = "true" ]]; then
			REG_COUNT=$((REG_COUNT + 1))
			REGRESSIONS="${REGRESSIONS}| \`${key}\` | ${b_crap} | ${crap} | ${crap_diff} | ${b_gaze} | ${gaze_crap} | ${gaze_diff} |"$'\n'
		elif [[ "$has_improvement" = "true" ]]; then
			IMP_COUNT=$((IMP_COUNT + 1))
			IMPROVEMENTS="${IMPROVEMENTS}| \`${key}\` | ${b_crap} | ${crap} | ${crap_diff} | ${b_gaze} | ${gaze_crap} | ${gaze_diff} |"$'\n'
		fi
	fi
done <"$CURRENT_TSV"

# Output counts
echo "regressions_count=$REG_COUNT"
echo "improvements_count=$IMP_COUNT"

# Determine pass/fail
TOTAL_FAILURES=$((REG_COUNT + NEW_VIOLATIONS))
if [[ "$TOTAL_FAILURES" -gt 0 ]]; then
	echo "status=fail"
	echo "::error::CRAP regressions detected: $REG_COUNT regression(s), $NEW_VIOLATIONS new function violation(s)" >&2
else
	echo "status=pass"
fi

# Build PR comment body
STATUS_BADGE="&#x2705;"
STATUS_TEXT="PASS"
if [[ "$TOTAL_FAILURES" -gt 0 ]]; then
	STATUS_BADGE="&#x274C;"
	STATUS_TEXT="FAIL"
fi

AVG_COMPLEXITY=$(jq -r '(.summary.avg_complexity // 0) * 10 | round / 10' "$CURRENT")
AVG_LINE_COV=$(jq -r '(.summary.avg_line_coverage // 0) * 10 | round / 10' "$CURRENT")
AVG_CRAP=$(jq -r '(.summary.avg_crap // 0) * 10 | round / 10' "$CURRENT")
CRAP_THRESH=$(jq -r '.summary.crap_threshold // 15' "$CURRENT")
AVG_CONTRACT_COV=$(jq -r '(.summary.avg_contract_coverage // 0) * 10 | round / 10' "$CURRENT")
AVG_GAZE_CRAP=$(jq -r '(.summary.avg_gaze_crap // 0) * 10 | round / 10' "$CURRENT")
GAZE_CRAP_THRESH=$(jq -r '.summary.gaze_crap_threshold // 15' "$CURRENT")
TOTAL_FUNCS=$(jq -r '.summary.total_functions // 0' "$CURRENT")

cat >/tmp/crapload-comment-body.md <<EOF
<!-- crapload-analysis-marker -->
## ${STATUS_BADGE} CRAP Load Analysis: ${STATUS_TEXT}

### Summary

| Metric | Value |
|--------|-------|
| Functions analysed | ${TOTAL_FUNCS} |
| Avg complexity | ${AVG_COMPLEXITY} |
| Avg line coverage | ${AVG_LINE_COV}% |
| Avg CRAP score | ${AVG_CRAP} |
| CRAPload (>= ${CRAP_THRESH}) | ${CRAPLOAD} |
| Avg contract coverage | ${AVG_CONTRACT_COV}% |
| Avg GazeCRAP score | ${AVG_GAZE_CRAP} |
| GazeCRAPload (>= ${GAZE_CRAP_THRESH}) | ${GAZE_CRAPLOAD} |
| Regressions | ${REG_COUNT} |
| Improvements | ${IMP_COUNT} |
| New functions | ${NEW_COUNT} |
EOF

# Add quality metrics if available
QUALITY_COV=$(jq -r '(.quality.summary.average_contract_coverage // empty) * 10 | round / 10' "$GAZE_REPORT" 2>/dev/null || true)
if [[ -n "$QUALITY_COV" ]]; then
	QUALITY_OVERSPEC=$(jq -r '(.quality.summary.average_over_specification // 0) * 10 | round / 10' "$GAZE_REPORT" 2>/dev/null || echo "0")
	cat >>/tmp/crapload-comment-body.md <<EOF
| Avg contract coverage (quality) | ${QUALITY_COV}% |
| Avg over-specification | ${QUALITY_OVERSPEC}% |
EOF
fi

# Add quadrant distribution if available
Q1=$(jq -r '.crap.summary.quadrant_counts.Q1_Safe // empty' "$GAZE_REPORT" 2>/dev/null || true)
if [[ -n "$Q1" ]]; then
	Q2=$(jq -r '.crap.summary.quadrant_counts.Q2_ComplexButTested // 0' "$GAZE_REPORT" 2>/dev/null || echo "0")
	Q3=$(jq -r '.crap.summary.quadrant_counts.Q3_SimpleButUnderspecified // 0' "$GAZE_REPORT" 2>/dev/null || echo "0")
	Q4=$(jq -r '.crap.summary.quadrant_counts.Q4_Dangerous // 0' "$GAZE_REPORT" 2>/dev/null || echo "0")
	cat >>/tmp/crapload-comment-body.md <<EOF

### Quadrant Distribution

| Quadrant | Count |
|----------|-------|
| Q1 Safe | ${Q1} |
| Q2 Complex but Tested | ${Q2} |
| Q3 Simple but Underspecified | ${Q3} |
| Q4 Dangerous | ${Q4} |
EOF
fi

# Add regressions table if any
if [[ -n "$REGRESSIONS" ]]; then
	cat >>/tmp/crapload-comment-body.md <<EOF

### Regressions

| Function | Baseline CRAP | Current CRAP | Delta | Baseline GazeCRAP | Current GazeCRAP | Delta |
|----------|---------------|--------------|-------|-------------------|------------------|-------|
EOF
	printf '%s' "$REGRESSIONS" >>/tmp/crapload-comment-body.md
fi

# Add improvements table if any
if [[ -n "$IMPROVEMENTS" ]]; then
	cat >>/tmp/crapload-comment-body.md <<EOF

### Improvements

| Function | Baseline CRAP | Current CRAP | Delta | Baseline GazeCRAP | Current GazeCRAP | Delta |
|----------|---------------|--------------|-------|-------------------|------------------|-------|
EOF
	printf '%s' "$IMPROVEMENTS" >>/tmp/crapload-comment-body.md
fi

# Add new functions table if any
if [[ -n "$NEW_FUNCTIONS" ]]; then
	cat >>/tmp/crapload-comment-body.md <<EOF

### New Functions

| Status | Function | CRAP | GazeCRAP | Note |
|--------|----------|------|----------|------|
EOF
	printf '%s' "$NEW_FUNCTIONS" >>/tmp/crapload-comment-body.md
fi

# Add analysis warnings if any
FAILED_STEPS=$(jq -r '.errors | to_entries[] | select(.value != null) | "- **\(.key)**: \(.value)"' "$GAZE_REPORT" 2>/dev/null || true)
if [[ -n "$FAILED_STEPS" ]]; then
	cat >>/tmp/crapload-comment-body.md <<EOF

### Analysis Warnings

$FAILED_STEPS
EOF
fi

# Add footer
cat >>/tmp/crapload-comment-body.md <<EOF

[View full analysis logs](${GITHUB_SERVER_URL}/${GITHUB_REPOSITORY}/actions/runs/${GITHUB_RUN_ID})
EOF
