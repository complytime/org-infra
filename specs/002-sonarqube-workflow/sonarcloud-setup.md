# SonarCloud Setup Guide

This guide covers the required SonarCloud configuration steps before implementing the reusable workflow in your repository.

## Prerequisites

- GitHub organization or repository access
- Administrative access to create SonarCloud projects
- Permissions to configure repository or organization secrets

## Step 1: SonarCloud Organization Setup

### First-Time Setup (Organization Admin)

If your organization doesn't have a SonarCloud account:

1. Navigate to [SonarCloud](https://sonarcloud.io)
2. Click **Log in** and authenticate with GitHub
3. Click **Analyze new project**
4. Select **Import an organization from GitHub**
5. Choose your GitHub organization
6. Install the SonarCloud GitHub App on your organization
7. Configure which repositories SonarCloud can access

### Organization Key

Your SonarCloud organization key is typically your GitHub organization name in lowercase. You can find it at:
- SonarCloud → **My Account** → **Organizations** tab
- Or in the URL: `https://sonarcloud.io/organizations/<organization-key>`

This key will be used as the `sonar_organization` input in the workflow.

## Step 2: Create a SonarCloud Project

### 2.1 Import Repository

1. Go to SonarCloud and click the **+** icon in the top right
2. Select **Analyze new project**
3. Choose your repository from the list
4. Click **Set Up**

### 2.2 Configure Project Key

The project key is automatically generated in the format:
```
<organization-key>_<repository-name>
```

**Example:** For organization `rh-psce` and repository `complyctl`:
```
rh-psce_complyctl
```

This key will be used as the `sonar_project_key` input in the workflow.

### 2.3 Choose Analysis Method

When prompted for analysis method:
1. Select **With GitHub Actions**
2. SonarCloud will display setup instructions

## Step 3: Generate SonarCloud Token

Tokens are required for the workflow to publish analysis results.

### 3.1 Create Token

1. In SonarCloud, click your profile icon (top right)
2. Select **My Account** → **Security** tab
3. Under **Generate Tokens**:
   - **Name:** `<repository-name>-github-actions` (e.g., `complyctl-github-actions`)
   - **Type:** Select **Project Analysis Token**
   - **Project:** Select your project from the dropdown
   - **Expires in:** Choose appropriate expiration (e.g., 90 days, No expiration)
4. Click **Generate**
5. **Important:** Copy the token immediately - it won't be shown again

### 3.2 Token Permissions

The token requires these permissions:
- **Execute Analysis:** Publish analysis results to SonarCloud

Project Analysis Tokens are automatically scoped to the specific project and cannot be used for other projects.

## Step 4: Configure GitHub Secrets

### Repository Secret (Recommended for Single Repository)

1. Navigate to your GitHub repository
2. Go to **Settings** → **Secrets and variables** → **Actions**
3. Click **New repository secret**
4. Add the secret:
   - **Name:** `SONAR_TOKEN`
   - **Value:** Paste the token from Step 3
5. Click **Add secret**

### Organization Secret (For Multiple Repositories)

If multiple repositories share the same SonarCloud organization:

1. Navigate to your GitHub organization settings
2. Go to **Secrets and variables** → **Actions**
3. Click **New organization secret**
4. Add the secret:
   - **Name:** `SONAR_TOKEN`
   - **Value:** Paste the token from Step 3
   - **Repository access:** Select repositories that need access
5. Click **Add secret**

**Note:** Organization secrets require separate tokens per project unless you use a User Token (less secure, not recommended for automation).

### Alternative: Multiple Project Tokens

For organizations with many projects, consider:
- Creating project-specific secrets: `SONAR_TOKEN_COMPLYCTL`, `SONAR_TOKEN_MYAPP`, etc.
- Updating consumer workflows to reference the appropriate secret
- Using organization-level secrets with repository-specific values

## Step 5: Configure Quality Gates (Optional)

Quality gates define the criteria for passing/failing analysis.

### Use Default Quality Gate

SonarCloud provides a default quality gate called **Sonar way** that includes:
- No new bugs
- No new vulnerabilities
- No new security hotspots
- New code coverage ≥ 80%
- New duplicated lines ≤ 3%
- Maintainability rating on new code ≥ A

Most projects can use this default without customization.

### Create Custom Quality Gate

If you need custom thresholds:

1. Go to **Quality Gates** in SonarCloud
2. Click **Create**
3. Define your conditions:
   - Metrics: Coverage, Duplications, Maintainability, Reliability, Security
   - Thresholds: Set acceptable values
   - Scope: New Code vs Overall Code
4. Save the quality gate
5. Assign it to your project:
   - Go to **Project Settings** → **Quality Gate**
   - Select your custom gate

## Step 6: Configure Project Settings (Optional)

### Main Branch Configuration

SonarCloud auto-detects your main branch, but you can verify:

1. Go to **Project Settings** → **Branches and Pull Requests**
2. Confirm the **Main Branch** is correctly set (e.g., `main` or `master`)


## Step 7: Verification Checklist

Before implementing the workflow, verify:

- [ ] SonarCloud organization is connected to GitHub organization
- [ ] SonarCloud project exists for your repository
- [ ] Project key is noted (format: `org_repo`)
- [ ] SonarCloud token has been generated
- [ ] `SONAR_TOKEN` secret is configured in GitHub
- [ ] Quality gate is assigned to the project
- [ ] Main branch is correctly configured

## Common Configuration Scenarios

### Scenario 1: New Organization, First Project

1. Complete all steps 1-6
2. This creates the foundation for future projects
3. Additional projects only need steps 2-4

### Scenario 2: Existing Organization, New Project

1. Skip step 1 (organization already configured)
2. Complete steps 2-4
3. Optionally complete steps 5-6 if custom configuration needed


## Token Management Best Practices

### Security

- **Never commit tokens** to source code or configuration files
- **Use GitHub Secrets** for all token storage
- **Use Project Analysis Tokens** instead of User Tokens when possible
- **Set expiration dates** and rotate tokens regularly

### Token Rotation

When tokens expire or need rotation:

1. Generate new token in SonarCloud (Step 3)
2. Update GitHub secret with new value
3. Old token is automatically invalidated after expiration
4. No workflow changes required


## Troubleshooting

### "Project not found" Error

**Cause:** Project key mismatch or token doesn't have access
**Solution:**
- Verify `sonar_project_key` matches SonarCloud project key exactly
- Confirm token has permissions for the specific project
- Check organization key is correct

### "Unauthorized" Error

**Cause:** Invalid or expired token
**Solution:**
- Generate new token in SonarCloud
- Update `SONAR_TOKEN` secret in GitHub
- Verify token was copied completely without extra spaces

### Quality Gate Always Failing

**Cause:** Quality gate thresholds too strict for current codebase
**Solution:**
- Review quality gate conditions in SonarCloud
- Focus on "New Code" metrics for gradual improvement
- Temporarily adjust thresholds or use default "Sonar way"


## Next Steps

After completing SonarCloud setup:

1. Follow the [Quickstart Guide](./quickstart.md) to implement the workflow
2. Review results in SonarCloud dashboard
3. Iterate on code quality based on feedback

## Additional Resources

- [SonarCloud Documentation](https://docs.sonarcloud.io/)
- [Quality Gate Configuration](https://docs.sonarcloud.io/improving/quality-gates/)
- [Token Management](https://docs.sonarcloud.io/advanced-setup/user-accounts/)
- [GitHub Integration](https://docs.sonarcloud.io/advanced-setup/ci-based-analysis/github-actions/)
