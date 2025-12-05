"""Management router for admin operations."""

from uuid import UUID

from fastapi import APIRouter, HTTPException, status, Security, Depends
from fastapi.security import APIKeyHeader

from ..config import settings
from ..models import OrderResponse, OrderStatusUpdate, OrderStatus
from ..database import get_database_adapter

router = APIRouter(
    prefix="/manage",
    tags=["management"],
)

# API Key security
api_key_header = APIKeyHeader(name="X-API-Key", auto_error=True)


async def verify_admin_key(api_key: str = Security(api_key_header)) -> str:
    """
    Verify the admin API key.
    
    All management endpoints require a valid admin API key in the X-API-Key header.
    """
    if api_key != settings.admin_api_key:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid API key"
        )
    return api_key


@router.get(
    "/orders",
    response_model=list[OrderResponse],
    summary="List all orders",
    description="Retrieve all submitted orders (admin only).",
    dependencies=[Depends(verify_admin_key)],
)
async def list_all_orders() -> list[OrderResponse]:
    """
    List all orders submitted by users.
    
    This endpoint is restricted to administrators and requires a valid API key.
    Returns all orders with complete information including items, buyer details,
    payment status, and order status.
    """
    db = get_database_adapter()
    orders = await db.get_all_orders()
    return [OrderResponse(**order.model_dump()) for order in orders]


@router.patch(
    "/orders/{order_id}/status",
    response_model=OrderResponse,
    summary="Update order status",
    description="Mark an order as 'Not Started', 'In Progress', or 'Completed' (admin only).",
    dependencies=[Depends(verify_admin_key)],
)
async def update_order_processing_status(
    order_id: UUID,
    status_update: OrderStatusUpdate
) -> OrderResponse:
    """
    Update the processing status of an order.
    
    Administrators can mark orders with the following statuses:
    - Not Started: Order has been received but not yet processed
    - In Progress: Order is currently being prepared
    - Completed: Order has been fulfilled and delivered
    
    This endpoint is restricted to administrators and requires a valid API key.
    """
    # Verify order exists
    db = get_database_adapter()
    order = await db.get_order(order_id)
    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Order with ID {order_id} not found"
        )
    
    # Update order status
    updated_order = await db.update_order_status(order_id, status_update.order_status)
    
    if not updated_order:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update order status"
        )
    
    return OrderResponse(**updated_order.model_dump())


@router.get(
    "/orders/{order_id}",
    response_model=OrderResponse,
    summary="Get order details",
    description="Retrieve detailed information about a specific order (admin only).",
    dependencies=[Depends(verify_admin_key)],
)
async def get_order_details(order_id: UUID) -> OrderResponse:
    """
    Retrieve complete information about an order (admin view).
    
    This endpoint provides the same information as the public order endpoint
    but is restricted to administrators.
    """
    db = get_database_adapter()
    order = await db.get_order(order_id)
    
    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Order with ID {order_id} not found"
        )
    
    return OrderResponse(**order.model_dump())

