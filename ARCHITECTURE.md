# Blumelein Server Architecture

This document describes the architecture and design decisions of the Blumelein Server API.

## Overview

The Blumelein Server is a REST API built with FastAPI for managing a flower shop's orders, payments, and administrative tasks. It uses Google Cloud Firestore for data persistence and Stripe for payment processing.

## Architecture Principles

1. **Separation of Concerns**: Clear separation between routers, models, database, and configuration
2. **Dependency Injection**: Using FastAPI's dependency system for authentication and database access
3. **Type Safety**: Full type hints and Pydantic validation throughout
4. **Adapter Pattern**: Database operations abstracted behind an interface for flexibility
5. **Configuration Management**: All environment-specific settings centralized in `config.py`

## Directory Structure

```
src/blumelein_server/
├── __init__.py              # Package initialization
├── main.py                  # FastAPI application and lifespan management
├── config.py                # Environment configuration with Pydantic Settings
├── database/                # Database layer
│   ├── __init__.py         # Database exports
│   ├── adapter.py          # Abstract database interface
│   ├── firestore_adapter.py # Firestore implementation
│   └── factory.py          # Database factory and global instance
├── models/                  # Data models
│   ├── __init__.py         # Model exports
│   └── schemas.py          # Pydantic schemas for validation
└── routers/                 # API endpoints
    ├── __init__.py         # Router exports
    ├── orders.py           # Order management endpoints
    ├── payments.py         # Payment processing endpoints
    └── manage.py           # Admin management endpoints
```

## Design Patterns

### 1. Database Adapter Pattern

**Purpose**: Decouple the application from the specific database implementation.

**Components**:

- **`DatabaseAdapter`** (abstract): Defines the interface for all database operations
- **`FirestoreAdapter`** (concrete): Implements the interface for Google Cloud Firestore
- **`get_database_adapter()`**: Returns the global database instance

**Benefits**:
- Easy to switch database backends (e.g., PostgreSQL, MongoDB)
- Simplifies testing with mock implementations
- Clear contract for database operations

**Example**:

```python
from ..database import get_database_adapter

async def submit_order(order_data: OrderCreate):
    db = get_database_adapter()
    order = Order(...)
    created_order = await db.create_order(order)
    return created_order
```

### 2. Repository Pattern

The database adapters act as repositories, encapsulating all data access logic:

- `create_order()` - Create a new order
- `get_order()` - Retrieve an order by ID
- `get_all_orders()` - Retrieve all orders
- `update_order_payment_status()` - Update payment status
- `update_order_status()` - Update order processing status

### 3. Factory Pattern

The `factory.py` module provides factory functions for creating and managing the database adapter:

```python
async def initialize_database() -> DatabaseAdapter:
    """Create and initialize the configured database adapter."""
    
def get_database_adapter() -> DatabaseAdapter:
    """Get the global database adapter instance."""
    
async def close_database() -> None:
    """Close and cleanup the database connection."""
```

### 4. Dependency Injection

FastAPI's dependency system is used for:

**Authentication**: Admin endpoints require API key validation

```python
async def verify_admin_key(api_key: str = Security(api_key_header)) -> str:
    """Verify admin API key."""
    if api_key != settings.admin_api_key:
        raise HTTPException(status_code=403, detail="Invalid API key")
    return api_key

@router.get("/orders", dependencies=[Depends(verify_admin_key)])
async def list_all_orders():
    """Admin-only endpoint."""
```

## Data Flow

### Order Submission Flow

```
1. Client sends POST /orders with order data
2. FastAPI validates request with OrderCreate schema
3. Router creates Order object with items
4. Router calls db.create_order()
5. FirestoreAdapter converts Order to dict
6. Firestore stores document in 'orders' collection
7. FirestoreAdapter returns Order object
8. Router returns OrderResponse to client
```

### Payment Processing Flow

```
1. Client sends POST /payments/create-payment-intent
2. Router verifies order exists via db.get_order()
3. Router checks payment status
4. Router creates Stripe PaymentIntent with order_id in metadata
5. Router returns client_secret to frontend
6. Frontend completes payment with Stripe
7. Stripe sends webhook to /payments/webhook
8. Router verifies webhook signature
9. Router updates order payment status via db.update_order_payment_status()
10. Firestore updates document with new payment status
```

### Admin Management Flow

```
1. Admin sends PATCH /manage/orders/{id}/status with X-API-Key header
2. FastAPI validates API key via verify_admin_key dependency
3. Router retrieves order via db.get_order()
4. Router updates status via db.update_order_status()
5. Firestore updates document
6. Router returns updated order
```

## Database Schema

### Firestore Collections

#### `orders` Collection

Each document represents a single order:

```javascript
{
  order_id: "uuid-string",
  items: [
    {
      item_id: "uuid-string",
      main_colours: ["red", "pink"],
      size: "M",
      comments: "Please include roses",
      created_at: Timestamp
    }
  ],
  buyer_full_name: "Jane Smith",
  buyer_email: "jane.smith@example.com",
  buyer_phone: "+1-555-0123",
  delivery_address: "123 Main St, New York, NY 10001",
  payment_status: "Incomplete" | "Completed",
  order_status: "Not Started" | "In Progress" | "Completed",
  created_at: Timestamp,
  updated_at: Timestamp
}
```

**Document ID**: `order_id` (UUID string)

**Indexes**: Firestore automatically indexes all fields. Consider adding composite indexes if querying by multiple fields.

## API Security

### Admin Authentication

- **Method**: API Key in `X-API-Key` header
- **Validation**: Compared against `ADMIN_API_KEY` environment variable
- **Endpoints**: All `/manage/*` endpoints require authentication

### Stripe Webhook Security

- **Method**: Signature verification using `stripe-signature` header
- **Secret**: `STRIPE_WEBHOOK_SECRET` from environment
- **Validation**: Stripe SDK verifies the webhook came from Stripe

### CORS

- **Configured**: In `main.py` via CORSMiddleware
- **Origins**: Specified in `ALLOWED_ORIGINS` environment variable
- **Development**: Typically `http://localhost:3000`
- **Production**: Your frontend domain(s)

## Error Handling

### HTTP Exceptions

The API uses FastAPI's `HTTPException` for all error responses:

```python
raise HTTPException(
    status_code=status.HTTP_404_NOT_FOUND,
    detail=f"Order with ID {order_id} not found"
)
```

### Common Status Codes

- **200 OK**: Successful GET, PATCH
- **201 Created**: Successful POST (order, payment intent)
- **400 Bad Request**: Invalid input, Stripe errors
- **403 Forbidden**: Invalid API key
- **404 Not Found**: Order not found
- **500 Internal Server Error**: Unexpected errors

## Configuration Management

### Environment Variables

All configuration is loaded via `pydantic-settings`:

```python
class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )
    
    # Configuration fields...
```

**Benefits**:
- Type validation
- Default values
- IDE autocomplete
- Centralized configuration

### Configuration Hierarchy

1. Environment variables (highest priority)
2. `.env` file
3. Default values in `Settings` class

## Lifespan Management

The application uses FastAPI's lifespan context manager:

```python
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    await initialize_database()
    
    yield
    
    # Shutdown
    await close_database()
```

**Startup**:
1. Initialize Firestore client
2. Verify connection

**Shutdown**:
1. Close Firestore client
2. Cleanup resources

## Testing Strategy

### Unit Tests

Test individual components in isolation:

```python
# Test database adapter with mocks
async def test_create_order():
    mock_db = MockDatabaseAdapter()
    order = Order(...)
    created = await mock_db.create_order(order)
    assert created.order_id == order.order_id
```

### Integration Tests

Test API endpoints with test client:

```python
from fastapi.testclient import TestClient

def test_submit_order():
    client = TestClient(app)
    response = client.post("/orders", json={...})
    assert response.status_code == 201
```

### Testing with Firestore Emulator

Use the Firestore emulator for local testing without cloud costs:

```bash
# Set environment variable
export FIRESTORE_EMULATOR_HOST=localhost:8080

# Run tests
pytest
```

## Scalability Considerations

### Horizontal Scaling

- **Stateless Design**: No in-memory state between requests
- **Cloud Run**: Automatically scales based on traffic
- **Connection Pooling**: Firestore client handles connection management

### Database Performance

- **Firestore**: Scales automatically with load
- **Indexes**: Create composite indexes for complex queries
- **Caching**: Consider Redis for frequently accessed data

### Cost Optimization

- **Cloud Run**: Scales to zero when idle
- **Firestore**: Free tier covers 50k reads, 20k writes per day
- **Batching**: Group multiple Firestore operations when possible

## Future Enhancements

### Potential Features

1. **User Authentication**: Add customer login with Firebase Auth or OAuth
2. **Real-time Updates**: Use Firestore listeners for live order status
3. **Email Notifications**: Send order confirmations via SendGrid/Mailgun
4. **Image Uploads**: Store bouquet images in Cloud Storage
5. **Analytics**: Track orders, revenue with Google Analytics
6. **Rate Limiting**: Implement rate limiting middleware
7. **Caching**: Add Redis for frequently accessed orders
8. **Search**: Implement full-text search with Algolia or Elasticsearch
9. **Internationalization**: Support multiple languages and currencies
10. **Inventory Management**: Track flower stock levels

### Database Alternatives

The adapter pattern makes it easy to add alternative backends:

```python
class PostgreSQLAdapter(DatabaseAdapter):
    """PostgreSQL implementation using asyncpg."""
    
class MongoDBAdapter(DatabaseAdapter):
    """MongoDB implementation using motor."""
```

## Deployment

### Google Cloud Run

The application is designed for Cloud Run deployment:

- **Dockerfile**: Multi-stage build for optimization
- **Environment**: All config via environment variables
- **Scaling**: Configurable min/max instances
- **Health Checks**: `/health` endpoint for monitoring

See [DEPLOYMENT.md](DEPLOYMENT.md) for detailed deployment instructions.

## Monitoring and Observability

### Logging

- **Startup/Shutdown**: Logs initialization events
- **Errors**: Logs warnings for webhook processing failures
- **Cloud Logging**: Automatic integration on Cloud Run

### Metrics

- **Cloud Run**: Provides request count, latency, error rate
- **Stripe Dashboard**: Payment metrics and webhooks
- **Firestore Console**: Read/write metrics and costs

### Health Checks

- **`GET /`**: Basic health check
- **`GET /health`**: Detailed status including database type

## References

- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [Pydantic Documentation](https://docs.pydantic.dev/)
- [Firestore Documentation](https://cloud.google.com/firestore/docs)
- [Stripe API Documentation](https://stripe.com/docs/api)
- [Google Cloud Run Documentation](https://cloud.google.com/run/docs)

