# Design

## Context

Five branch-protection policy files in `compliance/ampel/branch-protection/`
currently have no `when` guards. They always evaluate, even when the attestation
bundle contains no matching predicate types. See proposal.md for motivation.

The `Makefile` currently runs `lint-yaml` and `lint-python` under the `lint`
target. There is no JSON or policy-specific linting.

## Goals / Non-Goals

**Goals:**

- Branch-protection policies produce `SKIP` in multi-predicate bundles when their
  evidence types are absent.
- A lint check catches drift between `when` expressions and tenet predicate types.

**Non-Goals:**

- Auto-generating `when` expressions from tenet declarations (would require a
  build step or templating tool not currently in the repo).
- Validating ampel policy schema beyond predicate type consistency.

## Decisions

### 1. `when` expression uses `predicates.exists()` filtered by `predicate_type`

The `when` expression filters by `predicate_type` field:

```
predicates.exists(p, p.predicate_type == '<url-1>' || p.predicate_type == '<url-2>')
```

**Alternative considered**: `size(predicates) > 0`. Rejected because `predicates`
in the `when` context contains ALL loaded attestations regardless of type, so the
expression is always true when any attestation exists. Confirmed by testing
against ampel 1.4.2.

### 2. Lint check uses `jq` over `compliance/ampel/**/*.json`

The lint check is a shell loop that uses `jq` to:
1. Extract all unique predicate type URLs from `tenets[].predicates.types`
2. Check each one appears in the `when.expression` string via `contains()`
3. Report any missing types and exit non-zero

**Alternative considered**: A Python script using the `json` module. Rejected
because `jq` is already a de facto dependency across CI workflows (70+ uses in
`.github/workflows/`), requires no venv, and keeps the check to ~15 lines of
shell. A Python approach would require venv activation for consistency with the
existing lint targets, adding unnecessary overhead for a string-containment
check.

**Alternative considered**: Skipping the lint check entirely. Rejected because the
duplication between `when.expression` and `tenets[].predicates.types` is a real
consistency hazard, and the check is trivial to implement.

### 3. Files without `when` are skipped, not failed

The lint check skips policy files that have no `when` field. This allows
incremental adoption: future policy domains can be added without `when` guards
initially and gain them later without breaking CI.

**Alternative considered**: Requiring `when` on all policy files. Rejected as
overly prescriptive -- not all policy bundles will be multi-predicate.

### 4. `lint-policies` is a separate Makefile target wired into `lint`

```
lint: lint-yaml lint-python lint-policies
```

This follows the existing pattern where `lint` aggregates sub-targets. The new
target is independently runnable (`make lint-policies`) for fast iteration.

**Alternative considered**: Inlining the check into `lint-yaml`. Rejected because
this is JSON linting, not YAML linting, and conflating them would be misleading.

## Risks / Trade-offs

- **[Risk] `jq` not installed locally** -- The lint target requires `jq`. If a
  developer does not have it, `make lint` fails. Mitigation: `jq` is ubiquitous
  on Linux/macOS and pre-installed on all GitHub Actions runners. The error
  message from a missing `jq` is self-explanatory.

- **[Risk] `contains()` is a substring match** -- If two predicate type URLs
  share a common suffix (e.g., `foo/bar.yaml` and `baz/bar.yaml`), a `contains()`
  check could produce a false positive. Mitigation: the current predicate type
  URLs are fully qualified paths with distinct prefixes. If this becomes a
  concern, the check can be tightened to exact-match parsing later.
