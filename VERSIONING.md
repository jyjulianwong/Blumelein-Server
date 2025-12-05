# Semantic Versioning Guide

This project uses **Semantic Versioning** (SemVer) with automated version management through **Python Semantic Release** and **Conventional Commits**.

## 📋 Table of Contents

- [Quick Reference](#quick-reference)
- [How It Works](#how-it-works)
- [Conventional Commits](#conventional-commits)
- [Version Bumping Rules](#version-bumping-rules)
- [Workflow](#workflow)
- [Examples](#examples)
- [Best Practices](#best-practices)
- [Configuration Details](#configuration-details)
- [Troubleshooting](#troubleshooting)

---

## Quick Reference

### Commit Message Format

```
<type>(<scope>): <short description>

[optional body]

[optional footer]
```

### Common Commit Types

#### 🆕 New Features (Minor Version Bump: 0.X.0)

```bash
feat: add order filtering by status
feat(payments): support multiple currencies
feat(manage): add bulk order export
```

#### 🐛 Bug Fixes (Patch Version Bump: 0.0.X)

```bash
fix: correct payment webhook signature validation
fix(orders): handle empty delivery address
fix(database): retry failed Firestore connections
```

#### 💥 Breaking Changes (Major Version Bump: X.0.0)

```bash
feat!: redesign order API response format

BREAKING CHANGE: Order items now returned as object instead of array
```

#### 🔧 No Version Bump (No Deployment)

```bash
docs: update API documentation
chore: update dependencies
style: format code with black
refactor: simplify database adapter
test: add payment webhook tests
ci: optimize GitHub Actions workflow
```

### Quick Decision Tree

```
Is this a new feature?
├─ Yes → Use 'feat:'
│   └─ Is it breaking? 
│       ├─ Yes → Use 'feat!:' or add 'BREAKING CHANGE'
│       └─ No  → Use 'feat:'
│
└─ No → Is it a bug fix?
    ├─ Yes → Use 'fix:'
    │   └─ Is it breaking?
    │       ├─ Yes → Use 'fix!:' or add 'BREAKING CHANGE'
    │       └─ No  → Use 'fix:'
    │
    └─ No → Is it docs/tests/chores?
        └─ Yes → Use 'docs:', 'test:', 'chore:', etc.
```

### Version Bump Summary

| Commit Prefix | Version Bump | Example | Deploys? |
|---------------|--------------|---------|----------|
| `feat:` | Minor (0.X.0) | 0.1.0 → 0.2.0 | ✅ Yes |
| `fix:` | Patch (0.0.X) | 0.1.0 → 0.1.1 | ✅ Yes |
| `feat!:` or `BREAKING CHANGE:` | Major (X.0.0) | 0.1.0 → 1.0.0 | ✅ Yes |
| `docs:`, `chore:`, `test:`, etc. | None | No change | ❌ No |

---

## How It Works

### The Automated Flow

When you push to the `main` branch, the GitHub Actions workflow automatically:

1. **Analyzes** your commit messages since the last release
2. **Determines** the appropriate version bump (major, minor, or patch)
3. **Updates** version numbers in `pyproject.toml` and `setup.py`
4. **Generates** a new entry in `CHANGELOG.md`
5. **Creates** a Git tag for the new version
6. **Builds** a Docker image tagged with the new version
7. **Deploys** the new version to Google Cloud Run via Terraform

**No manual deployment is triggered** unless semantic release determines a version bump is needed.

### Visual Workflow

```
┌─────────────────────────────────────────────────────────────────┐
│ 1. Developer commits with conventional format                    │
│    git commit -m "feat: add order filtering"                    │
└─────────────────────────┬───────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────────┐
│ 2. Push to main branch                                          │
│    git push origin main                                         │
└─────────────────────────┬───────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────────┐
│ 3. GitHub Actions: version_bump job                             │
│    - Analyzes commit messages since last release                │
│    - Determines version bump (major/minor/patch)                │
│    - Updates pyproject.toml and setup.py                        │
│    - Updates CHANGELOG.md                                       │
│    - Creates and pushes Git tag                                 │
│    - Outputs: version, tag, released (true/false)               │
└─────────────────────────┬───────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────────┐
│ 4. GitHub Actions: build-and-push job (if released == true)    │
│    - Builds Docker image                                        │
│    - Tags with semantic version (e.g., 0.2.0)                   │
│    - Tags with 'latest'                                         │
│    - Pushes to Google Artifact Registry                         │
└─────────────────────────┬───────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────────┐
│ 5. GitHub Actions: terraform-deploy job                         │
│    - Generates terraform.tfvars with new image tag              │
│    - Runs terraform init/validate/plan/apply                    │
│    - Updates Cloud Run service with new version                 │
│    - Outputs deployment summary with version                    │
└─────────────────────────────────────────────────────────────────┘
```

---

## Conventional Commits

This project uses the **Conventional Commits** specification to determine version bumps automatically.

### Commit Message Format

```
<type>(<scope>): <subject>

<body>

<footer>
```

### Types

| Type | Description | Version Bump | Example |
|------|-------------|--------------|---------|
| `feat` | New feature | **MINOR** (0.x.0) | `feat: add order filtering by date` |
| `fix` | Bug fix | **PATCH** (0.0.x) | `fix: correct payment webhook validation` |
| `BREAKING CHANGE` | Breaking API change | **MAJOR** (x.0.0) | See below |
| `docs` | Documentation | None | `docs: update API endpoint examples` |
| `style` | Code style changes | None | `style: format with black` |
| `refactor` | Code refactoring | None | `refactor: simplify database adapter` |
| `test` | Test changes | None | `test: add payment integration tests` |
| `chore` | Maintenance | None | `chore: update dependencies` |
| `ci` | CI/CD changes | None | `ci: optimize workflow caching` |
| `perf` | Performance improvements | **PATCH** (0.0.x) | `perf: optimize database queries` |

### Scopes (Optional)

You can add a scope to provide more context:

```
feat(orders): add bulk order import
fix(payments): handle stripe timeout errors
docs(api): add webhook setup guide
```

Common scopes:
- `orders` - Order management
- `payments` - Payment processing
- `manage` - Admin/management endpoints
- `database` - Database operations
- `api` - General API changes

---

## Version Bumping Rules

### Patch Version (0.0.X)

**When:** Bug fixes, performance improvements, or internal changes

```bash
fix: resolve order status update race condition
perf: cache frequently accessed Firestore documents
```

**Result:** `0.1.0` → `0.1.1`

### Minor Version (0.X.0)

**When:** New features that are backward compatible

```bash
feat: add order search by customer name
feat(payments): support multiple currencies
```

**Result:** `0.1.0` → `0.2.0`

### Major Version (X.0.0)

**When:** Breaking changes that are NOT backward compatible

**Option 1:** Use `BREAKING CHANGE` in footer

```bash
feat(api): redesign order response format

BREAKING CHANGE: Order API now returns items as nested objects instead of arrays
```

**Option 2:** Add `!` after type

```bash
feat!: change payment intent creation endpoint
```

**Result:** `0.1.0` → `1.0.0`

---

## Workflow

### 1. Make Changes

Develop your features, fixes, or improvements on a feature branch:

```bash
git checkout -b feature/add-order-filters
# Make your changes
git add .
```

### 2. Commit with Conventional Format

Write commit messages following the Conventional Commits format:

```bash
git commit -m "feat(orders): add filtering by date range"
```

### 3. Push to Main

Either merge your PR or push directly to main:

```bash
git push origin main
```

### 4. Automated Deployment

The GitHub Actions workflow will:

1. **Version Bump Job**
   - Analyzes commits since last release
   - Determines version bump (if any)
   - Updates `pyproject.toml` and `setup.py`
   - Updates `CHANGELOG.md`
   - Creates Git tag
   - Pushes changes back to repo

2. **Build Job** (only if version bumped)
   - Builds Docker image with new version tag
   - Pushes to Google Artifact Registry
   - Tags image as `latest` and `<version>`

3. **Deploy Job** (only if version bumped)
   - Runs Terraform to deploy new version
   - Updates Cloud Run service
   - Outputs deployment summary

---

## Examples

### Example 1: Adding a New Feature

```bash
# Add order export functionality
git commit -m "feat(orders): add CSV export for orders

Allows admins to export all orders as a CSV file for reporting purposes."

git push origin main
```

**Result:**
- Version: `0.1.0` → `0.2.0`
- Changelog updated automatically
- Git tag `v0.2.0` created
- Docker image built and tagged: `blumelein-server:0.2.0`
- Deployed to Cloud Run

### Example 2: Fixing a Bug

```bash
# Fix payment webhook
git commit -m "fix(payments): validate webhook signature correctly

Previously, some valid Stripe webhooks were rejected due to incorrect signature comparison."

git push origin main
```

**Result:**
- Version: `0.1.0` → `0.1.1`
- Changelog updated automatically
- Git tag `v0.1.1` created
- Docker image built and tagged: `blumelein-server:0.1.1`
- Deployed to Cloud Run

### Example 3: Updating Documentation

```bash
git commit -m "docs: add Stripe webhook setup instructions"
git push origin main
```

**Result:**
- No version change
- No deployment
- Changes pushed to main

### Example 4: Breaking Change

```bash
# Change API response format
git commit -m "feat(api)!: restructure order response format

Order items are now returned as a dictionary keyed by item_id instead of an array.

BREAKING CHANGE: Clients must update their order parsing logic to handle the new response structure."

git push origin main
```

**Result:**
- Version: `0.1.0` → `1.0.0`
- Changelog updated with breaking change note
- Git tag `v1.0.0` created
- Docker image built and tagged: `blumelein-server:1.0.0`
- Deployed to Cloud Run

### Example 5: Multiple Commits

```bash
# Multiple changes in one PR
git commit -m "feat(orders): add order status history"
git commit -m "feat(manage): add bulk status update endpoint"
git commit -m "fix(database): handle connection timeout gracefully"

git push origin main
```

**Result:**
- Version: `0.1.0` → `0.2.0` (highest level bump wins)
- All changes documented in changelog
- Single deployment with all changes

### Example 6: With Scope and Body

```bash
git commit -m "feat(orders): add date range filter for order history

Allows admins to filter orders by creation date range using query parameters."

git push origin main
```

**Result:** `0.1.0` → `0.2.0` ✅ **Deploys**

---

## Best Practices

### 1. Write Clear Commit Messages

**Good:**
```bash
feat(payments): add support for partial refunds

Implements partial refund logic for Stripe payments, allowing admins to refund specific amounts.
```

**Bad:**
```bash
fix stuff
update code
changes
```

### 2. Use Appropriate Types

- Use `feat` for user-facing features
- Use `fix` for bug fixes that affect users
- Use `refactor` for internal code improvements
- Use `docs` for documentation-only changes

### 3. One Logical Change Per Commit

**Good:**
```bash
git commit -m "feat(orders): add date range filter"
git commit -m "feat(orders): add status filter"
```

**Bad:**
```bash
git commit -m "feat: add filters, fix bugs, update docs"
```

### 4. Test Before Pushing to Main

- Run tests locally: `uv run pytest`
- Test API endpoints manually
- Review your changes

### 5. Use Feature Branches

```bash
# Create feature branch
git checkout -b feature/order-filters

# Work on feature
git commit -m "feat(orders): add date range filter"

# Push and create PR
git push origin feature/order-filters

# After review, merge to main
```

### 6. Breaking Changes Require Documentation

When making breaking changes:

1. Clearly document what changed
2. Provide migration instructions
3. Update API documentation
4. Consider deprecation warnings first

### 7. Be Specific with Scopes

**Good:** `feat(orders): add CSV export` is better than `feat: add export`

### 8. Review Changes Before Committing

Check what you're committing with `git diff`

---

## Configuration Details

### What Was Configured

#### 1. Dependencies Added

**File:** `pyproject.toml`

```toml
[project.optional-dependencies]
dev = [
    "pytest>=8.0.0",
    "httpx>=0.27.0",
    "pytest-asyncio>=0.24.0",
    "python-semantic-release>=10.3.1",  # ← Added
]
```

#### 2. Semantic Release Configuration

**File:** `pyproject.toml`

```toml
[tool.semantic_release]
# Where to update the version
version_toml = [
  "pyproject.toml:project.version"
]
version_variables = [
  "setup.py:version=\"(?P<version>\\d+\\.\\d+\\.\\d+)\""
]
# Use Conventional Commits for deciding bumps
commit_parser = "conventional"
```

This tells semantic release:
- Update the version in `pyproject.toml` under `[project]`
- Update the version in `setup.py`
- Parse commits using Conventional Commits format

#### 3. Setup File Created

**File:** `setup.py`

```python
from setuptools import find_packages, setup

setup(
    name="blumelein-server",
    version="0.1.0",
    packages=find_packages(),
)
```

#### 4. Changelog Initialized

**File:** `CHANGELOG.md`

```markdown
# CHANGELOG

<!-- version list -->

## v0.1.0 (2025-12-05)

- Initial Release
```

This will be automatically updated by semantic release on each version bump.

#### 5. GitHub Workflow Updated

**File:** `.github/workflows/build-deploy.yaml`

Added a `version_bump` job that runs before building and deploying:

```yaml
jobs:
  version_bump:
    runs-on: ubuntu-latest
    outputs:
      version: ${{ steps.psr.outputs.version }}
      tag: ${{ steps.psr.outputs.tag }}
      released: ${{ steps.psr.outputs.released }}
    permissions:
      contents: write
      packages: write
    steps:
      - name: ⚙️ Set up repository
        uses: actions/checkout@v4
        with:
          fetch-depth: 0  # important for tags
      
      - name: ⚙️ Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'
          cache: 'pip'
      
      - name: 📦 Install dependencies
        run: |
          python -m pip install --upgrade pip
          python -m pip install uv
          uv sync --group dev
      
      - name: 📦 Run Semantic Release
        id: psr
        uses: python-semantic-release/python-semantic-release@v10
        with:
          github_token: ${{ secrets.GITHUB_TOKEN }}
```

**Key Changes:**
- The workflow now runs on both `push` and `pull_request` to main
- Version bump runs first and determines if a release is needed
- Build and deploy only run if `released == 'true'`
- Docker images are tagged with the semantic version (not git SHA)
- Deployment summary includes the version number

### What Gets Updated

When a version bump occurs, the following files are automatically updated:

1. **pyproject.toml**
   ```toml
   [project]
   version = "0.2.0"  # ← Updated
   ```

2. **setup.py**
   ```python
   setup(
       name="blumelein-server",
       version="0.2.0",  # ← Updated
       packages=find_packages(),
   )
   ```

3. **CHANGELOG.md**
   ```markdown
   ## v0.2.0 (2025-12-05)
   
   ### Features
   
   - Add order CSV export functionality
     ([`abc1234`](https://github.com/user/repo/commit/abc1234))
   ```

4. **Git Tags**
   ```bash
   v0.2.0  # ← Created and pushed
   ```

### Local Installation

If you want to run semantic release locally:

```bash
# Install dependencies
uv sync --group dev

# Run semantic release (dry-run)
uv run semantic-release version --no-commit --no-tag --no-push

# Run semantic release (actual release, requires git push access)
uv run semantic-release version
```

**Note:** Typically you won't need to run this locally, as GitHub Actions handles it automatically.

---

## Troubleshooting

### Deployment Didn't Trigger

**Problem:** Pushed to main but no deployment happened

**Solutions:**
- **Check commit messages:** Ensure you used `feat:` or `fix:` prefix
- **Check workflow:** View GitHub Actions tab for errors
- **Check branch:** Ensure you pushed to `main`
- **Check logs:** Review the version_bump job output

### Wrong Version Bump

**Problem:** Version bumped incorrectly (e.g., minor instead of patch)

**Solutions:**
- **Review commits:** Use `git log` to check commit messages
- **Fix commit messages:** Use `git commit --amend` before pushing
- **Contact maintainer:** For already-pushed changes

### CHANGELOG Not Updated

**Problem:** CHANGELOG.md doesn't reflect new version

**Solutions:**
- Ensure `CHANGELOG.md` exists in the repo
- Check GitHub Actions logs for errors
- Verify semantic release configuration in `pyproject.toml`

### Build Failed After Version Bump

**Problem:** Version bumped but deployment failed

**Solutions:**
- Check Docker build logs
- Verify all tests pass
- Check Terraform configuration
- Review Cloud Run deployment logs

### Permission Errors in GitHub Actions

**Problem:** `permission denied` errors in version_bump job

**Solutions:**
- Ensure workflow has `contents: write` permission
- Check GitHub token permissions in repository settings

### Git Tag Conflicts

**Problem:** Tag already exists error

**Solutions:**
- Don't create tags manually
- Let semantic release handle all tagging
- Delete conflicting tags if needed: `git tag -d v0.1.0 && git push origin :refs/tags/v0.1.0`

---

## Checking Current Version

```bash
# Check version in pyproject.toml
cat pyproject.toml | grep version

# Check latest Git tag
git describe --tags --abbrev=0

# Check CHANGELOG
cat CHANGELOG.md

# Check deployed version on Cloud Run
gcloud run services describe blumelein-server --region=us-central1 --format='value(spec.template.spec.containers[0].image)'
```

---

## Benefits

### 1. Automatic Version Management
- No manual version number updates needed
- Consistent versioning across the project
- Follows semantic versioning principles

### 2. Clear Change History
- CHANGELOG.md automatically generated
- Easy to see what changed in each version
- Links to commits and PRs

### 3. Controlled Deployments
- Only deploy when there are actual changes
- Documentation updates don't trigger deployments
- Clear version numbers on deployed services

### 4. Better Collaboration
- Standardized commit message format
- Easy to understand what each commit does
- Clear communication of breaking changes

### 5. Git Tags
- Each release automatically tagged
- Easy to reference specific versions
- Simple rollback if needed

---

## Additional Resources

- [Semantic Versioning Specification](https://semver.org/)
- [Conventional Commits Specification](https://www.conventionalcommits.org/)
- [Python Semantic Release Documentation](https://python-semantic-release.readthedocs.io/)
- [Keep a Changelog](https://keepachangelog.com/)

---

## Summary

| Commit Type | Version Change | Deployment |
|-------------|----------------|------------|
| `feat:` | Minor (0.x.0) | ✅ Yes |
| `fix:` | Patch (0.0.x) | ✅ Yes |
| `perf:` | Patch (0.0.x) | ✅ Yes |
| `BREAKING CHANGE:` | Major (x.0.0) | ✅ Yes |
| `docs:`, `chore:`, etc. | None | ❌ No |

**Remember:** Good commit messages = Accurate versioning = Smooth deployments! 🚀
