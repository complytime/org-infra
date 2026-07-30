#!/usr/bin/env bash
set -euo pipefail

# YAML-structure assertions for tag_push_token secret
# Verifies spec scenarios against reusable_release_preflight.yml

WORKFLOW=".github/workflows/reusable_release_preflight.yml"
FAILURES=0
TESTS=0

pass() { TESTS=$((TESTS + 1)); echo "PASS: $1"; }
fail() { TESTS=$((TESTS + 1)); FAILURES=$((FAILURES + 1)); echo "FAIL: $1"; }

# Resolve path relative to repo root (support running from any directory)
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
WORKFLOW_PATH="$REPO_ROOT/$WORKFLOW"

if [[ ! -f "$WORKFLOW_PATH" ]]; then
  echo "ERROR: Workflow file not found: $WORKFLOW_PATH"
  exit 1
fi

# ---------------------------------------------------------------------------
# 4.1 Assert secrets.tag_push_token exists with required: false
# ---------------------------------------------------------------------------

# Check the secret name exists under the secrets key
if grep -q 'tag_push_token:' "$WORKFLOW_PATH"; then
  pass "4.1a secrets.tag_push_token is declared in the workflow"
else
  fail "4.1a secrets.tag_push_token is NOT declared in the workflow"
fi

# Check required: false appears after the tag_push_token declaration
# Extract the secrets.tag_push_token block and verify required: false
TAG_PUSH_BLOCK=$(sed -n '/^    secrets:/,/^    [a-z]/p' "$WORKFLOW_PATH" \
  | sed -n '/tag_push_token:/,/^      [a-z]\|^    [a-z]/p')

if echo "$TAG_PUSH_BLOCK" | grep -q 'required: false'; then
  pass "4.1b tag_push_token has required: false"
else
  fail "4.1b tag_push_token does NOT have required: false"
fi

# ---------------------------------------------------------------------------
# 4.2 Assert the fallback expression appears only in "Create and push tag"
# ---------------------------------------------------------------------------

FALLBACK_EXPR="secrets.tag_push_token != '' && secrets.tag_push_token || secrets.GITHUB_TOKEN"

# Count total occurrences of the fallback expression
FALLBACK_COUNT=$(grep -c "$FALLBACK_EXPR" "$WORKFLOW_PATH" || true)

if [[ "$FALLBACK_COUNT" -eq 1 ]]; then
  pass "4.2a fallback expression appears exactly once in the workflow"
else
  fail "4.2a fallback expression appears $FALLBACK_COUNT times (expected 1)"
fi

# Verify the fallback expression is in the "Create and push tag" step
# Extract the step block and check for the expression
CREATE_TAG_BLOCK=$(sed -n '/- name: Create and push tag/,/- name:/p' "$WORKFLOW_PATH")

if echo "$CREATE_TAG_BLOCK" | grep -q "$FALLBACK_EXPR"; then
  pass "4.2b fallback expression is in the 'Create and push tag' step"
else
  fail "4.2b fallback expression is NOT in the 'Create and push tag' step"
fi

# ---------------------------------------------------------------------------
# 4.3 Assert no other step references secrets.tag_push_token (negative test)
# ---------------------------------------------------------------------------

# Find all lines referencing secrets.tag_push_token
# Exclude: the secrets declaration block (top-level secrets: section) and
# the "Create and push tag" step
#
# Strategy: find line numbers of all secrets.tag_push_token references,
# then check each is either in the declaration block or the tag-creation step.

# Get line number of the secrets declaration section
SECRETS_DECL_START=$(grep -n '^    secrets:' "$WORKFLOW_PATH" | head -1 | cut -d: -f1)

# Get line number range of the "Create and push tag" step
CREATE_TAG_LINE=$(grep -n 'name: Create and push tag' "$WORKFLOW_PATH" | head -1 | cut -d: -f1)

# Get all line numbers referencing tag_push_token
REFERENCE_LINES=$(grep -n 'tag_push_token' "$WORKFLOW_PATH" | cut -d: -f1)

UNEXPECTED_REFS=0
for line_num in $REFERENCE_LINES; do
  # Allow references in the secrets declaration block (lines near SECRETS_DECL_START)
  # The declaration block spans ~7 lines from the secrets: key
  if [[ -n "$SECRETS_DECL_START" ]] && \
     [[ "$line_num" -ge "$SECRETS_DECL_START" ]] && \
     [[ "$line_num" -le $((SECRETS_DECL_START + 10)) ]]; then
    continue
  fi

  # Allow references in the "Create and push tag" step
  # The step spans ~30 lines from its name
  if [[ -n "$CREATE_TAG_LINE" ]] && \
     [[ "$line_num" -ge "$CREATE_TAG_LINE" ]] && \
     [[ "$line_num" -le $((CREATE_TAG_LINE + 35)) ]]; then
    continue
  fi

  # Allow references in the header comment block (lines 1-33)
  if [[ "$line_num" -le 33 ]]; then
    continue
  fi

  UNEXPECTED_REFS=$((UNEXPECTED_REFS + 1))
  echo "  WARNING: Unexpected tag_push_token reference at line $line_num"
done

if [[ "$UNEXPECTED_REFS" -eq 0 ]]; then
  pass "4.3 no other step references secrets.tag_push_token"
else
  fail "4.3 found $UNEXPECTED_REFS unexpected reference(s) to secrets.tag_push_token"
fi

# ---------------------------------------------------------------------------
# 4.4 Assert description contains exact warning text
# ---------------------------------------------------------------------------

EXPECTED_DESC="Optional elevated token for tag creation. When provided, the tag event can trigger downstream workflows. WARNING: Do not use an elevated token in downstream workflows that re-invoke this preflight workflow, or you will create a recursive loop."

# Extract the description field from the tag_push_token secret block.
# The description uses YAML folded scalar (>-) with 10-space indented
# continuation lines (lines 78-81 in the current file). We grab lines
# between "description: >-" and "required:" within the tag_push_token
# block, strip the marker line and the required line, dedent, then
# join with single spaces (matching >- folding semantics).
DESC_BLOCK=$(sed -n '/^      tag_push_token:/,/^        required:/p' "$WORKFLOW_PATH" \
  | sed -n '/description: >-/,/required:/p' \
  | grep -v 'description: >-' \
  | grep -v 'required:' \
  | sed 's/^          //' \
  | tr '\n' ' ' \
  | sed 's/  */ /g' \
  | sed 's/^ *//;s/ *$//')

if [[ "$DESC_BLOCK" == "$EXPECTED_DESC" ]]; then
  pass "4.4 description contains exact warning text"
else
  fail "4.4 description does not match expected warning text"
  echo "  Expected: $EXPECTED_DESC"
  echo "  Got:      $DESC_BLOCK"
fi

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
