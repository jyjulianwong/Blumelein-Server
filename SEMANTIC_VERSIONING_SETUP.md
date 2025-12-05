# Semantic Versioning Setup Summary

This document summarizes the semantic versioning configuration added to the Blumelein-Server project.

## ✅ What Was Configured

### 1. Dependencies Added

**File:** `pyproject.toml`

Added `python-semantic-release>=10.3.1` to the dev dependencies:

```toml
[project.optional-dependencies]
dev = [
    "pytest>=8.0.0",
    "httpx>=0.27.0",
    "pytest-asyncio>=0.24.0",
    "python-semantic-release>=10.3.1",  # ← Added
]
```

### 2. Semantic Release Configuration

**File:** `pyproject.toml`

Added configuration for Python Semantic Release:

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

### 3. Setup File Created

**File:** `setup.py`

Created a minimal setup.py for version tracking:

```python
from setuptools import find_packages, setup

setup(
    name="blumelein-server",
    version="0.1.0",
    packages=find_packages(),
)
```

### 4. Changelog Initialized

**File:** `CHANGELOG.md`

Created initial changelog:

```markdown
# CHANGELOG

<!-- version list -->

## v0.1.0 (2025-12-05)

- Initial Release
```

This will be automatically updated by semantic release on each version bump.

### 5. GitHub Workflow Updated

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

### 6. Documentation Created

Created comprehensive documentation:

1. **VERSIONING.md** - Complete guide to semantic versioning
   - How it works
   - Conventional commit format
   - Version bumping rules
   - Workflow explanation
   - Examples and best practices
   
2. **VERSIONING_QUICK_REFERENCE.md** - Quick reference guide
   - Common commit types
   - Quick decision tree
   - Version bump summary table
   
3. **Updated README.md** - Added reference to semantic versioning

## 🔄 How It Works

### The Automated Flow

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

### Version Determination Logic

| Commit Type | Version Change | Example |
|-------------|----------------|---------|
| `feat:` | 0.1.0 → 0.2.0 | Minor bump |
| `fix:` | 0.1.0 → 0.1.1 | Patch bump |
| `feat!:` or `BREAKING CHANGE:` | 0.1.0 → 1.0.0 | Major bump |
| `docs:`, `chore:`, `style:`, etc. | No change | No deployment |

## 🚀 Usage Examples

### Example 1: Adding a New Feature

```bash
git commit -m "feat(orders): add CSV export functionality"
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
git commit -m "fix(payments): handle webhook timeout errors"
git push origin main
```

**Result:**
- Version: `0.1.0` → `0.1.1`
- Changelog updated automatically
- Git tag `v0.1.1` created
- Docker image built and tagged: `blumelein-server:0.1.1`
- Deployed to Cloud Run

### Example 3: Documentation Update

```bash
git commit -m "docs: update API examples"
git push origin main
```

**Result:**
- No version change
- No deployment
- Changes pushed to main

### Example 4: Breaking Change

```bash
git commit -m "feat(api)!: redesign order response format

BREAKING CHANGE: Order items now returned as object instead of array"
git push origin main
```

**Result:**
- Version: `0.1.0` → `1.0.0`
- Changelog updated with breaking change note
- Git tag `v1.0.0` created
- Docker image built and tagged: `blumelein-server:1.0.0`
- Deployed to Cloud Run

## 📋 Conventional Commit Types

| Type | Description | Triggers Release? |
|------|-------------|-------------------|
| `feat` | New feature | ✅ Yes (minor) |
| `fix` | Bug fix | ✅ Yes (patch) |
| `docs` | Documentation only | ❌ No |
| `style` | Code style (formatting) | ❌ No |
| `refactor` | Code refactoring | ❌ No |
| `perf` | Performance improvement | ✅ Yes (patch) |
| `test` | Adding tests | ❌ No |
| `chore` | Maintenance tasks | ❌ No |
| `ci` | CI/CD changes | ❌ No |
| `build` | Build system changes | ❌ No |

## 🔍 What Gets Updated

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

## 🎯 Benefits

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

## 🛠️ Installation on Local Machine

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

## 📚 Additional Resources

- [Semantic Versioning Specification](https://semver.org/)
- [Conventional Commits Specification](https://www.conventionalcommits.org/)
- [Python Semantic Release Documentation](https://python-semantic-release.readthedocs.io/)
- [Keep a Changelog](https://keepachangelog.com/)

## ✅ Setup Checklist

- [x] Added `python-semantic-release` to dev dependencies
- [x] Configured semantic release in `pyproject.toml`
- [x] Created `setup.py` for version tracking
- [x] Initialized `CHANGELOG.md`
- [x] Updated GitHub Actions workflow
- [x] Created comprehensive documentation
- [x] Updated README.md with versioning information

## 🚦 Next Steps

1. **Install dependencies**: Run `uv sync --group dev`
2. **Test it out**: Make a commit with `feat:` or `fix:` prefix
3. **Push to main**: Watch the GitHub Actions workflow
4. **Verify**: Check that version was bumped and deployment succeeded

## 💡 Tips

- Always use conventional commit format
- Test locally before pushing to main
- Use feature branches for development
- Review the CHANGELOG after each release
- Check GitHub Actions logs if something goes wrong

## 🆘 Support

If you encounter issues:

1. Check the GitHub Actions logs
2. Review commit messages for proper format
3. Verify all required secrets are configured
4. Consult [VERSIONING.md](VERSIONING.md) for detailed guidance

---

**Configuration completed on:** 2025-12-05
**Initial version:** 0.1.0
**Configured by:** AI Assistant

