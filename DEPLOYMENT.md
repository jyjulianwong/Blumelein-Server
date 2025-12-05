# Deployment Guide for Google Cloud

This guide walks you through deploying the Blumelein Server API to Google Cloud Platform.

## Prerequisites

1. Google Cloud CLI (`gcloud`) installed and configured
2. Docker installed (for local testing)
3. Active Google Cloud project
4. Billing enabled on your project

## Option 1: Deploy to Cloud Run (Recommended)

Cloud Run is a fully managed serverless platform that automatically scales your application.

### Step 1: Authenticate with Google Cloud

```bash
gcloud auth login
gcloud config set project YOUR_PROJECT_ID
```

### Step 2: Enable Required APIs

```bash
gcloud services enable run.googleapis.com
gcloud services enable cloudbuild.googleapis.com
```

### Step 3: Build and Deploy

```bash
# Build the container image using Cloud Build
gcloud builds submit --tag gcr.io/YOUR_PROJECT_ID/blumelein-server

# Deploy to Cloud Run
gcloud run deploy blumelein-server \
  --image gcr.io/YOUR_PROJECT_ID/blumelein-server \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated \
  --port 8000 \
  --memory 512Mi \
  --timeout 300
```

### Step 4: Configure Environment Variables

```bash
gcloud run services update blumelein-server \
  --region us-central1 \
  --set-env-vars="
STRIPE_API_KEY=sk_live_your_key,
STRIPE_PUBLISHABLE_KEY=pk_live_your_key,
STRIPE_WEBHOOK_SECRET=whsec_your_secret,
ADMIN_API_KEY=your_secure_admin_key,
ENVIRONMENT=production,
ALLOWED_ORIGINS=https://your-frontend-domain.com
"
```

### Step 5: Get Your Service URL

```bash
gcloud run services describe blumelein-server \
  --region us-central1 \
  --format 'value(status.url)'
```

### Step 6: Configure Stripe Webhook

1. Go to your Stripe Dashboard
2. Navigate to Developers → Webhooks
3. Click "Add endpoint"
4. Enter your Cloud Run URL + `/payments/webhook`
5. Select events to listen for: `payment_intent.succeeded`
6. Copy the signing secret and update your environment variables

## Option 2: Deploy to App Engine

App Engine provides a fully managed platform with automatic scaling.

### Step 1: Create `app.yaml`

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

### Step 2: Deploy

```bash
gcloud app deploy
```

## Option 3: Deploy to GKE (Google Kubernetes Engine)

For advanced users who need fine-grained control.

### Step 1: Create a GKE Cluster

```bash
gcloud container clusters create blumelein-cluster \
  --num-nodes=2 \
  --machine-type=e2-small \
  --region=us-central1
```

### Step 2: Build and Push Image

```bash
gcloud builds submit --tag gcr.io/YOUR_PROJECT_ID/blumelein-server
```

### Step 3: Create Kubernetes Deployment

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

### Step 4: Deploy to GKE

```bash
kubectl apply -f k8s-deployment.yaml
```

## Security Best Practices

### 1. Use Secret Manager

Instead of environment variables, use Google Cloud Secret Manager:

```bash
# Create secrets
echo -n "sk_live_your_key" | gcloud secrets create stripe-api-key --data-file=-

# Grant Cloud Run access to secrets
gcloud run services update blumelein-server \
  --update-secrets=STRIPE_API_KEY=stripe-api-key:latest
```

### 2. Enable HTTPS

Cloud Run automatically provides HTTPS. For custom domains:

```bash
gcloud run domain-mappings create \
  --service blumelein-server \
  --domain api.yourdomain.com \
  --region us-central1
```

### 3. Configure CORS Properly

Update `ALLOWED_ORIGINS` to include only your frontend domain:

```bash
ALLOWED_ORIGINS=https://yourdomain.com,https://www.yourdomain.com
```

### 4. Implement Rate Limiting

Consider adding rate limiting middleware or using Google Cloud Armor.

## Monitoring and Logging

### View Logs

```bash
# Cloud Run
gcloud logging read "resource.type=cloud_run_revision AND resource.labels.service_name=blumelein-server" --limit 50

# Real-time logs
gcloud run services logs tail blumelein-server --region us-central1
```

### Set Up Alerts

1. Go to Cloud Console → Monitoring
2. Create alerting policy for:
   - High error rate
   - High latency
   - Low availability

## Scaling Configuration

### Cloud Run Auto-scaling

```bash
gcloud run services update blumelein-server \
  --region us-central1 \
  --min-instances 1 \
  --max-instances 100 \
  --concurrency 80
```

## Backup and Disaster Recovery

Since the current implementation uses in-memory storage, consider:

1. **Migrate to Cloud SQL or Firestore**
2. **Set up automated backups**
3. **Implement multi-region deployment**

## Cost Optimization

1. Use Cloud Run for automatic scaling to zero
2. Set appropriate memory limits (512Mi is usually sufficient)
3. Configure min instances to 0 for development environments
4. Use preemptible VMs for GKE clusters in non-production

## CI/CD Pipeline

### Using GitHub Actions

Create `.github/workflows/deploy.yml`:

```yaml
name: Deploy to Cloud Run

on:
  push:
    branches: [ main ]

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      
      - name: Setup Cloud SDK
        uses: google-github-actions/setup-gcloud@v0
        with:
          project_id: ${{ secrets.GCP_PROJECT_ID }}
          service_account_key: ${{ secrets.GCP_SA_KEY }}
      
      - name: Build and Deploy
        run: |
          gcloud builds submit --tag gcr.io/${{ secrets.GCP_PROJECT_ID }}/blumelein-server
          gcloud run deploy blumelein-server \
            --image gcr.io/${{ secrets.GCP_PROJECT_ID }}/blumelein-server \
            --region us-central1 \
            --platform managed
```

## Troubleshooting

### Check Service Status

```bash
gcloud run services describe blumelein-server --region us-central1
```

### Test Endpoints

```bash
SERVICE_URL=$(gcloud run services describe blumelein-server --region us-central1 --format 'value(status.url)')
curl $SERVICE_URL/health
```

### Common Issues

1. **503 Service Unavailable**: Check container logs for startup errors
2. **Memory errors**: Increase memory allocation
3. **Timeout errors**: Increase timeout limit or optimize code

## Support

For issues related to:
- **Application**: Check application logs
- **Google Cloud**: Consult Google Cloud documentation
- **Stripe**: Contact Stripe support

## Next Steps

1. Set up monitoring and alerting
2. Configure custom domain
3. Implement database persistence
4. Add automated testing in CI/CD
5. Set up staging environment

