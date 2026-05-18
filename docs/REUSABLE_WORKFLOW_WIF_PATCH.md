# WIF Integration Patch for reusable_council_review.yml

This document specifies the changes needed to add Vertex AI WIF support
to `reusable_council_review.yml` from PR #218. The changes implement the
two-tier provider interface: GCP Vertex AI (WIF) takes precedence when
configured, with generic API key as fallback.

## Change 1: Add WIF secrets to workflow_call

Add three optional secrets for the GCP-native path alongside the
existing `AI_API_KEY` and `AI_API_ENDPOINT`:

```yaml
    secrets:
      AI_API_KEY:
        description: "API key for the AI provider (generic path)"
        required: false
      AI_API_ENDPOINT:
        description: "Base URL for the AI API (generic path)"
        required: false
      GCP_WORKLOAD_IDENTITY_PROVIDER:
        description: "WIF provider resource name (Vertex AI path)"
        required: false
      GCP_SERVICE_ACCOUNT:
        description: "GCP service account email (Vertex AI path)"
        required: false
      GCP_PROJECT_ID:
        description: "GCP project ID (Vertex AI path)"
        required: false
```

## Change 2: Add Vertex AI inputs

Add region and model inputs for the Vertex AI path:

```yaml
    inputs:
      # ... existing inputs ...
      vertex_ai_region:
        description: "GCP region for Vertex AI (default: us-east5)"
        required: false
        type: string
        default: "us-east5"
      vertex_ai_model:
        description: "Claude model name on Vertex AI"
        required: false
        type: string
        default: "claude-sonnet-4-6"
```

## Change 3: Update gate check for two-tier detection

Replace the single `HAS_API_KEY` check with two-tier detection and
output the detected provider:

```yaml
      - name: Check gate conditions
        id: gate
        env:
          PR_AUTHOR: ${{ github.event.pull_request.user.login }}
          PR_DRAFT: ${{ github.event.pull_request.draft }}
          HAS_WIF: ${{ secrets.GCP_WORKLOAD_IDENTITY_PROVIDER != '' }}
          HAS_API_KEY: ${{ secrets.AI_API_KEY != '' }}
        run: |
          # Gate 1-2: dependabot, draft (unchanged)
          # ...

          # Gate 3: Detect provider or skip
          if [[ "${HAS_WIF}" == "true" ]]; then
            echo "provider=vertex-wif" >> "$GITHUB_OUTPUT"
            echo "should_review=true" >> "$GITHUB_OUTPUT"
          elif [[ "${HAS_API_KEY}" == "true" ]]; then
            echo "provider=generic-api" >> "$GITHUB_OUTPUT"
            echo "should_review=true" >> "$GITHUB_OUTPUT"
          else
            echo "should_review=false" >> "$GITHUB_OUTPUT"
            echo "skip_reason=No AI credentials configured" >> "$GITHUB_OUTPUT"
            exit 0
          fi
          echo "skip_reason=" >> "$GITHUB_OUTPUT"
```

Add `provider` to the gate-checks outputs:

```yaml
    outputs:
      should_review: ${{ steps.gate.outputs.should_review }}
      review_mode: ${{ steps.detect-mode.outputs.review_mode }}
      skip_reason: ${{ steps.gate.outputs.skip_reason }}
      provider: ${{ steps.gate.outputs.provider }}
```

## Change 4: Add WIF auth step to council-review job

Add an authentication step before the review step. This step only runs
on the WIF path. It requires `id-token: write` permission.

```yaml
  council-review:
    name: Council Review
    needs: gate-checks
    if: needs.gate-checks.outputs.should_review == 'true'
    runs-on: ubuntu-latest
    permissions:
      contents: read
      id-token: write
      pull-requests: write
    steps:
      # ... existing steps (checkout, check-agents, context, diff) ...

      - name: Authenticate to Google Cloud (WIF path)
        id: gcp-auth
        if: needs.gate-checks.outputs.provider == 'vertex-wif'
        uses: google-github-actions/auth@v3
        with:
          project_id: ${{ secrets.GCP_PROJECT_ID }}
          workload_identity_provider: ${{ secrets.GCP_WORKLOAD_IDENTITY_PROVIDER }}
          service_account: ${{ secrets.GCP_SERVICE_ACCOUNT }}
          token_format: access_token

      - name: Run council review
        # ... update env to include WIF token and provider ...
        env:
          AI_PROVIDER: ${{ needs.gate-checks.outputs.provider }}
          AI_API_KEY: ${{ secrets.AI_API_KEY }}
          AI_API_ENDPOINT: ${{ secrets.AI_API_ENDPOINT }}
          GCP_ACCESS_TOKEN: ${{ steps.gcp-auth.outputs.access_token || '' }}
          GCP_PROJECT_ID: ${{ secrets.GCP_PROJECT_ID }}
          VERTEX_REGION: ${{ inputs.vertex_ai_region }}
          VERTEX_MODEL: ${{ inputs.vertex_ai_model }}
          # ... existing env vars ...
```

## Change 5: Two-tier API call logic in the review step

Replace the placeholder review step with actual API calls that detect
the provider and use the correct endpoint/auth:

```bash
call_ai_api() {
  local system_prompt="$1"
  local user_prompt="$2"

  if [[ "${AI_PROVIDER}" == "vertex-wif" ]]; then
    ENDPOINT="https://${VERTEX_REGION}-aiplatform.googleapis.com/v1/projects/${GCP_PROJECT_ID}/locations/${VERTEX_REGION}/publishers/anthropic/models/${VERTEX_MODEL}:rawPredict"

    curl -s -X POST "${ENDPOINT}" \
      -H "Authorization: Bearer ${GCP_ACCESS_TOKEN}" \
      -H "Content-Type: application/json" \
      -d "$(jq -n \
        --arg system "${system_prompt}" \
        --arg user "${user_prompt}" \
        '{
          anthropic_version: "vertex-2023-10-16",
          max_tokens: 4096,
          system: $system,
          messages: [{role: "user", content: $user}]
        }')"
  else
    ENDPOINT="${AI_API_ENDPOINT:-https://api.anthropic.com/v1/messages}"
    MODEL="${AI_MODEL:-claude-sonnet-4-6-20250514}"

    curl -s -X POST "${ENDPOINT}" \
      -H "x-api-key: ${AI_API_KEY}" \
      -H "anthropic-version: 2023-06-01" \
      -H "Content-Type: application/json" \
      -d "$(jq -n \
        --arg model "${MODEL}" \
        --arg system "${system_prompt}" \
        --arg user "${user_prompt}" \
        '{
          model: $model,
          max_tokens: 4096,
          system: $system,
          messages: [{role: "user", content: $user}]
        }')"
  fi
}
```

## Change 6: Update consumer workflow (ci_council_review.yml)

Pass the WIF secrets from the consumer to the reusable workflow:

```yaml
jobs:
  council:
    name: AI Council Review
    uses: complytime/org-infra/.github/workflows/reusable_council_review.yml@main
    permissions:
      contents: read
      id-token: write
      pull-requests: write
    secrets:
      AI_API_KEY: ${{ secrets.AI_API_KEY }}
      AI_API_ENDPOINT: ${{ secrets.AI_API_ENDPOINT }}
      GCP_WORKLOAD_IDENTITY_PROVIDER: ${{ secrets.GCP_WORKLOAD_IDENTITY_PROVIDER }}
      GCP_SERVICE_ACCOUNT: ${{ secrets.GCP_SERVICE_ACCOUNT }}
      GCP_PROJECT_ID: ${{ secrets.GCP_PROJECT_ID }}
```

Note the addition of `id-token: write` permission (required for WIF).

## Change 7: Add concurrency control

Add to the consumer workflow:

```yaml
concurrency:
  group: council-review-${{ github.event.pull_request.number }}
  cancel-in-progress: true
```
