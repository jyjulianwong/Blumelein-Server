#!/bin/bash

# Setup Artifact Registry for Blumelein Server Deployment
# This script sets up the Artifact Registry repository needed before Terraform deployment.
# Note: Cloud Run will use the same service account as Terraform (no separate SA needed).

set -e

# Configuration
PROJECT_ID="${1:-}"
REGION="${2:-us-east1}"

if [ -z "$PROJECT_ID" ]; then
  echo "Error: PROJECT_ID is required"
  echo "Usage: ./setup-artifact-registry.sh PROJECT_ID [REGION]"
  echo "Example: ./setup-artifact-registry.sh my-project-id us-east1"
  exit 1
fi

# Convert region to abbreviation for naming
convert_region() {
  local region=$1
  if [[ $region =~ ^([a-z]{2})[a-z]*-([a-z]{2})[a-z]*([0-9]+)$ ]]; then
    echo "${BASH_REMATCH[1]}${BASH_REMATCH[2]}${BASH_REMATCH[3]}"
  else
    echo "${region//-/}"
  fi
}

REGION_ABBREV=$(convert_region "$REGION")
REPO_NAME="gar-${REGION_ABBREV}-docker"

echo "=============================================="
echo "Setting up Artifact Registry"
echo "=============================================="
echo "Project ID: $PROJECT_ID"
echo "Region: $REGION"
echo ""
echo "Will create:"
echo "  • Artifact Registry: $REPO_NAME"
echo ""
echo "Note: Cloud Run will use the Terraform service account"
echo "      (svc-${REGION_ABBREV}-tf@${PROJECT_ID}.iam.gserviceaccount.com)"
echo ""

# Set project
gcloud config set project "$PROJECT_ID"

# Create Artifact Registry repository
echo "================================================"
echo "Creating Artifact Registry repository"
echo "================================================"
gcloud artifacts repositories create "$REPO_NAME" \
  --repository-format=docker \
  --location="$REGION" \
  --description="Docker repository for Blumelein Server" \
  2>/dev/null || echo "✓ Artifact Registry already exists"

echo "✅ Artifact Registry ready: ${REGION}-docker.pkg.dev/${PROJECT_ID}/${REPO_NAME}"
echo ""

# Summary
echo "================================================"
echo "✅ Artifact Registry setup complete!"
echo "================================================"
echo ""
echo "Summary:"
echo "  ✓ Artifact Registry: ${REGION}-docker.pkg.dev/${PROJECT_ID}/${REPO_NAME}"
echo "  ✓ Service Account: svc-${REGION_ABBREV}-tf@${PROJECT_ID}.iam.gserviceaccount.com"
echo "    (will be used by both Terraform and Cloud Run)"
echo ""
echo "Next steps:"
echo "  1. Ensure Terraform SA has roles/datastore.user and roles/logging.logWriter"
echo "  2. Push your Docker image to the Artifact Registry"
echo "  3. Run Terraform deployment (GitHub Actions or manual)"
echo ""

