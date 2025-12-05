# Service Account Setup Scripts

These scripts help you create and manage the Terraform service account following the naming convention: `svc-{region-abbrev}-tf@{project}.iam.gserviceaccount.com`

## Quick Start

```bash
# 1. Create service account with all permissions
./scripts/setup-service-account.sh YOUR_PROJECT_ID us-central1

# 2. Create a JSON key
./scripts/create-service-account-key.sh YOUR_PROJECT_ID us-central1

# 3. Verify permissions (optional)
./scripts/verify-service-account.sh YOUR_PROJECT_ID us-central1
```

## Scripts

### 1. `setup-service-account.sh`

Creates a service account with the proper naming convention and grants all required IAM roles.

**Usage:**
```bash
./scripts/setup-service-account.sh PROJECT_ID [REGION]
```

**Example:**
```bash
./scripts/setup-service-account.sh blumelein-prod us-central1
```

This creates: `svc-usce1-tf@blumelein-prod.iam.gserviceaccount.com`

**Permissions granted:**
- Artifact Registry Reader & Writer
- BigQuery Data Owner & Job User
- Cloud Datastore Owner & User
- Cloud Run Admin & Developer
- Firestore Service Agent
- Project IAM Admin
- Service Account User
- Service Usage Admin
- Storage Admin, Object Admin & Object Viewer
- Vertex AI User
- Viewer

### 2. `create-service-account-key.sh`

Creates a JSON key file for the service account.

**Usage:**
```bash
./scripts/create-service-account-key.sh PROJECT_ID [REGION]
```

**Example:**
```bash
./scripts/create-service-account-key.sh blumelein-prod us-central1
```

**⚠️ Security Warning:**
- Never commit the key file to git
- Delete the key file after adding to GitHub Secrets
- Rotate keys every 90 days

### 3. `verify-service-account.sh`

Verifies that the service account has all required permissions.

**Usage:**
```bash
./scripts/verify-service-account.sh PROJECT_ID [REGION]
```

**Example:**
```bash
./scripts/verify-service-account.sh blumelein-prod us-central1
```

## Region Abbreviations

The scripts automatically convert region names to abbreviations:

| Region | Abbreviation | Service Account Name |
|--------|-------------|---------------------|
| us-central1 | usce1 | svc-usce1-tf |
| us-east1 | usea1 | svc-usea1-tf |
| europe-west1 | euwe1 | svc-euwe1-tf |
| europe-west2 | euwe2 | svc-euwe2-tf |
| asia-east1 | asea1 | svc-asea1-tf |

## Complete Setup Example

```bash
# Set your project ID
export PROJECT_ID="blumelein-prod"
export REGION="us-central1"

# 1. Authenticate with gcloud
gcloud auth login
gcloud config set project $PROJECT_ID

# 2. Create service account with permissions
./scripts/setup-service-account.sh $PROJECT_ID $REGION

# 3. Create key file
./scripts/create-service-account-key.sh $PROJECT_ID $REGION

# 4. Copy the key content
cat svc-usce1-tf-key.json

# 5. Add to GitHub Secrets
# Go to: Repository Settings → Secrets and variables → Actions
# Create secret: GCP_CREDENTIALS
# Paste the JSON content

# 6. Delete local key file (security)
rm svc-usce1-tf-key.json

# 7. Verify everything is set up correctly
./scripts/verify-service-account.sh $PROJECT_ID $REGION
```

## Updating Existing Service Account

If you already have a service account and want to add missing permissions:

```bash
# Check current permissions
./scripts/verify-service-account.sh YOUR_PROJECT_ID us-central1

# Re-run setup to add missing permissions
./scripts/setup-service-account.sh YOUR_PROJECT_ID us-central1
```

The script is idempotent - it won't recreate the account if it exists, just ensures all permissions are granted.

## Troubleshooting

### Permission Denied

**Error:** `(gcloud.iam.service-accounts.create) PERMISSION_DENIED`

**Solution:** You need `resourcemanager.projects.setIamPolicy` permission. Ask your project owner to run the script or grant you the role.

### Service Account Already Exists

This is normal - the script will skip creation and proceed to grant permissions.

### Role Not Found

**Error:** `ERROR: (gcloud.projects.add-iam-policy-binding) NOT_FOUND: Role roles/XXX not found`

**Solution:** The role might not be available in your project. You can comment out that role in the script.

## Security Best Practices

1. **Least Privilege**: Only grant permissions your deployment actually needs
2. **Key Rotation**: Rotate service account keys every 90 days
3. **Audit Logs**: Enable Cloud Audit Logs to monitor service account usage
4. **Key Storage**: Store keys in GitHub Secrets, never in code
5. **Multiple Environments**: Use separate service accounts for dev/staging/prod

## Next Steps

After setting up the service account:

1. Add `GCP_CREDENTIALS` to GitHub Secrets
2. Update other secrets in GitHub (Stripe keys, Admin API key, etc.)
3. Push to main branch to trigger deployment
4. Monitor the GitHub Actions workflow

See [TERRAFORM_DEPLOYMENT.md](../TERRAFORM_DEPLOYMENT.md) for complete deployment instructions.

