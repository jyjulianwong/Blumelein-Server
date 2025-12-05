# Terraform Deployment Guide

This guide explains how to deploy the Blumelein Server API to Google Cloud Run using Terraform and GitHub Actions.

## Overview

The deployment setup includes:

- **Terraform** for infrastructure as code
- **GitHub Actions** for automated CI/CD
- **Cloud Run** for serverless container deployment
- **Artifact Registry** for Docker image storage
- **Firestore** for database
- **Automatic deployments** on push to main branch

## Prerequisites

1. **Google Cloud Project** with billing enabled
2. **GitHub repository** for your code
3. **gcloud CLI** installed locally (for initial setup)
4. **Terraform** installed locally (optional, for local testing)

## Initial Setup

### Step 1: Create Google Cloud Resources

```bash
# Set your project ID
export PROJECT_ID="your-project-id"
gcloud config set project $PROJECT_ID

# Enable required APIs
gcloud services enable run.googleapis.com
gcloud services enable firestore.googleapis.com
gcloud services enable artifactregistry.googleapis.com
gcloud services enable cloudbuild.googleapis.com

# Create Firestore database (if not already created)
gcloud firestore databases create \
  --location=us-central1 \
  --type=firestore-native
```

### Step 2: Create Terraform State Bucket

Terraform needs a GCS bucket to store its state:

```bash
# Create bucket for Terraform state
export TERRAFORM_BUCKET="${PROJECT_ID}-terraform-state"
gsutil mb -l us-central1 gs://${TERRAFORM_BUCKET}

# Enable versioning for safety
gsutil versioning set on gs://${TERRAFORM_BUCKET}
```

### Step 3: Create Service Account for GitHub Actions

We provide automated scripts to create a properly configured service account following the naming convention:
`svc-{region-abbrev}-tf@{project}.iam.gserviceaccount.com`

**Automated Setup (Recommended):**

```bash
# Run the setup script
./scripts/setup-service-account.sh $PROJECT_ID us-central1

# Create the key file
./scripts/create-service-account-key.sh $PROJECT_ID us-central1

# Verify permissions (optional)
./scripts/verify-service-account.sh $PROJECT_ID us-central1
```

This creates a service account with the naming pattern `svc-usce1-tf@{project}.iam.gserviceaccount.com` and grants all necessary permissions.

**Manual Setup (Alternative):**

If you prefer manual setup:

```bash
# Create service account
REGION_ABBREV="usce1"  # us-central1 abbreviated
SERVICE_ACCOUNT_NAME="svc-${REGION_ABBREV}-tf"

gcloud iam service-accounts create $SERVICE_ACCOUNT_NAME \
  --display-name="Terraform Service Account"

# Grant comprehensive permissions
ROLES=(
  "roles/artifactregistry.reader"
  "roles/artifactregistry.writer"
  "roles/bigquery.dataOwner"
  "roles/bigquery.jobUser"
  "roles/datastore.owner"
  "roles/datastore.user"
  "roles/run.admin"
  "roles/run.developer"
  "roles/firestore.serviceAgent"
  "roles/resourcemanager.projectIamAdmin"
  "roles/iam.serviceAccountUser"
  "roles/serviceusage.serviceUsageAdmin"
  "roles/storage.admin"
  "roles/storage.objectAdmin"
  "roles/storage.objectViewer"
  "roles/aiplatform.user"
  "roles/viewer"
)

for role in "${ROLES[@]}"; do
  gcloud projects add-iam-policy-binding $PROJECT_ID \
    --member="serviceAccount:${SERVICE_ACCOUNT_NAME}@${PROJECT_ID}.iam.gserviceaccount.com" \
    --role="$role"
done

# Create key
gcloud iam service-accounts keys create ${SERVICE_ACCOUNT_NAME}-key.json \
  --iam-account=${SERVICE_ACCOUNT_NAME}@${PROJECT_ID}.iam.gserviceaccount.com

cat ${SERVICE_ACCOUNT_NAME}-key.json
```

**⚠️ Important**: 
- Save the key securely
- Never commit to git
- Add to GitHub Secrets as `GCP_CREDENTIALS`
- Delete local key file after adding to GitHub

See [scripts/README.md](scripts/README.md) for detailed documentation on the setup scripts.

### Step 4: Configure GitHub Secrets

Go to your GitHub repository → Settings → Secrets and variables → Actions → New repository secret

Add the following **Secrets**:

| Secret Name | Value | Description |
|------------|-------|-------------|
| `GCP_CREDENTIALS` | Contents of `github-actions-key.json` | Service account key |
| `GCP_PROJECT_ID` | Your project ID | Google Cloud project |
| `TERRAFORM_STATE_BUCKET` | `your-project-id-terraform-state` | Terraform state bucket |
| `STRIPE_API_KEY` | Your Stripe secret key | Stripe API secret |
| `STRIPE_PUBLISHABLE_KEY` | Your Stripe publishable key | Stripe public key |
| `STRIPE_WEBHOOK_SECRET` | Your webhook secret | Stripe webhook secret |
| `ADMIN_API_KEY` | Generate secure key | Admin API key |

Add the following **Variables** (Settings → Secrets and variables → Actions → Variables):

| Variable Name | Value | Description |
|--------------|-------|-------------|
| `ENVIRONMENT` | `production` | Environment name |
| `FIRESTORE_LOCATION` | `us-central1` | Firestore location |
| `ALLOWED_ORIGINS` | `https://yourdomain.com` | CORS origins |
| `MIN_INSTANCES` | `0` | Min Cloud Run instances |
| `MAX_INSTANCES` | `10` | Max Cloud Run instances |
| `MEMORY_LIMIT` | `512Mi` | Memory limit |
| `CPU_LIMIT` | `1000m` | CPU limit (1 vCPU) |

### Step 5: Generate Secure Keys

```bash
# Generate admin API key
openssl rand -base64 32

# You can use this for ADMIN_API_KEY secret
```

## Deployment

### Automated Deployment (Recommended)

Simply push to the main branch:

```bash
git add .
git commit -m "Deploy to Cloud Run"
git push origin main
```

The GitHub Actions workflow will automatically:
1. Build the Docker image
2. Push to Artifact Registry
3. Run Terraform to deploy infrastructure
4. Deploy to Cloud Run

### Manual Deployment (Local Testing)

If you want to test locally before pushing:

```bash
# Authenticate with Google Cloud
gcloud auth application-default login

# Navigate to terraform directory
cd terraform

# Create terraform.tfvars from template
cp terraform.tfvars.template terraform.tfvars

# Edit terraform.tfvars with your values
nano terraform.tfvars

# Initialize Terraform
terraform init \
  -backend-config="bucket=your-project-id-terraform-state" \
  -backend-config="prefix=terraform/state"

# Preview changes
terraform plan

# Apply changes
terraform apply
```

## Terraform State Management

### Import Existing Resources

If you already have resources in Google Cloud:

```bash
cd terraform

# Import Firestore database
terraform import google_firestore_database.main projects/YOUR_PROJECT_ID/databases/\(default\)

# Import Cloud Run service (if exists)
terraform import google_cloud_run_service.server locations/us-central1/namespaces/YOUR_PROJECT_ID/services/blumelein-server

# Import Artifact Registry (if exists)
terraform import google_artifact_registry_repository.docker projects/YOUR_PROJECT_ID/locations/us-central1/repositories/blumelein-docker
```

### View Current State

```bash
# List all resources
terraform state list

# Show specific resource
terraform state show google_cloud_run_service.server

# Get outputs
terraform output
```

### Destroy Infrastructure (⚠️ Be Careful)

```bash
# Preview what will be destroyed
terraform plan -destroy

# Destroy all resources
terraform destroy
```

## Monitoring and Logs

### View Deployment Status

- **GitHub Actions**: Check the Actions tab in your repository
- **Cloud Run Console**: https://console.cloud.google.com/run
- **Terraform State**: Stored in your GCS bucket

### View Logs

```bash
# View Cloud Run logs
gcloud run services logs read blumelein-server \
  --region=us-central1 \
  --limit=50

# Follow logs in real-time
gcloud run services logs tail blumelein-server \
  --region=us-central1
```

### Check Service Status

```bash
# Get service details
gcloud run services describe blumelein-server \
  --region=us-central1

# Get service URL
gcloud run services describe blumelein-server \
  --region=us-central1 \
  --format='value(status.url)'

# Test the service
SERVICE_URL=$(gcloud run services describe blumelein-server --region=us-central1 --format='value(status.url)')
curl $SERVICE_URL/health
```

## Troubleshooting

### Build Failures

**Problem**: Docker build fails in GitHub Actions

**Solution**:
1. Check the Actions logs for specific errors
2. Test build locally: `docker build -t test .`
3. Verify all dependencies in `pyproject.toml`

### Terraform Errors

**Problem**: `Error: Resource already exists`

**Solution**: Import the existing resource
```bash
terraform import <resource_type>.<name> <resource_id>
```

**Problem**: `Error: Backend initialization required`

**Solution**: Re-initialize Terraform
```bash
cd terraform
rm -rf .terraform
terraform init -backend-config="bucket=YOUR_BUCKET"
```

### Permission Errors

**Problem**: `Permission denied` when deploying

**Solution**: Verify service account has all required roles
```bash
gcloud projects get-iam-policy YOUR_PROJECT_ID \
  --flatten="bindings[].members" \
  --filter="bindings.members:serviceAccount:github-actions@YOUR_PROJECT_ID.iam.gserviceaccount.com"
```

### Cloud Run Errors

**Problem**: Service returns 500 errors

**Solution**:
1. Check environment variables in Cloud Run console
2. View container logs: `gcloud run services logs read blumelein-server`
3. Verify Firestore permissions
4. Check that all secrets are set correctly

## Customization

### Change Region

Update `.github/workflows/deploy.yaml`:

```yaml
env:
  GCP_REGION: us-east1  # Change this
```

And update `FIRESTORE_LOCATION` variable in GitHub.

### Adjust Resources

Update GitHub Variables:
- `MEMORY_LIMIT`: `1Gi` for more memory
- `CPU_LIMIT`: `2000m` for 2 vCPUs
- `MAX_INSTANCES`: `50` for higher scale

### Multiple Environments

To support dev/staging/production:

1. Create separate branches: `develop`, `staging`, `main`
2. Duplicate the workflow file for each environment
3. Use different service names and variables per environment

Example:
```yaml
# .github/workflows/deploy-staging.yaml
on:
  push:
    branches:
      - staging
env:
  SERVICE_NAME: blumelein-server-staging
```

## Cost Optimization

### Free Tier

Cloud Run includes:
- 2 million requests/month
- 360,000 GB-seconds/month
- 180,000 vCPU-seconds/month

### Reduce Costs

1. Set `MIN_INSTANCES: 0` (scale to zero when idle)
2. Use smaller memory: `MEMORY_LIMIT: 256Mi`
3. Set up budget alerts:

```bash
gcloud billing budgets create \
  --billing-account=YOUR_BILLING_ACCOUNT \
  --display-name="Blumelein Monthly Budget" \
  --budget-amount=50USD \
  --threshold-rule=percent=50 \
  --threshold-rule=percent=90
```

## Security Best Practices

1. **Rotate secrets regularly**: Update GitHub Secrets every 90 days
2. **Use least privilege**: Only grant necessary IAM roles
3. **Enable audit logs**: Monitor who accesses what
4. **Use HTTPS only**: Enforce secure connections
5. **Review dependencies**: Keep packages up to date

## Next Steps

1. ✅ Set up custom domain
2. ✅ Configure Stripe webhooks with your Cloud Run URL
3. ✅ Set up monitoring and alerting
4. ✅ Configure backup strategy for Firestore
5. ✅ Set up CI/CD for multiple environments

## Support

For issues:
- Check GitHub Actions logs
- Review Terraform plan output
- Consult [Google Cloud Run docs](https://cloud.google.com/run/docs)
- Review [Terraform Google Provider docs](https://registry.terraform.io/providers/hashicorp/google/latest/docs)

