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
  --location=us-east1 \
  --type=firestore-native

# Create Artifact Registry repository (REQUIRED - for Docker images)
gcloud artifacts repositories create gar-usea1-docker \
  --repository-format=docker \
  --location=us-east1 \
  --description="Docker repository for Blumelein Server"

# Create Terraform state bucket (REQUIRED - deployment will fail without this!)
gsutil mb -l us-east1 gs://${PROJECT_ID}-terraform-state
gsutil versioning set on gs://${PROJECT_ID}-terraform-state

# Verify the bucket was created
gsutil ls -L gs://${PROJECT_ID}-terraform-state
```

**⚠️ Important Prerequisites:**
- **Artifact Registry**: The Docker repository `gar-usea1-docker` must exist before pushing images
- **Terraform State Bucket**: Must exist before Terraform can initialize
- **First Deployment**: Requires a [conventional commit](https://www.conventionalcommits.org/) (e.g., `feat:`, `fix:`) to trigger semantic versioning and build

### Step 2: Create Service Account (2 minutes)

Use our automated scripts (recommended):

```bash
# Run the setup script (use us-east1 to match your deployment region)
./scripts/setup-service-account.sh $PROJECT_ID us-east1

# Create the key file
./scripts/create-service-account-key.sh $PROJECT_ID us-east1

# Copy the key content (you'll need it in the next step)
cat svc-usea1-tf-key.json
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

**⚠️ Important**: Only add truly sensitive values as Secrets. Project IDs should be Variables.

| Secret Name | Value | Description |
|------------|-------|-------------|
| `GCP_CREDENTIALS` | Contents of key JSON file | Service account key |
| `TERRAFORM_STATE_BUCKET` | `your-project-id-terraform-state` | Terraform state bucket (**required**, must be created first!) |
| `STRIPE_API_KEY` | Your Stripe secret key | Stripe API secret |
| `STRIPE_PUBLISHABLE_KEY` | Your Stripe publishable key | Stripe public key |
| `STRIPE_WEBHOOK_SECRET` | Your webhook secret | Stripe webhook secret |
| `ADMIN_API_KEY` | `openssl rand -base64 32` | Admin API key |

#### Add Variables (required):

**Note**: These values are NOT secrets and must be added as **Variables** (not Secrets) to avoid GitHub Actions output redaction.

| Variable Name | Value | Description |
|--------------|-------|-------------|
| `GCP_PROJECT_ID` | `your-project-id` | Google Cloud project ID (**required**) |
| `ENVIRONMENT` | `production` | Environment name (optional) |
| `ALLOWED_ORIGINS` | `https://yourdomain.com` | CORS origins (optional) |
| `FIRESTORE_LOCATION` | `us-east1` | Firestore location (optional) |
| `MIN_INSTANCES` | `0` | Min Cloud Run instances (optional) |
| `MAX_INSTANCES` | `10` | Max Cloud Run instances (optional) |
| `MEMORY_LIMIT` | `512Mi` | Memory limit (optional) |
| `CPU_LIMIT` | `1000m` | CPU limit (1 vCPU, optional) |

### Step 4: Deploy (1 minute)

The deployment uses [semantic versioning](https://semver.org/) with [conventional commits](https://www.conventionalcommits.org/). Your commit message determines the version bump:

- `feat:` → Minor version bump (e.g., 1.0.0 → 1.1.0)
- `fix:` → Patch version bump (e.g., 1.0.0 → 1.0.1)
- `BREAKING CHANGE:` → Major version bump (e.g., 1.0.0 → 2.0.0)

```bash
# Commit with a conventional commit message to trigger deployment
git add .
git commit -m "feat: initial deployment"
git push origin main
```

**Note**: Only commits with conventional commit prefixes (`feat:`, `fix:`, etc.) will trigger a build and deployment. Regular commits without these prefixes will not deploy.

Watch the GitHub Actions tab as your application builds and deploys automatically!

### Step 5: Test Your API

```bash
# Get the service URL
gcloud run services describe blumelein-server \
  --region=us-east1 \
  --format='value(status.url)'

# Test the health endpoint
curl $(gcloud run services describe blumelein-server --region=us-east1 --format='value(status.url)')/health
```

### Success! 🎉

Your API is now live. Access:

- **API Docs**: `{YOUR_URL}/docs`
- **ReDoc**: `{YOUR_URL}/redoc`
- **Health Check**: `{YOUR_URL}/health`

### Quick Start Troubleshooting

**Build doesn't start?**
- Make sure you used a [conventional commit](https://www.conventionalcommits.org/) (e.g., `feat:`, `fix:`)
- Check GitHub Actions logs for `version_bump` job output
- Regular commits without conventional prefixes will not trigger builds

**Build fails?**
- Check GitHub Actions logs
- Verify all secrets are set
- Ensure Artifact Registry repository exists: `gcloud artifacts repositories describe gar-usea1-docker --location=us-east1`

**Terraform fails with "must provide an image name"?**
- This means no Docker image was built (likely no conventional commit was used)
- Use a conventional commit: `git commit -m "feat: initial deployment"`
- Verify `build-and-push` job ran successfully in GitHub Actions

**Can't access API?**
- Check logs: `gcloud run services logs read blumelein-server --region=us-east1`
- Verify environment variables in Cloud Run console

---

## Automated Terraform Deployment

This section provides detailed information about the Terraform-based deployment pipeline.

### Overview

The deployment setup includes:

- **Semantic Versioning** with conventional commits for automated version management
- **Revision Management** with version-based naming for Cloud Run revisions
- **Terraform** for infrastructure as code
- **GitHub Actions** for automated CI/CD
- **Cloud Run** for serverless container deployment
- **Artifact Registry** for Docker image storage
- **Firestore** for database
- **Automatic deployments** on push to main branch (with conventional commits)

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
  --location=us-east1 \
  --type=firestore-native

# Create Artifact Registry repository (REQUIRED for Docker images)
gcloud artifacts repositories create gar-usea1-docker \
  --repository-format=docker \
  --location=us-east1 \
  --description="Docker repository for Blumelein Server"
```

#### Step 2: Create Terraform State Bucket

**⚠️ CRITICAL**: Terraform needs a GCS bucket to store its state. **Deployment will fail if this bucket doesn't exist!**

```bash
# Create bucket for Terraform state (MUST match your region!)
export TERRAFORM_BUCKET="${PROJECT_ID}-terraform-state"
gsutil mb -l us-east1 gs://${TERRAFORM_BUCKET}

# Enable versioning for safety (protects against accidental state deletion)
gsutil versioning set on gs://${TERRAFORM_BUCKET}

# Verify the bucket was created successfully
gsutil ls -L gs://${TERRAFORM_BUCKET}
```

**Common Error**: If you see `Error: Failed to get existing workspaces: querying Cloud Storage failed: storage: bucket doesn't exist`, it means this step was skipped. Create the bucket using the commands above.

**Note**: The bucket name you create here MUST match the value you set in the GitHub secret `TERRAFORM_STATE_BUCKET` (typically `your-project-id-terraform-state`).

#### Step 3: Create Service Account for GitHub Actions

We provide automated scripts to create a properly configured service account following the naming convention:
`svc-{region-abbrev}-tf@{project}.iam.gserviceaccount.com`

**Automated Setup (Recommended):**

```bash
# Run the setup script (use us-east1 to match your deployment region)
./scripts/setup-service-account.sh $PROJECT_ID us-east1

# Create the key file
./scripts/create-service-account-key.sh $PROJECT_ID us-east1

# Verify permissions (optional)
./scripts/verify-service-account.sh $PROJECT_ID us-east1
```

This creates a service account with the naming pattern `svc-usea1-tf@{project}.iam.gserviceaccount.com` and grants all necessary permissions.

**Manual Setup (Alternative):**

If you prefer manual setup:

```bash
# Create service account
REGION_ABBREV="usea1"  # us-east1 abbreviated
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

The deployment uses **semantic versioning** with **conventional commits**. Use these commit message formats:

- `feat: description` → Minor version bump (new features)
- `fix: description` → Patch version bump (bug fixes)
- `feat!: description` or `BREAKING CHANGE:` → Major version bump

**Deploy to Cloud Run:**

```bash
git add .
git commit -m "feat: add new feature"  # Use conventional commit format!
git push origin main
```

The GitHub Actions workflow will automatically:
1. **Version**: Determine version bump from commit messages (semantic-release)
2. **Build**: Build Docker image with the new version tag
3. **Push**: Push to Artifact Registry
4. **Deploy**: Run Terraform to deploy infrastructure to Cloud Run

**Important**: 
- Only commits with conventional prefixes (`feat:`, `fix:`, `chore:`, etc.) trigger the build and deploy
- Regular commits without these prefixes will **not** trigger deployment
- See the [Versioning Guide](VERSIONING.md) for more details on semantic versioning

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
terraform import google_cloud_run_service.server locations/us-east1/namespaces/YOUR_PROJECT_ID/services/blumelein-server

# Import Artifact Registry (if exists)
terraform import google_artifact_registry_repository.docker projects/YOUR_PROJECT_ID/locations/us-east1/repositories/blumelein-docker
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

### Cloud Run Revision Management

The deployment automatically creates Cloud Run revisions with semantic version names for easy tracking and rollback.

#### Revision Naming Convention

Each deployment creates a new revision named: `{service-name}-v{version}`

Examples:
- `blumelein-server-v1-0-0` (version 1.0.0)
- `blumelein-server-v1-2-3` (version 1.2.3)
- `blumelein-server-v2-0-0` (version 2.0.0)

#### View Revisions

```bash
# List all revisions
gcloud run revisions list \
  --service=blumelein-server \
  --region=us-east1

# Describe a specific revision
gcloud run revisions describe blumelein-server-v1-2-3 \
  --region=us-east1
```

#### Rollback to Previous Revision

If you need to rollback to a previous version:

```bash
# Split traffic to test old revision (50/50 split)
gcloud run services update-traffic blumelein-server \
  --region=us-east1 \
  --to-revisions=blumelein-server-v1-2-3=50,blumelein-server-v1-3-0=50

# Or rollback completely to old revision
gcloud run services update-traffic blumelein-server \
  --region=us-east1 \
  --to-revisions=blumelein-server-v1-2-3=100
```

#### Delete Old Revisions

Cloud Run keeps all revisions by default. To clean up old revisions:

```bash
# Delete a specific revision
gcloud run revisions delete blumelein-server-v1-0-0 \
  --region=us-east1 \
  --quiet

# Or use a script to delete all except the latest 5
gcloud run revisions list \
  --service=blumelein-server \
  --region=us-east1 \
  --format="value(metadata.name)" \
  --sort-by="~metadata.creationTimestamp" \
  | tail -n +6 \
  | xargs -I {} gcloud run revisions delete {} --region=us-east1 --quiet
```

**Benefits of Version-Based Revisions:**
- ✅ **Easy Identification**: Quickly see which version is deployed
- ✅ **Simple Rollback**: Rollback to any previous version by name
- ✅ **Audit Trail**: Track deployment history with semantic versions
- ✅ **Traffic Splitting**: Test new versions with gradual rollout
- ✅ **Blue-Green Deployments**: Run multiple versions simultaneously

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
  --region=us-east1 \
  --limit=50

# Follow logs in real-time
gcloud run services logs tail blumelein-server \
  --region=us-east1

# View logs with Cloud Logging
gcloud logging read "resource.type=cloud_run_revision AND resource.labels.service_name=blumelein-server" --limit 50
```

### Check Service Status

```bash
# Get service details
gcloud run services describe blumelein-server \
  --region=us-east1

# Get service URL
gcloud run services describe blumelein-server \
  --region=us-east1 \
  --format='value(status.url)'

# Test the service
SERVICE_URL=$(gcloud run services describe blumelein-server --region=us-east1 --format='value(status.url)')
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

### Terraform State Bucket Errors

**Problem**: `Error: Failed to get existing workspaces: querying Cloud Storage failed: storage: bucket doesn't exist`

**Cause**: The Terraform state bucket was not created before running the deployment workflow.

**Solution**: 
1. Create the Terraform state bucket manually:
   ```bash
   export PROJECT_ID="your-project-id"
   gcloud config set project $PROJECT_ID
   
   # Create the bucket (use us-east1 to match your deployment region)
   gsutil mb -l us-east1 gs://${PROJECT_ID}-terraform-state
   
   # Enable versioning for state file protection
   gsutil versioning set on gs://${PROJECT_ID}-terraform-state
   
   # Verify it was created
   gsutil ls -L gs://${PROJECT_ID}-terraform-state
   ```

2. Verify your GitHub secret `TERRAFORM_STATE_BUCKET` matches the bucket name (e.g., `your-project-id-terraform-state`)

3. Re-run your GitHub Actions workflow

**Prevention**: Always complete Step 1 and Step 2 of the Quick Start before pushing code to trigger deployment.

### Build Failures

**Problem**: Docker build fails in GitHub Actions

**Solution**:
1. Check the Actions logs for specific errors
2. Test build locally: `docker build -t test .`
3. Verify all dependencies in `pyproject.toml`

### Terraform Errors

**Problem**: `Error creating Service: must provide an image name to deploy`

**Cause**: This error occurs when Terraform tries to create a Cloud Run service without a valid Docker image. This happens when:
1. No conventional commit was used (e.g., `feat:`, `fix:`), so semantic versioning didn't trigger a build
2. The `build-and-push` job was skipped, resulting in an empty `server_image_tag` variable
3. The `build-and-push` job ran but the `image_tag` output was not properly exported or received by `terraform-deploy`

**Solution**:

**Step 1: Verify your commit uses conventional format**
```bash
# Good examples:
git commit -m "feat: add new feature"
git commit -m "fix: fix bug"
git commit -m "chore: update dependencies"

# Bad examples:
git commit -m "update code"
git commit -m "changes"
```

**Step 2: Check GitHub Actions logs**

Go to GitHub → Actions → Click on the failed workflow run

Check the **version_bump** job output:
```
Version:   1.0.5
Tag:       v1.0.5
Released:  true    <-- Must be 'true' for build to run!
```

If `Released: false`, semantic-release didn't detect a version change. This can happen if:
- The last commit was already released
- No conventional commits since last release
- Commit is a non-releasing type (like `docs:`, `style:`)

**Step 3: Check build-and-push job**

Look for the "📦 Export image tag" step. You should see:
```
DEBUG - GCP_REGION: us-east1
DEBUG - GCP_PROJECT_ID: your-project-id
DEBUG - DOCKER_REPOSITORY: gar-usea1-docker
DEBUG - SERVICE_NAME: blumelein-server
DEBUG - VERSION: 1.0.5
DEBUG - IMAGE_TAG from env: us-east1-docker.pkg.dev/...
DEBUG - Final IMAGE_TAG: us-east1-docker.pkg.dev/PROJECT/REPO/SERVICE:1.0.5
```

**Common Issue**: If `DEBUG - Image tag from build-and-push` shows as empty in the terraform-deploy step, this is caused by **GitHub Actions secret redaction**. GitHub automatically censors any output containing secret values.

**Solution**: Ensure `GCP_PROJECT_ID` is configured as a **Variable** (not Secret) in GitHub:
1. Go to GitHub → Settings → Secrets and variables → Actions
2. Click the **Variables** tab
3. Add `GCP_PROJECT_ID` as a variable
4. Remove it from the Secrets tab if it exists there

**Why**: Project IDs are not sensitive information. When stored as secrets, GitHub redacts them from all outputs, causing the image tag to become empty.

**Step 4: Check terraform-deploy job**

Look for the "📝 Generate terraform.tfvars" step. You should see:
```
DEBUG - Version from version_bump: 1.0.5
DEBUG - Image tag from build-and-push: us-east1-docker.pkg.dev/...
DEBUG - Generated revision suffix: v1-0-5
DEBUG - Checking server_image_tag in tfvars:
server_image_tag = "us-east1-docker.pkg.dev/PROJECT/REPO/SERVICE:1.0.5"
```

If `server_image_tag` is empty, the issue is with job output passing between jobs.

**Step 5: Force a new deployment**

If the issue persists, you can force a new version:

```bash
# Create an empty commit with a conventional message
git commit --allow-empty -m "fix: force new deployment"
git push origin main
```

**Prevention**: 
- Always use conventional commit messages when deploying
- Check GitHub Actions logs to verify all three jobs completed successfully
- Ensure your semantic-release configuration is correct in `pyproject.toml`

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
  --region us-east1 \
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
  --region us-east1
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
  --region=us-east1
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
