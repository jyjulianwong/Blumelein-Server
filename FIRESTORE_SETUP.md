# Firestore Setup Guide

This guide will help you set up Google Cloud Firestore for the Blumelein Server API.

## Prerequisites

- Google Cloud account
- `gcloud` CLI installed and configured
- Project with billing enabled

## Step 1: Create a Google Cloud Project

If you don't already have a project:

```bash
# Create a new project
gcloud projects create YOUR_PROJECT_ID --name="Blumelein Flower Shop"

# Set as default project
gcloud config set project YOUR_PROJECT_ID

# Enable billing (required for Firestore)
# Visit: https://console.cloud.google.com/billing
```

## Step 2: Enable Firestore API

```bash
# Enable Firestore API
gcloud services enable firestore.googleapis.com

# Enable other required APIs
gcloud services enable cloudbuild.googleapis.com
gcloud services enable run.googleapis.com
```

## Step 3: Create Firestore Database

### Option A: Using Console (Recommended for first time)

1. Go to [Firestore Console](https://console.cloud.google.com/firestore)
2. Click "Create Database"
3. Choose a mode:
   - **Native mode** (recommended) - Better for mobile/web apps
   - **Datastore mode** - Better for server apps
4. Select a location (choose closest to your users)
5. Click "Create Database"

### Option B: Using CLI

```bash
# Create Firestore database in Native mode
gcloud firestore databases create --location=us-central

# View database info
gcloud firestore databases describe --database="(default)"
```

## Step 4: Authenticate with Google Cloud

### For Local Development

Use Application Default Credentials (ADC) for local development:

```bash
# Authenticate with your Google Cloud account
gcloud auth application-default login

# This will open a browser window for authentication
# After authentication, credentials are stored automatically
```

This method is preferred because:
- No service account key files to manage
- Uses your own Google Cloud credentials
- More secure than key files
- Same authentication method works across all Google Cloud SDKs

### For Production (Cloud Run)

When deploying to Cloud Run, authentication is automatic. Cloud Run uses the default compute service account.

Ensure the service account has Firestore permissions:

```bash
# Grant Firestore permissions to default compute service account
gcloud projects add-iam-policy-binding YOUR_PROJECT_ID \
    --member="serviceAccount:YOUR_PROJECT_NUMBER-compute@developer.gserviceaccount.com" \
    --role="roles/datastore.user"
```

### Alternative: Service Account Key (Not Recommended)

If you need a service account key for CI/CD or specific use cases:

```bash
# Create a service account
gcloud iam service-accounts create blumelein-api \
    --display-name="Blumelein API Service Account"

# Grant Firestore permissions
gcloud projects add-iam-policy-binding YOUR_PROJECT_ID \
    --member="serviceAccount:blumelein-api@YOUR_PROJECT_ID.iam.gserviceaccount.com" \
    --role="roles/datastore.user"

# Generate and download key file
gcloud iam service-accounts keys create ~/blumelein-service-account.json \
    --iam-account=blumelein-api@YOUR_PROJECT_ID.iam.gserviceaccount.com

# Set environment variable
export GOOGLE_APPLICATION_CREDENTIALS=~/blumelein-service-account.json

# Keep this file secure and never commit it to version control!
```

## Step 5: Configure Environment Variables

### Local Development

Update your `.env` file:

```env
DATABASE_TYPE=firestore
GOOGLE_CLOUD_PROJECT=your-project-id
GOOGLE_CLOUD_LOCATION=us-central1
```

Make sure you've authenticated:

```bash
gcloud auth application-default login
```

### Production (Cloud Run)

```bash
gcloud run services update blumelein-server \
  --region us-central1 \
  --set-env-vars="
DATABASE_TYPE=firestore,
GOOGLE_CLOUD_PROJECT=your-project-id,
GOOGLE_CLOUD_LOCATION=us-central1
"
```

## Step 6: Test the Connection

Run the API locally:

```bash
# Make sure dependencies are installed
uv sync

# Run the server
uv run uvicorn src.blumelein_server.main:app --reload
```

You should see in the startup logs:

```
🌸 Blumelein Server starting up...
📍 Environment: development
🔑 Stripe configured: Yes
📊 Firestore initialized (project: your-project-id)
```

## Step 7: Verify Firestore is Working

### Create a Test Order

```bash
curl -X POST http://localhost:8000/orders \
  -H "Content-Type: application/json" \
  -d '{
    "items": [
      {
        "main_colours": ["red", "pink"],
        "size": "M",
        "comments": "Test order"
      }
    ],
    "buyer_full_name": "Test User",
    "delivery_address": "123 Test St, Test City"
  }'
```

### Check Firestore Console

1. Go to [Firestore Console](https://console.cloud.google.com/firestore)
2. You should see an `orders` collection
3. Click on it to view the order document

## Firestore Data Structure

### Collections

The API uses the following Firestore structure:

```
orders/ (collection)
  ├── {order_id}/ (document)
      ├── order_id: string (UUID)
      ├── items: array
      │   └── [
      │       {
      │         item_id: string (UUID)
      │         main_colours: array of strings
      │         size: string
      │         comments: string | null
      │         created_at: timestamp
      │       }
      │     ]
      ├── buyer_full_name: string
      ├── delivery_address: string
      ├── payment_status: string
      ├── order_status: string
      ├── created_at: timestamp
      └── updated_at: timestamp
```

## Security Rules

To secure your Firestore database, set up security rules:

### Development Rules (Permissive)

```javascript
rules_version = '2';
service cloud.firestore {
  match /databases/{database}/documents {
    match /orders/{orderId} {
      // Allow read/write for development
      allow read, write: if true;
    }
  }
}
```

### Production Rules (Recommended)

```javascript
rules_version = '2';
service cloud.firestore {
  match /databases/{database}/documents {
    match /orders/{orderId} {
      // Allow anyone to create orders
      allow create: if true;
      
      // Allow reading own order (in production, add authentication)
      allow read: if true;
      
      // Only allow updates from authenticated admin
      // (In production, integrate with Firebase Auth or your auth system)
      allow update, delete: if false;
    }
  }
}
```

### Apply Security Rules

1. Create a file `firestore.rules` with your rules
2. Deploy them:

```bash
gcloud firestore rules deploy firestore.rules
```

Or use the [Firestore Console](https://console.cloud.google.com/firestore/rules).

## Monitoring and Management

### View Firestore Usage

```bash
# Get database statistics
gcloud firestore operations list

# Monitor usage in console
# Visit: https://console.cloud.google.com/firestore/usage
```

### Backup Firestore Data

```bash
# Create a backup
gcloud firestore export gs://YOUR_BACKUP_BUCKET/firestore-backup

# Restore from backup
gcloud firestore import gs://YOUR_BACKUP_BUCKET/firestore-backup
```

## Cost Management

Firestore pricing is based on:
- **Document reads/writes/deletes**
- **Storage** (per GB per month)
- **Network egress**

### Free Tier (as of 2024)
- 50,000 document reads/day
- 20,000 document writes/day
- 20,000 document deletes/day
- 1 GB storage

### Optimization Tips

1. **Batch operations** - Group multiple operations when possible
2. **Use indexes wisely** - Avoid unnecessary composite indexes
3. **Cache frequently accessed data** - Use Redis or in-memory cache
4. **Monitor usage** - Set up budget alerts in Google Cloud

### Set Up Budget Alerts

```bash
# Create a budget
gcloud billing budgets create \
  --billing-account=YOUR_BILLING_ACCOUNT \
  --display-name="Blumelein Monthly Budget" \
  --budget-amount=50 \
  --threshold-rule=percent=50 \
  --threshold-rule=percent=90 \
  --threshold-rule=percent=100
```

## Troubleshooting

### Error: "Could not load the default credentials"

**Solution**: Make sure `GOOGLE_APPLICATION_CREDENTIALS` points to a valid service account key file.

```bash
export GOOGLE_APPLICATION_CREDENTIALS="/path/to/service-account.json"
```

### Error: "Permission denied"

**Solution**: Grant the necessary IAM roles:

```bash
gcloud projects add-iam-policy-binding YOUR_PROJECT_ID \
  --member="serviceAccount:YOUR_SERVICE_ACCOUNT@YOUR_PROJECT_ID.iam.gserviceaccount.com" \
  --role="roles/datastore.user"
```

### Error: "Database not initialized"

**Solution**: Make sure the lifespan function is running properly. Check that:
1. Firestore API is enabled
2. Database is created
3. Service account has proper permissions

## Alternative: Using Firestore Emulator for Development

For local development without using the cloud:

### Install Emulator

```bash
# Install Firebase CLI
npm install -g firebase-tools

# Login to Firebase
firebase login

# Initialize Firebase in your project
firebase init emulators

# Start Firestore emulator
firebase emulators:start --only firestore
```

### Update `.env` for Emulator

```env
DATABASE_TYPE=firestore
GOOGLE_CLOUD_PROJECT=demo-test
FIRESTORE_EMULATOR_HOST=localhost:8080
```

### Update Code (if using emulator)

The Firestore client will automatically detect the `FIRESTORE_EMULATOR_HOST` environment variable and connect to the emulator instead of the production database.

## Next Steps

1. ✅ Firestore is set up
2. Set up Stripe for payments
3. Deploy to Cloud Run
4. Configure custom domain
5. Set up monitoring and alerts
6. Implement authentication for customers
7. Add backup automation

## Resources

- [Firestore Documentation](https://cloud.google.com/firestore/docs)
- [Firestore Pricing](https://cloud.google.com/firestore/pricing)
- [Security Rules Guide](https://firebase.google.com/docs/firestore/security/get-started)
- [Best Practices](https://cloud.google.com/firestore/docs/best-practices)

