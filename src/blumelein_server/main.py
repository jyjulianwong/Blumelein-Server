"""Main FastAPI application for Blumelein Server."""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from .config import settings
from .database import initialize_database, close_database
from .routers import orders_router, payments_router, manage_router

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan context manager for startup and shutdown events.
    """
    # Startup
    print("🌸 Blumelein Server starting up...")
    print(f"📍 Environment: {settings.environment}")
    print(f"🔑 Stripe configured: {'Yes' if settings.stripe_api_key else 'No'}")
    
    # Initialize database
    await initialize_database()
    
    yield
    
    # Shutdown
    print("🌸 Blumelein Server shutting down...")
    await close_database()


# Create FastAPI application
app = FastAPI(
    title="Blumelein Server API",
    description="REST API for a flower shop web application",
    version="0.1.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(orders_router)
app.include_router(payments_router)
app.include_router(manage_router)


@app.get(
    "/",
    tags=["health"],
    summary="Health check",
    description="Check if the API is running."
)
async def root():
    """Root endpoint for health checks."""
    return JSONResponse(
        content={
            "status": "healthy",
            "service": "Blumelein Server API",
            "version": "0.1.0",
        }
    )


@app.get(
    "/health",
    tags=["health"],
    summary="Detailed health check",
    description="Get detailed health information about the API."
)
async def health_check():
    """Detailed health check endpoint."""
    return JSONResponse(
        content={
            "status": "healthy",
            "environment": settings.environment,
            "database_type": settings.database_type,
            "stripe_configured": bool(settings.stripe_api_key),
        }
    )

