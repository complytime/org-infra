# Vertex AI Workload Identity Federation Setup

This runbook configures keyless authentication from GitHub Actions to Google
Cloud Vertex AI using Workload Identity Federation (WIF). It enables the
CI council review workflow to call Claude models on Vertex AI without
long-lived credentials.

## Prerequisites

- `gcloud` CLI authenticated with Owner or IAM Admin on the target project
- The target GCP project with Vertex AI API enabled
- GitHub organization admin access (for org-level secrets)

## Project Details

| Resource | Value |
|----------|-------|
| GCP Project ID | `itpc-gcp-prodsec-eng-claude` |
| GCP Project Number | `909559566812` |
| GitHub Org | `complytime` |
| GitHub Org ID | `181758273` |
| Vertex AI Region | `us-east5` (Claude availability) |

## Step 1: Enable Required APIs

WIF requires IAM, STS, and IAM Credentials APIs in addition to Vertex AI
(already enabled).

```bash
gcloud services enable \
  iam.googleapis.com \
  cloudresourcemanager.googleapis.com \
  iamcredentials.googleapis.com \
  sts.googleapis.com \
  --project=itpc-gcp-prodsec-eng-claude
```

## Step 2: Create Workload Identity Pool

The pool is a logical grouping for external identities. One pool can serve
all ComplyTime repositories.

```bash
gcloud iam workload-identity-pools create "github-actions" \
  --project="itpc-gcp-prodsec-eng-claude" \
  --location="global" \
  --display-name="GitHub Actions Pool" \
  --description="WIF pool for ComplyTime GitHub Actions workflows"
```

Verify creation:

```bash
gcloud iam workload-identity-pools describe "github-actions" \
  --project="itpc-gcp-prodsec-eng-claude" \
  --location="global" \
  --format="value(name)"
```

Expected output:
```
projects/909559566812/locations/global/workloadIdentityPools/github-actions
```

## Step 3: Create OIDC Provider

The provider establishes trust with GitHub's OIDC issuer. The attribute
condition restricts access to the ComplyTime org using the **numeric org ID**
(immutable, not vulnerable to name-squatting).

```bash
gcloud iam workload-identity-pools providers create-oidc "complytime" \
  --project="itpc-gcp-prodsec-eng-claude" \
  --location="global" \
  --workload-identity-pool="github-actions" \
  --display-name="ComplyTime GitHub" \
  --attribute-mapping="\
google.subject=assertion.sub,\
attribute.actor=assertion.actor,\
attribute.repository=assertion.repository,\
attribute.repository_owner_id=assertion.repository_owner_id,\
attribute.repository_id=assertion.repository_id,\
attribute.ref=assertion.ref" \
  --attribute-condition="assertion.repository_owner_id == '181758273'" \
  --issuer-uri="https://token.actions.githubusercontent.com"
```

### Attribute Mapping Rationale

| Mapped Attribute | Source Claim | Purpose |
|-----------------|-------------|---------|
| `google.subject` | `assertion.sub` | Required. Unique identity per workflow run |
| `attribute.repository_owner_id` | `assertion.repository_owner_id` | Gate condition: only ComplyTime org |
| `attribute.repository_id` | `assertion.repository_id` | Optional: per-repo restrictions |
| `attribute.repository` | `assertion.repository` | Audit logging (human-readable) |
| `attribute.actor` | `assertion.actor` | Audit logging |
| `attribute.ref` | `assertion.ref` | Optional: branch restrictions |

### Security Notes

- The condition uses `repository_owner_id` (numeric `181758273`), not the
  string name `complytime`. Numeric IDs are immutable and cannot be reused
  if the org is deleted, preventing name-squatting attacks.
- All repositories under the `complytime` GitHub org can authenticate.
  To restrict to specific repos, add:
  `&& assertion.repository_id == '1084101898'` (org-infra only).
- Fork PRs **cannot** obtain OIDC tokens from GitHub Actions, so they
  cannot authenticate through WIF. This is enforced by GitHub, not GCP.

## Step 4: Create Service Account

A dedicated service account for council review with minimal permissions.

```bash
gcloud iam service-accounts create "ci-council-review" \
  --project="itpc-gcp-prodsec-eng-claude" \
  --display-name="CI Council Review" \
  --description="Service account for AI council review in GitHub Actions CI"
```

## Step 5: Grant Vertex AI Permissions

Grant the service account permission to call Vertex AI prediction endpoints.
`roles/aiplatform.user` is the minimum role needed for `rawPredict` calls
to Claude models.

```bash
gcloud projects add-iam-policy-binding "itpc-gcp-prodsec-eng-claude" \
  --role="roles/aiplatform.user" \
  --member="serviceAccount:ci-council-review@itpc-gcp-prodsec-eng-claude.iam.gserviceaccount.com" \
  --condition=None
```

## Step 6: Allow WIF to Impersonate the Service Account

Grant the GitHub Actions federated identity permission to impersonate the
service account. This binding is scoped to the ComplyTime org.

```bash
gcloud iam service-accounts add-iam-policy-binding \
  "ci-council-review@itpc-gcp-prodsec-eng-claude.iam.gserviceaccount.com" \
  --project="itpc-gcp-prodsec-eng-claude" \
  --role="roles/iam.workloadIdentityUser" \
  --member="principalSet://iam.googleapis.com/projects/909559566812/locations/global/workloadIdentityPools/github-actions/attribute.repository_owner_id/181758273"
```

This allows **any** repo in the `complytime` org to authenticate. To
restrict to a single repo (e.g., org-infra only during testing):

```bash
# Alternative: restrict to org-infra only
gcloud iam service-accounts add-iam-policy-binding \
  "ci-council-review@itpc-gcp-prodsec-eng-claude.iam.gserviceaccount.com" \
  --project="itpc-gcp-prodsec-eng-claude" \
  --role="roles/iam.workloadIdentityUser" \
  --member="principalSet://iam.googleapis.com/projects/909559566812/locations/global/workloadIdentityPools/github-actions/attribute.repository_id/1084101898"
```

## Step 7: Configure GitHub Organization Secrets

Set these as **organization secrets** in the ComplyTime GitHub org, scoped
to repositories that need council review.

| Secret Name | Value | Notes |
|-------------|-------|-------|
| `GCP_WORKLOAD_IDENTITY_PROVIDER` | `projects/909559566812/locations/global/workloadIdentityPools/github-actions/providers/complytime` | Full provider resource name |
| `GCP_SERVICE_ACCOUNT` | `ci-council-review@itpc-gcp-prodsec-eng-claude.iam.gserviceaccount.com` | Service account email |
| `GCP_PROJECT_ID` | `itpc-gcp-prodsec-eng-claude` | Project ID |

These are the GCP-native path secrets. The workflow also accepts the
generic `AI_API_KEY` and `AI_API_ENDPOINT` secrets as a fallback for
non-GCP providers (Anthropic direct, OpenAI, etc.). WIF takes
precedence when both are set.

## Step 8: Test with the Validation Workflow

Push a branch with `.github/workflows/ci_council_review_test.yml` to
org-infra and open a PR. See the workflow file for the test procedure.

## Verification Checklist

- [ ] APIs enabled (`iam`, `sts`, `iamcredentials`, `aiplatform`)
- [ ] WIF pool created and visible in IAM console
- [ ] OIDC provider created with correct attribute condition
- [ ] Service account created with `roles/aiplatform.user`
- [ ] WIF-to-SA binding in place
- [ ] GitHub org secrets configured
- [ ] Test workflow succeeds on an org-member PR
- [ ] Test workflow skips on a fork PR (no OIDC token available)

## Troubleshooting

### "Unable to exchange token" error
- Wait 5 minutes after creating WIF resources (propagation delay)
- Verify the `id-token: write` permission is in the workflow
- Check the attribute condition matches the org ID exactly

### "Permission denied" on Vertex AI
- Verify `roles/aiplatform.user` is granted to the service account
- Check the region in the API URL matches where Claude is available
- Ensure the service account can access the specific model

### Fork PR attempts to authenticate
- This should not happen. `pull_request` events from forks do not
  receive OIDC tokens. If it does, the WIF attribute condition
  (`repository_owner_id == '181758273'`) blocks non-ComplyTime repos.

## Cost Estimate

Per council review run (5 personas, ~1000-line diff):
- Input: ~5K-25K tokens across 5 calls
- Output: ~2K-10K tokens across 5 calls
- At Claude Sonnet 4.6 Vertex rates (`claude-sonnet-4-6`): ~$0.05-0.20 per review
- Gate checks prevent unnecessary runs (drafts, dependabot, forks,
  binary-only changes)

## Architecture

```
GitHub Actions (pull_request)
  |
  | 1. Request OIDC token (id-token: write)
  v
GitHub OIDC Provider (token.actions.githubusercontent.com)
  |
  | 2. JWT with org_id, repo_id, actor claims
  v
google-github-actions/auth@v3
  |
  | 3. Exchange OIDC token for GCP access token via STS
  v
GCP Workload Identity Federation
  |
  | 4. Validate attribute condition (org_id == 181758273)
  | 5. Impersonate ci-council-review service account
  v
GCP Service Account (ci-council-review@...)
  |
  | 6. Short-lived OAuth 2.0 access token (~1 hour)
  v
Vertex AI rawPredict (Claude models)
  |
  | 7. Council review responses
  v
GitHub PR Comment (peter-evans/create-or-update-comment)
```
