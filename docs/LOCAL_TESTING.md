# Local Testing Guide

This guide explains how to test the repository sync script locally.

## Prerequisites

- Python 3.11+ installed
- Git installed
- GitHub account with access to your organization
- GitHub App created (or use a Personal Access Token for testing)

## Setup Local Environment

### 1. Clone the Repository

```bash
git clone https://github.com/complytime/org-infra.git
cd org-infra
```

### 2. Create Python Virtual Environment

```bash
# Create virtual environment
python3 -m venv .venv

# Activate it
source .venv/bin/activate  # Linux/Mac
# or
.venv\Scripts\activate     # Windows
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Verify Installation

```bash
python scripts/sync-org-repositories.py --help
```

You should see the help message with available options.

## Authentication Options

#### 1. Create Fine-Grained PAT

1. Go to: `https://github.com/settings/personal-access-tokens/new`
2. Configure:
   - **Name:** `repo-sync-testing`
   - **Expiration:** 7 days (short-lived for testing)
   - **Repository access:** Select your org repositories
   - **Permissions:**
     - Contents: Read-only
     - Pull requests: Read and write
     - Metadata: Read-only
3. Generate and copy token

Note that some different permissions may be necessary depending on the testing environment.

#### 2. Set Environment Variables

```bash
# Export token
export GITHUB_PAT="ghp_your_token_here"
```

## Test Scenarios

### Test 1: Dry Run on Single Repository

This is the safest way to start - it won't make any changes.

```bash
cd org-infra

python scripts/sync-org-repositories.py \
  --org complytime \
  --config sync-config.yml \
  --repos complytime-demos \
  --dry-run
```

**Expected Output:**
```
Authenticated as: your-username
Fetching peribolos configuration from https://github.com/complytime/.github.git
Successfully loaded peribolos.yaml
Found 8 repositories in peribolos configuration for complytime
Filtering to 1 specified repository(ies)
Will process 1 repository(ies)

============================================================
Processing: complytime/complytime-demos
============================================================
[DRY RUN] Would clone fork: https://github.com/your-username/complytime-demos.git
Cloning https://github.com/complytime/complytime-demos.git...
[DRY RUN] Would add: .github/workflows/ci_checks.yml
[DRY RUN] Would update: .github/dependabot.yml
.github/pull_request_template.md is up to date
[DRY RUN] Would create PR with 2 file(s)

============================================================
Summary: Successfully processed 1/1 repositories
============================================================
```

### Test 2: Dry Run on All Repositories

Test without making changes to see what would happen:

```bash
python scripts/sync-org-repositories.py \
  --org complytime \
  --config sync-config.yml \
  --dry-run
```

**What to check:**
- ✅ All repositories are detected from peribolos.yml
- ✅ Excluded repositories are skipped
- ✅ Files are correctly identified as up-to-date/missing/different
- ✅ No errors in authentication or repository access

### Test 3: Actual Sync on Test Repository

**⚠️ Warning:** This will create real forks and PRs!

```bash
# Create a test repository first or use an existing test repo
python scripts/sync-org-repositories.py \
  --org complytime \
  --config sync-config.yml \
  --repos test-repo
```

**What happens:**
1. Fork is created under your account
2. Fork is cloned locally (in temp directory)
3. Changes are applied
4. Commit is pushed to fork
5. PR is created from fork -> upstream

**Verify:**
```bash
# Check if fork was created
gh repo view your-username/test-repo

# Check if PR was created
gh pr list --repo complytime/test-repo
```

### Test 4: Test with Multiple Specific Repos

```bash
python scripts/sync-org-repositories.py \
  --org complytime \
  --config sync-config.yml \
  --repos complybeacon complyscribe complyctl \
  --dry-run
```

### Test 5: Test Configuration Changes

Edit `sync-config.yml` to test different configurations:

```yaml
# Test excluding a repository
exclude_repos:
  - test-excluded-repo

# Test excluding files for specific repos
files_to_sync:
  - source: ruff.toml
    destination: ruff.toml
    exclude_repos:
      - non-python-repo
```

Run with dry-run to verify exclusions work:

```bash
python scripts/sync-org-repositories.py \
  --org complytime \
  --config sync-config.yml \
  --dry-run
```

## Testing Checklist

Before running in production:

- [ ] **Dry run succeeds** on single repository
- [ ] **Dry run succeeds** on all repositories
- [ ] **Authentication works** (user/app detected)
- [ ] **peribolos.yaml loads** correctly
- [ ] **Repositories list** is correct
- [ ] **Excluded repos** are skipped
- [ ] **File detection** works (up-to-date/missing/different)
- [ ] **Test sync** creates fork successfully
- [ ] **Test sync** creates PR successfully
- [ ] **PR attribution** is correct (your user or app)
- [ ] **PR content** matches expectations
- [ ] **Error handling** works (test with invalid repo name)

## Common Issues and Solutions

### Issue 1: Authentication Failed

```
Error: Failed to get authenticated user
```

**Debug:**
```bash
# Check token is set
echo $GITHUB_PAT

# Test token manually
curl -H "Authorization: Bearer $GITHUB_PAT" \
     https://api.github.com/user
```

**Solutions:**
- Verify token is exported in current shell
- Check token hasn't expired
- Verify token has correct permissions

## Testing Best Practices

### 1. Use a Test Organization

Create a test organization with a few test repositories:

```bash
# Fork some repos to your test org
gh repo fork source-repo --org test-org
```

### 2. Use Short-Lived Tokens

For testing, create tokens that expire in 7 days or less:
- Less security risk
- Forces you to rotate regularly
- Revoke as soon the tests are finished

### 3. Clean Up After Testing

```bash
# Delete test forks
gh repo delete your-username/test-repo

# Close test PRs
gh pr close 123 --repo complytime/test-repo

# Revoke test token
gh auth logout
```

## Advanced Testing

### Test with Custom Configuration

Create a test config file:

```bash
cp sync-config.yml sync-config-test.yml
```

Edit to include only test files:

```yaml
files_to_sync:
  - source: .github/pull_request_template.md
    destination: .github/pull_request_template.md
```

Run with test config:

```bash
python scripts/sync-org-repositories.py \
  --org complytime \
  --config sync-config-test.yml \
  --repos test-repo \
  --dry-run
```

### Test Error Handling

Test with invalid inputs to ensure proper error handling:

```bash
# Invalid org
python scripts/sync-org-repositories.py \
  --org invalid-org-name \
  --config sync-config.yml \
  --dry-run

# Invalid repo
python scripts/sync-org-repositories.py \
  --org complytime \
  --config sync-config.yml \
  --repos non-existent-repo

# Missing config
python scripts/sync-org-repositories.py \
  --org complytime \
  --config non-existent.yml
```
