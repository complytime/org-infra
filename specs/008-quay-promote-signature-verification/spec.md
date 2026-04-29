# Feature specification: Quay cross-registry promote + destination `cosign verify`

**Id:** `008-quay-promote-signature-verification`  
**Created:** 2026-04-23  
**Status:** Draft (design + E2E evidence)  
**Workflow:** [`.github/workflows/resuable_publish_quay.yml`](../../.github/workflows/resuable_publish_quay.yml)

**Related (handoff / E2E context, not changes to older org-infra feature specs):**

- [complytime-policies
  `002-policy-oci-quay-e2e-supply-chain`](https://github.com/complytime/complytime-policies/blob/main/specs/002-policy-oci-quay-e2e-supply-chain/spec.md)
- [oci-artifact
  `002-gemara-oci-supply-chain-e2e`](https://github.com/complytime/oci-artifact/blob/main/specs/002-gemara-oci-supply-chain-e2e/spec.md)

## Problem statement

The reusable **Promote** workflow copies a **signed, attested** image (or OCI object addressed like
an image) from a **staging** registry (typically **GHCR**) to **Quay**, then runs **`cosign verify`**
on the **destination** digest when **`verify_signature: true`**.

**Observed failure (2026-04, policy OCI E2E):** **Source** `cosign verify` succeeded, but
**destination** `cosign verify` returned **“no signatures found”** after:

1. `cosign copy` from `source@digest` → `dest:tag`, and
2. A follow-up `cosign copy --only=sig,att,sbom` to the same destination tag (mitigation for
   incomplete copies per cosign#3379–style issues).

A **green E2E** in a public **test mirror** was achieved by replacing the promote **copy** step with
**`oras copy -r`**, which copies the **image and referring artifacts** (the graph ORAS can traverse)
so that **`cosign verify`** on Quay for that digest **succeeds**. This is a **behavioral change** to
the reusable (adds **ORAS** setup, changes copy mechanism) and requires **formal review**, **registry
compatibility** checks, and alignment with the **org supply-chain** story.

## Goals

1. **Default:** `verify_signature: true` remains a **reliable** gate: if promote completes, **destination
   verify** matches **source** under the same identity/OIDC policy (unless a **documented** org
   exception applies).
2. **Document** the trade-off between:
   - **`cosign copy`** (and optional **`--only=…`**) as the “native” cosign path, and
   - **Recursive copy** (e.g. **`oras copy -r`**, or future **`oras copy`/`skopeo`** patterns) when a
     destination registry (notably **Quay**) does not present copied signature/referrer objects in a
     way **cosign** can verify after a **single** `cosign copy`.
3. **Clarify** for consumers: this workflow promotes the **cosign “subject”** and related **in-graph**
   objects. **Attestation types** that are **out of graph** (e.g. separate vulnerability pipelines)
   are **out of scope** of this file unless the org **explicitly** extends the reusable contract.

## Non-goals (v1 of this spec)

- Redefining **Gemara** bundle layout (owned by **go-gemara** + **oci-artifact**).
- Quay **UI** “layer” display (OCI **artifact** bundles are not always Docker **layer**-shaped).
- Mandating a single tool for **all** OCI promotion in the org (only this **reusable** + Quay+GHCR
  keyless path).

## Design options (to decide in PR / review)

| Option | Description | Pros | Cons / risks |
|--------|-------------|------|----------------|
| **A** | Keep **only** `cosign copy` + `cosign copy --only=sig,att,sbom` | Stays in cosign-native APIs | E2E showed **insufficient** for some Quay+verify combinations |
| **B** | **`oras copy -r`** (with pinned **setup-oras**) as the **sole** copy for promote | **E2E green** on test Quay with full referrer copy | **Duplication** risk if other teams rely on A; must document cosign **deprecation** guidance |
| **C** | **B** for Quay (or a flag), **A** for other `dest_registry` | Registry-specific behavior | **Branching** + test matrix; document **when** to use which |

**Recommendation (from field evidence, not yet approved):** **C** or **B** until **cosign/Quay**
interoperability catches up; record **provenance** of the chosen path in this spec’s
**Implementation** section when merged.

## Relationship to other work

- [PR #211](https://github.com/complytime/org-infra/pull/211) (Gemara-only `reusable_publish_oras` and
  policy pipeline alignment).
- **complytime-policies** thin caller: [complytime-policies#5](https://github.com/complytime/complytime-policies/issues/5),
  spec [001-policy-oci-publish](https://github.com/complytime/complytime-policies/blob/main/specs/001-policy-oci-publish/team-briefing-2026-04-23.md).
- **Test mirror (interim):** [org-infra-tests](https://github.com/sonupreetam/org-infra-tests) used
  to validate `workflow_call` + **`allow_unprotected_ref`**; **retire** when `complytime/org-infra`
  **main** is at **parity** with the agreed promote behavior.

## Acceptance criteria (draft)

- [ ] E2E on a **test Quay** org: **source** and **dest** `cosign verify` **both** succeed with
  **default** `verify_signature: true` for a **Gemara** staging image (GHCR) produced by
  `reusable_publish_oras` + `reusable_sign_and_verify`.
- [ ] Documentation in **this** spec and in **reusable** header comments: **Quay** vs other
  registries if behavior diverges.
- [ ] If **`oras copy -r`**: pinned **ORAS** setup version; no floating `@main` for setup actions.
- [ ] **SBOM / vuln** attestation expectations: either **covered** by the promote graph and verify
  step, or **explicitly** called out as **not guaranteed** by this promote (separate org policy).

## Implementation log

| Date | Change | Evidence |
|------|--------|----------|
| 2026-04-23 | Spec opened; options A/B/C from E2E troubleshooting | complytime-policies team briefing; test mirror run with `oras copy -r` |

*Update this table when `resuable_publish_quay.yml` is merged to `main` with a **decision**.*

## References

- Cosign `copy` deprecation text (suggests **`oras copy -r`** for recursive / referring artifacts).
- [sigstore/cosign#3379](https://github.com/sigstore/cosign/issues/3379) (copy/verify class of issues, context only).
