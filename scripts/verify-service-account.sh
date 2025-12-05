#!/bin/bash

# Verify Service Account Permissions
# This script checks that the service account has all required permissions

set -e

PROJECT_ID="${1:-}"
REGION="${2:-us-central1}"

if [ -z "$PROJECT_ID" ]; then
  echo "Error: PROJECT_ID is required"
  echo "Usage: ./verify-service-account.sh PROJECT_ID [REGION]"
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
SERVICE_ACCOUNT_EMAIL="svc-${REGION_ABBREV}-tf@${PROJECT_ID}.iam.gserviceaccount.com"

echo "=========================================="
echo "Verifying Service Account Permissions"
echo "=========================================="
echo "Service Account: $SERVICE_ACCOUNT_EMAIL"
echo ""

# Expected roles
EXPECTED_ROLES=(
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

# Get current roles
CURRENT_ROLES=$(gcloud projects get-iam-policy "$PROJECT_ID" \
  --flatten="bindings[].members" \
  --filter="bindings.members:serviceAccount:$SERVICE_ACCOUNT_EMAIL" \
  --format="value(bindings.role)")

echo "Checking permissions..."
echo ""

MISSING_ROLES=()

for role in "${EXPECTED_ROLES[@]}"; do
  if echo "$CURRENT_ROLES" | grep -q "^$role$"; then
    echo "✅ $role"
  else
    echo "❌ $role (MISSING)"
    MISSING_ROLES+=("$role")
  fi
done

echo ""

if [ ${#MISSING_ROLES[@]} -eq 0 ]; then
  echo "✅ All required permissions are configured!"
else
  echo "⚠️  Missing ${#MISSING_ROLES[@]} role(s)"
  echo ""
  echo "To grant missing roles, run:"
  for role in "${MISSING_ROLES[@]}"; do
    echo "  gcloud projects add-iam-policy-binding $PROJECT_ID \\"
    echo "    --member=\"serviceAccount:$SERVICE_ACCOUNT_EMAIL\" \\"
    echo "    --role=\"$role\""
    echo ""
  done
fi

