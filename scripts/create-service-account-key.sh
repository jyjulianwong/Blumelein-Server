#!/bin/bash

# Create Service Account Key
# This script creates a JSON key for the Terraform service account

set -e

PROJECT_ID="${1:-}"
REGION="${2:-us-central1}"

if [ -z "$PROJECT_ID" ]; then
  echo "Error: PROJECT_ID is required"
  echo "Usage: ./create-service-account-key.sh PROJECT_ID [REGION]"
  exit 1
fi

# Convert region to abbreviation
convert_region() {
  local region=$1
  if [[ $region =~ ^([a-z]{2})[a-z]*-([a-z]{2})[a-z]*([0-9]+)$ ]]; then
    echo "${BASH_REMATCH[1]}${BASH_REMATCH[2]}${BASH_REMATCH[3]}"
  else
    echo "${region//-/}"
  fi
}

REGION_ABBREV=$(convert_region "$REGION")
SERVICE_ACCOUNT_NAME="svc-${REGION_ABBREV}-tf"
SERVICE_ACCOUNT_EMAIL="${SERVICE_ACCOUNT_NAME}@${PROJECT_ID}.iam.gserviceaccount.com"
KEY_FILE="${SERVICE_ACCOUNT_NAME}-key.json"

echo "Creating key for: $SERVICE_ACCOUNT_EMAIL"

gcloud iam service-accounts keys create "$KEY_FILE" \
  --iam-account="$SERVICE_ACCOUNT_EMAIL" \
  --project="$PROJECT_ID"

echo ""
echo "✅ Key created: $KEY_FILE"
echo ""
echo "⚠️  IMPORTANT: Keep this file secure and never commit it to git!"
echo ""
echo "Next steps:"
echo "1. Copy the contents of this file:"
echo "   cat $KEY_FILE"
echo ""
echo "2. Go to GitHub → Repository Settings → Secrets and variables → Actions"
echo ""
echo "3. Create a new secret called 'GCP_CREDENTIALS'"
echo ""
echo "4. Paste the entire JSON content"
echo ""
echo "5. Delete the local key file for security:"
echo "   rm $KEY_FILE"
echo ""

