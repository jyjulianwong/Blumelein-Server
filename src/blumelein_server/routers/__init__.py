"""API routers for the Blumelein Server."""

from .orders import router as orders_router
from .payments import router as payments_router
from .manage import router as manage_router

__all__ = ["orders_router", "payments_router", "manage_router"]

