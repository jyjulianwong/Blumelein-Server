# Quick Start: Deploy to Cloud Run in 10 Minutes

Follow these steps to deploy your Blumelein Server API to Google Cloud Run using the automated Terraform + GitHub Actions pipeline.

## Prerequisites

- Google Cloud account with billing enabled
- GitHub account
- `gcloud` CLI installed

## Step 1: Prepare Google Cloud (5 minutes)

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

## Step 2: Create Service Account (2 minutes)

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

# Copy the key content (you'll need it in the next step)
cat github-actions-key.json
```

## Step 3: Configure GitHub (2 minutes)

Go to your GitHub repository → **Settings** → **Secrets and variables** → **Actions**

### Add Secrets:

1. **GCP_CREDENTIALS**: Paste contents of `github-actions-key.json`
2. **GCP_PROJECT_ID**: Your project ID
3. **TERRAFORM_STATE_BUCKET**: `your-project-id-terraform-state`
4. **STRIPE_API_KEY**: Your Stripe secret key
5. **STRIPE_PUBLISHABLE_KEY**: Your Stripe publishable key
6. **STRIPE_WEBHOOK_SECRET**: Your Stripe webhook secret
7. **ADMIN_API_KEY**: Generate with `openssl rand -base64 32`

### Add Variables (optional):

- **ENVIRONMENT**: `production`
- **ALLOWED_ORIGINS**: `https://yourdomain.com`

## Step 4: Deploy (1 minute)

```bash
# Commit and push to main branch
git add .
git commit -m "Initial deployment"
git push origin main
```

Watch the GitHub Actions tab as your application builds and deploys automatically!

## Step 5: Test Your API

```bash
# Get the service URL
gcloud run services describe blumelein-server \
  --region=us-central1 \
  --format='value(status.url)'

# Test the health endpoint
curl $(gcloud run services describe blumelein-server --region=us-central1 --format='value(status.url)')/health
```

## Success! 🎉

Your API is now live at the URL from Step 5.

- **API Docs**: `{YOUR_URL}/docs`
- **ReDoc**: `{YOUR_URL}/redoc`
- **Health Check**: `{YOUR_URL}/health`

## Next Steps

1. **Configure Stripe Webhook**: Use your Cloud Run URL
2. **Set up custom domain**: See [Terraform Deployment Guide](TERRAFORM_DEPLOYMENT.md)
3. **Monitor logs**: `gcloud run services logs tail blumelein-server --region=us-central1`

## Troubleshooting

**Build fails?**
- Check GitHub Actions logs
- Verify all secrets are set

**Can't access API?**
- Check logs: `gcloud run services logs read blumelein-server`
- Verify environment variables in Cloud Run console

**Need help?**
- See [Terraform Deployment Guide](TERRAFORM_DEPLOYMENT.md) for detailed information
- Check [Architecture Documentation](ARCHITECTURE.md)

## Clean Up (Optional)

To delete all resources:

```bash
cd terraform
terraform destroy
```

