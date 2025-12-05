# Semantic Versioning Guide

This project uses **Semantic Versioning** (SemVer) with automated version management through **Python Semantic Release** and **Conventional Commits**.

## 📋 Table of Contents

- [How It Works](#how-it-works)
- [Conventional Commits](#conventional-commits)
- [Version Bumping Rules](#version-bumping-rules)
- [Workflow](#workflow)
- [Examples](#examples)
- [Best Practices](#best-practices)

## 🔄 How It Works

When you push to the `main` branch, the GitHub Actions workflow automatically:

1. **Analyzes** your commit messages
2. **Determines** the appropriate version bump (major, minor, or patch)
3. **Updates** version numbers in `pyproject.toml` and `setup.py`
4. **Generates** a new entry in `CHANGELOG.md`
5. **Creates** a Git tag for the new version
6. **Builds** a Docker image tagged with the new version
7. **Deploys** the new version to Google Cloud Run via Terraform

**No manual deployment is triggered** unless semantic release determines a version bump is needed.

## 📝 Conventional Commits

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

## 🔢 Version Bumping Rules

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

## 🚀 Workflow

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

## 📚 Examples

### Example 1: Adding a New Feature

```bash
# Add order export functionality
git commit -m "feat(orders): add CSV export for orders

Allows admins to export all orders as a CSV file for reporting purposes."

# Result: 0.1.0 → 0.2.0
```

### Example 2: Fixing a Bug

```bash
# Fix payment webhook
git commit -m "fix(payments): validate webhook signature correctly

Previously, some valid Stripe webhooks were rejected due to incorrect signature comparison."

# Result: 0.1.0 → 0.1.1
```

### Example 3: Breaking Change

```bash
# Change API response format
git commit -m "feat(api)!: restructure order response format

Order items are now returned as a dictionary keyed by item_id instead of an array.

BREAKING CHANGE: Clients must update their order parsing logic to handle the new response structure."

# Result: 0.1.0 → 1.0.0
```

### Example 4: Multiple Commits

```bash
# Multiple changes in one PR
git commit -m "feat(orders): add order status history"
git commit -m "feat(manage): add bulk status update endpoint"
git commit -m "fix(database): handle connection timeout gracefully"

# Result: 0.1.0 → 0.2.0 (highest level bump wins)
```

### Example 5: No Version Bump

```bash
# Documentation or chore changes
git commit -m "docs: update deployment guide"
git commit -m "chore: update dependencies"

# Result: No version bump, no deployment
```

## ✅ Best Practices

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

## 🔍 Checking Current Version

```bash
# Check version in pyproject.toml
cat pyproject.toml | grep version

# Check latest Git tag
git describe --tags --abbrev=0

# Check CHANGELOG
cat CHANGELOG.md
```

## 🏷️ Manual Tagging (Not Recommended)

The system handles tagging automatically. However, if needed:

```bash
# Create a tag manually (not recommended)
git tag v0.2.0
git push origin v0.2.0
```

**Note:** Manual tags may conflict with semantic release. Always use conventional commits instead.

## 📖 Additional Resources

- [Semantic Versioning](https://semver.org/)
- [Conventional Commits](https://www.conventionalcommits.org/)
- [Python Semantic Release](https://python-semantic-release.readthedocs.io/)
- [Keep a Changelog](https://keepachangelog.com/)

## 🆘 Troubleshooting

### Deployment Didn't Trigger

- **Check commit messages:** Ensure you used `feat:` or `fix:` prefix
- **Check workflow:** View GitHub Actions tab for errors
- **Check branch:** Ensure you pushed to `main`

### Wrong Version Bump

- **Review commits:** Use `git log` to check commit messages
- **Fix commit messages:** Use `git commit --amend` before pushing
- **Contact maintainer:** For already-pushed changes

### CHANGELOG Not Updated

- The CHANGELOG is automatically generated by semantic release
- Ensure `CHANGELOG.md` exists in the repo
- Check GitHub Actions logs for errors

### Build Failed After Version Bump

- Check Docker build logs
- Verify all tests pass
- Check Terraform configuration

## 📝 Summary

| Commit Type | Version Change | Deployment |
|-------------|----------------|------------|
| `feat:` | Minor (0.x.0) | ✅ Yes |
| `fix:` | Patch (0.0.x) | ✅ Yes |
| `BREAKING CHANGE:` | Major (x.0.0) | ✅ Yes |
| `docs:`, `chore:`, etc. | None | ❌ No |

**Remember:** Good commit messages = Accurate versioning = Smooth deployments! 🚀

