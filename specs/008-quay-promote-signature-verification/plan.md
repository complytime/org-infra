# Plan: Quay promote + destination verify (008)

**Spec:** [spec.md](./spec.md) | **Workflow:** [`resuable_publish_quay.yml`](../../.github/workflows/resuable_publish_quay.yml)

## Objectives

1. Close the **“no signatures found”** gap on **Quay** after `cosign copy` + optional `--only=…`
   while keeping **`verify_signature: true`** meaningful.
2. Record the **decision** (options A / B / C in the spec) with **E2E** evidence and **downstream**
   attestation expectations.

## Phases

### Phase 0 — Evidence (complete for draft)

- Capture **failing** run logs: source verify OK, dest verify fails.
- Capture **passing** run: **`oras copy -r`** to Quay, dest verify OK.
- Note **Quay UI** may show “empty” layers for **Gemara** bundles; **CLI** is acceptance.

### Phase 1 — Design / review

- Team review: **cosign-only** vs **oras recursive** vs **split by registry** (see spec).
- **SBOM / vulnerability** attestation: confirm what **`cosign verify` / org CI** require vs
  out-of-band policies.

### Phase 2 — Implementation (org-infra)

- Update `resuable_publish_quay.yml` per chosen option; pin **ORAS** if used.
- **Tests:** at least one **E2E** (GHCR → Quay) on a **test** namespace; document **Quay** robot
  requirements.

### Phase 3 — Callers

- **complytime-policies** (and any other `workflow_call` users) bump **SHA**; **no** logic change
  in thin callers if inputs/outputs of `resuable_publish_quay` are unchanged.
- **Retire** or refresh **org-infra-tests** mirror when **main** is aligned.

## Deliverables

- Merged `resuable_publish_quay.yml` with documented behavior.
- This **spec** updated: **Implementation log** + **Status** to **Ready** (or **Superseded** if
  obsoleted by a newer spec).
- **README** or **reusable** header block pointing to **008** for “why oras on Quay.”
