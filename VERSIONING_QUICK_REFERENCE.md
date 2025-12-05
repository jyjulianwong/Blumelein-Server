# 🚀 Semantic Versioning Quick Reference

## Commit Message Format

```
<type>(<scope>): <short description>

[optional body]

[optional footer]
```

## Common Commit Types

### 🆕 New Features (Minor Version Bump: 0.X.0)

```bash
feat: add order filtering by status
feat(payments): support multiple currencies
feat(manage): add bulk order export
```

### 🐛 Bug Fixes (Patch Version Bump: 0.0.X)

```bash
fix: correct payment webhook signature validation
fix(orders): handle empty delivery address
fix(database): retry failed Firestore connections
```

### 💥 Breaking Changes (Major Version Bump: X.0.0)

```bash
feat!: redesign order API response format

BREAKING CHANGE: Order items now returned as object instead of array
```

### 🔧 No Version Bump (No Deployment)

```bash
docs: update API documentation
chore: update dependencies
style: format code with black
refactor: simplify database adapter
test: add payment webhook tests
ci: optimize GitHub Actions workflow
```

## Examples by Scenario

### Adding a Feature

```bash
git commit -m "feat(orders): add date range filter for order history

Allows admins to filter orders by creation date range using query parameters."
```

Result: `0.1.0` → `0.2.0` ✅ **Deploys**

### Fixing a Bug

```bash
git commit -m "fix(payments): handle Stripe webhook timeout errors

Added retry logic for failed webhook processing to prevent data loss."
```

Result: `0.1.0` → `0.1.1` ✅ **Deploys**

### Updating Documentation

```bash
git commit -m "docs: add Stripe webhook setup instructions"
```

Result: No version change ❌ **No deployment**

### Breaking Change

```bash
git commit -m "feat(api)!: change order response structure

BREAKING CHANGE: 'items' field now returns a dictionary keyed by item_id instead of an array. Clients must update parsing logic."
```

Result: `0.1.0` → `1.0.0` ✅ **Deploys**

## Quick Decision Tree

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

## Version Bump Summary

| Commit Prefix | Version Bump | Example | Deploys? |
|---------------|--------------|---------|----------|
| `feat:` | Minor (0.X.0) | 0.1.0 → 0.2.0 | ✅ Yes |
| `fix:` | Patch (0.0.X) | 0.1.0 → 0.1.1 | ✅ Yes |
| `feat!:` or `BREAKING CHANGE:` | Major (X.0.0) | 0.1.0 → 1.0.0 | ✅ Yes |
| `docs:`, `chore:`, `test:`, etc. | None | No change | ❌ No |

## Tips

1. **Be specific**: `feat(orders): add CSV export` is better than `feat: add export`
2. **One thing per commit**: Don't mix features and fixes
3. **Test first**: Run tests before committing
4. **Use branches**: Create feature branches, then merge to main
5. **Review changes**: Check what you're committing with `git diff`

## Need More Info?

See [VERSIONING.md](VERSIONING.md) for the complete guide.

