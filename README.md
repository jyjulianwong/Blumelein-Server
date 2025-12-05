# Blumelein Server API

REST API for a flower shop web application built with FastAPI. This API handles order submissions, payment processing via Stripe, and administrative order management.

## 🌸 Features

- **Order Management**: Submit and retrieve flower orders
- **Payment Processing**: Integrated Stripe payment system
- **Admin Dashboard**: Manage order statuses and view all orders
- **Modern API**: Built with FastAPI for high performance
- **Cloud Database**: Google Cloud Firestore for scalable data storage
- **Type Safety**: Full Pydantic validation for requests/responses
- **Portable**: All configuration via environment variables

## 📋 Prerequisites

- Python 3.11 or higher
- [uv](https://github.com/astral-sh/uv) - Fast Python package installer
- Google Cloud account with Firestore enabled (see [Firestore Setup Guide](FIRESTORE_SETUP.md))
- Stripe account (for payment processing)

## 🚀 Quick Start

### 1. Install UV

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

### 2. Clone and Setup

```bash
cd Blumelein-Server
```

### 3. Install Dependencies

```bash
uv sync
```

### 4. Configure Environment

Copy the example environment file and configure your settings:

```bash
cp .env.example .env
```

Edit `.env` with your configuration:

```env
# Database Configuration (required)
DATABASE_TYPE=firestore
GOOGLE_CLOUD_PROJECT=your-project-id
GOOGLE_CLOUD_LOCATION=us-central1

# Stripe Configuration (required)
STRIPE_API_KEY=sk_test_your_stripe_secret_key
STRIPE_PUBLISHABLE_KEY=pk_test_your_stripe_publishable_key
STRIPE_WEBHOOK_SECRET=whsec_your_webhook_secret

# Admin Configuration (required)
ADMIN_API_KEY=your-secure-admin-api-key

# Server Configuration (optional)
API_HOST=0.0.0.0
API_PORT=8000
ENVIRONMENT=development
```

**Important**: Before running the server, you need to set up Firestore and authenticate with Google Cloud. See the [Firestore Setup Guide](FIRESTORE_SETUP.md) for detailed instructions.

### 5. Run the Server

```bash
uv run uvicorn src.blumelein_server.main:app --reload --host 0.0.0.0 --port 8000
```

The API will be available at:
- **API**: http://localhost:8000
- **Interactive Docs**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## 🧪 Testing Stripe Webhooks Locally

For local development, you need to test Stripe webhooks. The recommended approach is using the Stripe CLI.

### Option 1: Stripe CLI (Recommended)

The Stripe CLI is the official tool for testing webhooks locally.

#### Installation

**macOS:**
```bash
brew install stripe/stripe-cli/stripe
```

**Linux/Windows:** Follow instructions at [stripe.com/docs/stripe-cli](https://stripe.com/docs/stripe-cli)

#### Setup & Testing

1. **Login to Stripe:**
   ```bash
   stripe login
   ```
   This opens a browser to authenticate with your Stripe account.

2. **Start Your Local API:**
   ```bash
   # Terminal 1: Start FastAPI server
   uv run uvicorn src.blumelein_server.main:app --reload --host 0.0.0.0 --port 8000
   ```

3. **Forward Webhooks to Local Server:**
   ```bash
   # Terminal 2: Forward Stripe webhooks to your local API
   stripe listen --forward-to localhost:8000/payments/webhook
   ```

4. **Copy Webhook Secret:**
   The `stripe listen` command outputs:
   ```
   > Ready! Your webhook signing secret is whsec_1234abcd... (^C to quit)
   ```
   Copy this secret and update your `.env` file:
   ```env
   STRIPE_WEBHOOK_SECRET=whsec_1234abcd...
   ```
   Restart your server to pick up the new secret.

5. **Test Webhook Events:**
   ```bash
   # Terminal 3: Trigger test webhook events
   stripe trigger payment_intent.succeeded
   stripe trigger payment_intent.payment_failed
   stripe trigger payment_intent.canceled
   ```

6. **Test Complete Payment Flow:**
   ```bash
   # Create a test payment intent
   curl -X POST http://localhost:8000/payments/create-payment-intent \
     -H "Content-Type: application/json" \
     -d '{
       "order_id": "your-order-id",
       "amount": 5000,
       "currency": "usd"
     }'
   
   # Use the client_secret from the response to complete payment on frontend
   # Or trigger a test webhook event
   stripe trigger payment_intent.succeeded
   ```

#### Benefits of Stripe CLI:
- ✅ **Official Stripe tool** - Always up-to-date
- ✅ **No external dependencies** - No need for ngrok accounts  
- ✅ **Easy testing** - Built-in event triggering
- ✅ **Real-time logs** - See webhook events as they happen
- ✅ **Automatic cleanup** - No manual webhook management

### Option 2: ngrok (Alternative)

If you prefer using ngrok for exposing your local server:

1. **Install ngrok:**
   ```bash
   brew install ngrok
   ```

2. **Start Your API:**
   ```bash
   uv run uvicorn src.blumelein_server.main:app --reload --host 0.0.0.0 --port 8000
   ```

3. **Expose Local Server:**
   ```bash
   # In another terminal
   ngrok http 8000
   ```

4. **Configure Stripe Dashboard:**
   - Copy the ngrok URL (e.g., `https://abc123.ngrok.io`)
   - Go to [Stripe Dashboard > Webhooks](https://dashboard.stripe.com/webhooks)
   - Add endpoint: `https://abc123.ngrok.io/payments/webhook`
   - Select events: `payment_intent.succeeded`, `payment_intent.payment_failed`, `payment_intent.canceled`
   - Copy the webhook signing secret to your `.env` file
   - Restart your server

### Stripe Test Cards

Use these test card numbers for different scenarios:

| Card Number | Scenario |
|-------------|----------|
| `4242 4242 4242 4242` | Successful payment |
| `4000 0000 0000 0002` | Declined payment |
| `4000 0025 0000 3155` | Requires 3D Secure authentication |
| `4000 0000 0000 9995` | Insufficient funds |

For any test card, use:
- **Expiry**: Any future date (e.g., `12/34`)
- **CVC**: Any 3 digits (e.g., `123`)
- **ZIP**: Any 5 digits (e.g., `12345`)

## 📚 API Endpoints

### Orders (`/orders`)

#### Submit an Order
```http
POST /orders
Content-Type: application/json

{
  "items": [
    {
      "main_colours": ["red", "pink"],
      "size": "M",
      "comments": "Please include roses"
    }
  ],
  "buyer_full_name": "Jane Smith",
  "delivery_address": "123 Main St, New York, NY 10001"
}
```

#### Get Order by ID
```http
GET /orders/{order_id}
```

### Payments (`/payments`)

#### Create Payment Intent
```http
POST /payments/create-payment-intent
Content-Type: application/json

{
  "order_id": "550e8400-e29b-41d4-a716-446655440000",
  "amount": 5000,
  "currency": "usd"
}
```

#### Stripe Webhook
```http
POST /payments/webhook
stripe-signature: {signature}
```

### Management (`/manage`) - Admin Only

All management endpoints require an API key in the `X-API-Key` header.

#### List All Orders
```http
GET /manage/orders
X-API-Key: your-admin-api-key
```

#### Update Order Status
```http
PATCH /manage/orders/{order_id}/status
X-API-Key: your-admin-api-key
Content-Type: application/json

{
  "order_status": "In Progress"
}
```

#### Get Order Details
```http
GET /manage/orders/{order_id}
X-API-Key: your-admin-api-key
```

## 🏗️ Project Structure

```
Blumelein-Server/
├── src/
│   └── blumelein_server/
│       ├── __init__.py
│       ├── main.py              # FastAPI application
│       ├── config.py            # Configuration management
│       ├── database/
│       │   ├── __init__.py
│       │   ├── adapter.py       # Database adapter interface
│       │   ├── firestore_adapter.py  # Firestore implementation
│       │   └── factory.py       # Database factory
│       ├── models/
│       │   ├── __init__.py
│       │   └── schemas.py       # Pydantic models
│       └── routers/
│           ├── __init__.py
│           ├── orders.py        # Order endpoints
│           ├── payments.py      # Payment endpoints
│           └── manage.py        # Admin endpoints
├── pyproject.toml              # Project dependencies
├── .env.example                # Example environment variables
├── Dockerfile                  # Docker configuration
├── FIRESTORE_SETUP.md          # Firestore setup guide
├── DEPLOYMENT.md               # Deployment guide
├── .gitignore
└── README.md
```

## 🗄️ Data Models

### Order
- `order_id`: Unique UUID
- `items`: List of items
- `buyer_full_name`: Customer name
- `delivery_address`: Delivery address
- `payment_status`: "Completed" or "Incomplete"
- `order_status`: "Not Started", "In Progress", or "Completed"
- `created_at`, `updated_at`: Timestamps

### Item
- `item_id`: Unique UUID
- `main_colours`: List of colors
- `size`: "S", "M", or "L"
- `comments`: Optional user comments
- `created_at`: Timestamp

## 🔒 Security

- **Admin Endpoints**: Protected by API key authentication
- **CORS**: Configurable allowed origins
- **Stripe Webhooks**: Signature verification enabled
- **Input Validation**: Full Pydantic validation on all inputs

## 🧪 Testing

You can test the API using:

1. **Interactive Docs**: Navigate to http://localhost:8000/docs
2. **cURL**:
   ```bash
   curl -X POST http://localhost:8000/orders \
     -H "Content-Type: application/json" \
     -d '{
       "items": [{"main_colours": ["red"], "size": "M"}],
       "buyer_full_name": "Test User",
       "delivery_address": "123 Test St"
     }'
   ```
3. **HTTPie**:
   ```bash
   http POST localhost:8000/orders \
     items:='[{"main_colours": ["red"], "size": "M"}]' \
     buyer_full_name="Test User" \
     delivery_address="123 Test St"
   ```

## 🌐 Deployment to Google Cloud

### Automated Deployment with Terraform & GitHub Actions

The project includes automated deployment infrastructure with **semantic versioning**:

- **Push to main with conventional commits** → Automatically versions, builds, and deploys to Cloud Run
- **Semantic versioning** automatically determines version bumps based on commit messages
- **Terraform** manages all infrastructure as code
- **GitHub Actions** handles CI/CD pipeline

**Quick Deploy**:
1. Configure GitHub Secrets (see [Terraform Deployment Guide](TERRAFORM_DEPLOYMENT.md))
2. Commit changes using [Conventional Commits](https://www.conventionalcommits.org/) format
3. Push to main branch
4. Automatic versioning and deployment! 🎉

For detailed semantic versioning instructions, see:
- **[Versioning Guide](VERSIONING.md)** - How to use semantic versioning with conventional commits
- **[Terraform Deployment Guide](TERRAFORM_DEPLOYMENT.md)** - Complete setup walkthrough
- **[Deployment Guide](DEPLOYMENT.md)** - Manual deployment options

### Manual Deployment

If you prefer manual deployment:

```bash
# Build and push Docker image
gcloud builds submit --tag gcr.io/[PROJECT-ID]/blumelein-server

# Deploy to Cloud Run
gcloud run deploy blumelein-server \
  --image gcr.io/[PROJECT-ID]/blumelein-server \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated
```

## 📝 Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `DATABASE_TYPE` | Yes | Database type (currently only "firestore") |
| `GOOGLE_CLOUD_PROJECT` | Yes | Google Cloud project ID |
| `GOOGLE_CLOUD_LOCATION` | No | Firestore location (default: us-central1) |
| `STRIPE_API_KEY` | Yes | Stripe secret API key |
| `STRIPE_PUBLISHABLE_KEY` | Yes | Stripe publishable key |
| `STRIPE_WEBHOOK_SECRET` | Yes | Stripe webhook signing secret |
| `ADMIN_API_KEY` | Yes | Admin API key for management endpoints |
| `API_HOST` | No | Server host (default: 0.0.0.0) |
| `API_PORT` | No | Server port (default: 8000) |
| `ENVIRONMENT` | No | Environment name (default: development) |
| `ALLOWED_ORIGINS` | No | CORS origins (default: http://localhost:3000) |

**Note**: For local development, authenticate with Google Cloud using `gcloud auth application-default login`. On Cloud Run, authentication is automatic.

## 🔄 Database

The API uses **Google Cloud Firestore** for data persistence. Firestore provides:

- **Scalability**: Automatically scales with your application
- **Real-time updates**: Support for real-time listeners (future feature)
- **Serverless**: No infrastructure management required
- **Global distribution**: Multi-region support for low latency
- **ACID transactions**: Ensures data consistency

### Database Architecture

The codebase uses a **database adapter pattern** for flexibility:

- **`DatabaseAdapter`**: Abstract interface defining all database operations
- **`FirestoreAdapter`**: Firestore implementation of the interface
- **`get_database_adapter()`**: Factory function to get the current adapter

This design makes it easy to:
- Switch database backends in the future
- Mock the database for testing
- Support multiple database types

### Setup

See [FIRESTORE_SETUP.md](FIRESTORE_SETUP.md) for complete setup instructions.

## 🛠️ Development

### Run with Auto-reload
```bash
uv run uvicorn src.blumelein_server.main:app --reload
```

### Format Code
```bash
uv run ruff format src/
```

### Type Checking
```bash
uv run mypy src/
```

## 📄 License

MIT

## 🤝 Contributing

Contributions welcome! Please feel free to submit a Pull Request.

## 📧 Support

For issues and questions, please open an issue on the repository.

