# Deployment Guide

This comprehensive guide covers deploying the Blumelein Server API to Google Cloud Platform. Choose the path that best fits your needs:

- **[Quick Start](#quick-start)** - Get deployed in 10 minutes (recommended for first-time users)
- **[Automated Terraform Deployment](#automated-terraform-deployment)** - Production-ready infrastructure as code
- **[Alternative Deployment Options](#alternative-deployment-options)** - App Engine and GKE

## Quick Start

Deploy to Cloud Run in 10 minutes using automated Terraform + GitHub Actions.

### Prerequisites

- Google Cloud account with billing enabled
- GitHub account
- `gcloud` CLI installed

### Step 1: Prepare Google Cloud (5 minutes)

```bash
# Set your project ID
export PROJECT_ID="your-project-id"
gcloud config set project $PROJECT_ID

# Enable APIs
gcloud services enable run.googleapis.com \
  firestore.googleapis.com \
  artifactregistry.googleapis.com \
  cloudbuild.googleapis.com

# Create Firestore database
gcloud firestore databases create \
  --location=us-central1 \
  --type=firestore-native

# Create Terraform state bucket
gsutil mb -l us-central1 gs://${PROJECT_ID}-terraform-state
gsutil versioning set on gs://${PROJECT_ID}-terraform-state
```

### Step 2: Create Service Account (2 minutes)

Use our automated scripts (recommended):

```bash
# Run the setup script
./scripts/setup-service-account.sh $PROJECT_ID us-central1

# Create the key file
./scripts/create-service-account-key.sh $PROJECT_ID us-central1

# Copy the key content (you'll need it in the next step)
cat svc-usce1-tf-key.json
```

Or manually create the service account:

```bash
# Create service account
gcloud iam service-accounts create github-actions \
  --display-name="GitHub Actions"

# Grant permissions
for role in run.admin iam.serviceAccountUser artifactregistry.admin datastore.owner storage.admin; do
  gcloud projects add-iam-policy-binding $PROJECT_ID \
    --member="serviceAccount:github-actions@${PROJECT_ID}.iam.gserviceaccount.com" \
    --role="roles/$role"
done

# Create key
gcloud iam service-accounts keys create github-actions-key.json \
  --iam-account=github-actions@${PROJECT_ID}.iam.gserviceaccount.com

# Copy the key content
cat github-actions-key.json
```

### Step 3: Configure GitHub (2 minutes)

Go to your GitHub repository → **Settings** → **Secrets and variables** → **Actions**

#### Add Secrets:

| Secret Name | Value | Description |
|------------|-------|-------------|
| `GCP_CREDENTIALS` | Contents of key JSON file | Service account key |
| `GCP_PROJECT_ID` | Your project ID | Google Cloud project |
| `TERRAFORM_STATE_BUCKET` | `your-project-id-terraform-state` | Terraform state bucket |
| `STRIPE_API_KEY` | Your Stripe secret key | Stripe API secret |
| `STRIPE_PUBLISHABLE_KEY` | Your Stripe publishable key | Stripe public key |
| `STRIPE_WEBHOOK_SECRET` | Your webhook secret | Stripe webhook secret |
| `ADMIN_API_KEY` | `openssl rand -base64 32` | Admin API key |

#### Add Variables (optional):

| Variable Name | Value | Description |
|--------------|-------|-------------|
| `ENVIRONMENT` | `production` | Environment name |
| `ALLOWED_ORIGINS` | `https://yourdomain.com` | CORS origins |
| `FIRESTORE_LOCATION` | `us-central1` | Firestore location |
| `MIN_INSTANCES` | `0` | Min Cloud Run instances |
| `MAX_INSTANCES` | `10` | Max Cloud Run instances |
| `MEMORY_LIMIT` | `512Mi` | Memory limit |
| `CPU_LIMIT` | `1000m` | CPU limit (1 vCPU) |

### Step 4: Deploy (1 minute)

```bash
# Commit and push to main branch
git add .
git commit -m "Initial deployment"
git push origin main
```

Watch the GitHub Actions tab as your application builds and deploys automatically!

### Step 5: Test Your API

```bash
# Get the service URL
gcloud run services describe blumelein-server \
  --region=us-central1 \
  --format='value(status.url)'

# Test the health endpoint
curl $(gcloud run services describe blumelein-server --region=us-central1 --format='value(status.url)')/health
```

### Success! 🎉

Your API is now live. Access:

- **API Docs**: `{YOUR_URL}/docs`
- **ReDoc**: `{YOUR_URL}/redoc`
- **Health Check**: `{YOUR_URL}/health`

### Quick Start Troubleshooting

**Build fails?**
- Check GitHub Actions logs
- Verify all secrets are set

**Can't access API?**
- Check logs: `gcloud run services logs read blumelein-server`
- Verify environment variables in Cloud Run console

---

## Automated Terraform Deployment

This section provides detailed information about the Terraform-based deployment pipeline.

### Overview

The deployment setup includes:

- **Terraform** for infrastructure as code
- **GitHub Actions** for automated CI/CD
- **Cloud Run** for serverless container deployment
- **Artifact Registry** for Docker image storage
- **Firestore** for database
- **Automatic deployments** on push to main branch

### Prerequisites

1. **Google Cloud Project** with billing enabled
2. **GitHub repository** for your code
3. **gcloud CLI** installed locally (for initial setup)
4. **Terraform** installed locally (optional, for local testing)

### Initial Setup

#### Step 1: Create Google Cloud Resources

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

#### Step 2: Create Terraform State Bucket

Terraform needs a GCS bucket to store its state:

```bash
# Create bucket for Terraform state
export TERRAFORM_BUCKET="${PROJECT_ID}-terraform-state"
gsutil mb -l us-central1 gs://${TERRAFORM_BUCKET}

# Enable versioning for safety
gsutil versioning set on gs://${TERRAFORM_BUCKET}
```

#### Step 3: Create Service Account for GitHub Actions

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

### Deployment

#### Automated Deployment (Recommended)

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

#### Manual Deployment (Local Testing)

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

### Terraform State Management

#### Import Existing Resources

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

#### View Current State

```bash
# List all resources
terraform state list

# Show specific resource
terraform state show google_cloud_run_service.server

# Get outputs
terraform output
```

#### Destroy Infrastructure (⚠️ Be Careful)

```bash
# Preview what will be destroyed
terraform plan -destroy

# Destroy all resources
terraform destroy
```

---

## Monitoring and Logging

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

# View logs with Cloud Logging
gcloud logging read "resource.type=cloud_run_revision AND resource.labels.service_name=blumelein-server" --limit 50
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

### Set Up Alerts

1. Go to Cloud Console → Monitoring
2. Create alerting policy for:
   - High error rate
   - High latency
   - Low availability

---

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

**Problem**: 503 Service Unavailable

**Solution**: Check container logs for startup errors

**Problem**: Memory errors

**Solution**: Increase memory allocation

**Problem**: Timeout errors

**Solution**: Increase timeout limit or optimize code

---

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

### Configure Scaling

```bash
gcloud run services update blumelein-server \
  --region us-central1 \
  --min-instances 1 \
  --max-instances 100 \
  --concurrency 80
```

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

---

## Security Best Practices

### Use Secret Manager

Instead of environment variables, use Google Cloud Secret Manager:

```bash
# Create secrets
echo -n "sk_live_your_key" | gcloud secrets create stripe-api-key --data-file=-

# Grant Cloud Run access to secrets
gcloud run services update blumelein-server \
  --update-secrets=STRIPE_API_KEY=stripe-api-key:latest
```

### Enable HTTPS and Custom Domains

Cloud Run automatically provides HTTPS. For custom domains:

```bash
gcloud run domain-mappings create \
  --service blumelein-server \
  --domain api.yourdomain.com \
  --region us-central1
```

### Configure CORS Properly

Update `ALLOWED_ORIGINS` to include only your frontend domain:

```bash
ALLOWED_ORIGINS=https://yourdomain.com,https://www.yourdomain.com
```

### Configure Stripe Webhook

1. Go to your Stripe Dashboard
2. Navigate to Developers → Webhooks
3. Click "Add endpoint"
4. Enter your Cloud Run URL + `/payments/webhook`
5. Select events to listen for: `payment_intent.succeeded`
6. Copy the signing secret and update your environment variables

### Best Practices Checklist

1. **Rotate secrets regularly**: Update GitHub Secrets every 90 days
2. **Use least privilege**: Only grant necessary IAM roles
3. **Enable audit logs**: Monitor who accesses what
4. **Use HTTPS only**: Enforce secure connections
5. **Review dependencies**: Keep packages up to date
6. **Implement rate limiting**: Consider adding rate limiting middleware or using Google Cloud Armor

---

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

4. Configure min instances to 0 for development environments
5. Set appropriate memory limits (512Mi is usually sufficient)

---

## Alternative Deployment Options

### Option 1: Deploy to App Engine

App Engine provides a fully managed platform with automatic scaling.

#### Step 1: Create `app.yaml`

Create a file named `app.yaml` in the project root:

```yaml
runtime: python311
entrypoint: uvicorn src.blumelein_server.main:app --host 0.0.0.0 --port $PORT

env_variables:
  STRIPE_API_KEY: "sk_live_your_key"
  STRIPE_PUBLISHABLE_KEY: "pk_live_your_key"
  STRIPE_WEBHOOK_SECRET: "whsec_your_secret"
  ADMIN_API_KEY: "your_secure_admin_key"
  ENVIRONMENT: "production"
  ALLOWED_ORIGINS: "https://your-frontend-domain.com"

automatic_scaling:
  min_instances: 0
  max_instances: 10
  target_cpu_utilization: 0.65
```

#### Step 2: Enable APIs and Deploy

```bash
gcloud services enable cloudbuild.googleapis.com
gcloud app deploy
```

### Option 2: Deploy to GKE (Google Kubernetes Engine)

For advanced users who need fine-grained control.

#### Step 1: Create a GKE Cluster

```bash
gcloud container clusters create blumelein-cluster \
  --num-nodes=2 \
  --machine-type=e2-small \
  --region=us-central1
```

#### Step 2: Build and Push Image

```bash
gcloud builds submit --tag gcr.io/YOUR_PROJECT_ID/blumelein-server
```

#### Step 3: Create Kubernetes Deployment

Create `k8s-deployment.yaml`:

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: blumelein-server
spec:
  replicas: 2
  selector:
    matchLabels:
      app: blumelein-server
  template:
    metadata:
      labels:
        app: blumelein-server
    spec:
      containers:
      - name: blumelein-server
        image: gcr.io/YOUR_PROJECT_ID/blumelein-server
        ports:
        - containerPort: 8000
        env:
        - name: STRIPE_API_KEY
          valueFrom:
            secretKeyRef:
              name: blumelein-secrets
              key: stripe-api-key
---
apiVersion: v1
kind: Service
metadata:
  name: blumelein-server
spec:
  type: LoadBalancer
  ports:
  - port: 80
    targetPort: 8000
  selector:
    app: blumelein-server
```

#### Step 4: Deploy to GKE

```bash
kubectl apply -f k8s-deployment.yaml
```

---

## Next Steps

1. ✅ Set up custom domain
2. ✅ Configure Stripe webhooks with your Cloud Run URL
3. ✅ Set up monitoring and alerting
4. ✅ Configure backup strategy for Firestore
5. ✅ Set up CI/CD for multiple environments
6. ✅ Implement database persistence (migrate from in-memory if needed)
7. ✅ Add automated testing in CI/CD

---

## Support

For issues:
- Check GitHub Actions logs
- Review Terraform plan output
- Consult [Google Cloud Run docs](https://cloud.google.com/run/docs)
- Review [Terraform Google Provider docs](https://registry.terraform.io/providers/hashicorp/google/latest/docs)
- Check application logs for runtime issues
- Contact Stripe support for payment-related issues
