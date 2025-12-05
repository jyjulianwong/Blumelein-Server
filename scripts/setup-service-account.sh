#!/bin/bash

# Setup Service Account for Terraform/GitHub Actions
# This script creates a service account following the naming convention:
# svc-{region-abbrev}-tf@{project}.iam.gserviceaccount.com

set -e

# Configuration
PROJECT_ID="${1:-}"
REGION="${2:-us-central1}"

if [ -z "$PROJECT_ID" ]; then
  echo "Error: PROJECT_ID is required"
  echo "Usage: ./setup-service-account.sh PROJECT_ID [REGION]"
  echo "Example: ./setup-service-account.sh my-project-id us-central1"
  exit 1
fi

# Convert region to abbreviation
# us-central1 -> usce1
# us-east1 -> usea1
# europe-west2 -> euwe2
convert_region() {
  local region=$1
  # Extract first 2 chars of each part and the number
  if [[ $region =~ ^([a-z]{2})[a-z]*-([a-z]{2})[a-z]*([0-9]+)$ ]]; then
    echo "${BASH_REMATCH[1]}${BASH_REMATCH[2]}${BASH_REMATCH[3]}"
  else
    # Fallback: just remove dashes
    echo "${region//-/}"
  fi
}

REGION_ABBREV=$(convert_region "$REGION")
SERVICE_ACCOUNT_NAME="svc-${REGION_ABBREV}-tf"
SERVICE_ACCOUNT_EMAIL="${SERVICE_ACCOUNT_NAME}@${PROJECT_ID}.iam.gserviceaccount.com"

echo "=========================================="
echo "Setting up Service Account for Terraform"
echo "=========================================="
echo "Project ID: $PROJECT_ID"
echo "Region: $REGION ($REGION_ABBREV)"
echo "Service Account: $SERVICE_ACCOUNT_EMAIL"
echo ""

# Set project
gcloud config set project "$PROJECT_ID"

# Create service account
echo "Creating service account..."
gcloud iam service-accounts create "$SERVICE_ACCOUNT_NAME" \
  --display-name="Terraform Service Account ($REGION)" \
  --description="Service account for Terraform deployments via GitHub Actions" \
  2>/dev/null || echo "Service account already exists"

# Define IAM roles
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

# Grant roles
echo ""
echo "Granting IAM roles..."
for role in "${ROLES[@]}"; do
  echo "  - Granting $role..."
  gcloud projects add-iam-policy-binding "$PROJECT_ID" \
    --member="serviceAccount:$SERVICE_ACCOUNT_EMAIL" \
    --role="$role" \
    --condition=None \
    --quiet > /dev/null 2>&1 || true
done

echo ""
echo "✅ Service account setup complete!"
echo ""
echo "Service Account Email: $SERVICE_ACCOUNT_EMAIL"
echo ""
echo "Next steps:"
echo "1. Create a key for this service account:"
echo "   gcloud iam service-accounts keys create ${SERVICE_ACCOUNT_NAME}-key.json \\"
echo "     --iam-account=$SERVICE_ACCOUNT_EMAIL"
echo ""
echo "2. Add the key to GitHub Secrets as 'GCP_CREDENTIALS'"
echo "   cat ${SERVICE_ACCOUNT_NAME}-key.json"
echo ""
echo "3. Update your .github/workflows/deploy.yaml to use this service account"
echo ""

