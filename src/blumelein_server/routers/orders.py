"""Orders router for submitting and retrieving orders."""

from uuid import UUID

from fastapi import APIRouter, HTTPException, status

from ..models import (
    OrderCreate,
    OrderResponse,
    Order,
    Item,
)
from ..database import get_database_adapter

router = APIRouter(
    prefix="/orders",
    tags=["orders"],
)


@router.post(
    "",
    response_model=OrderResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Submit a new order",
    description="Create a new order with one or more items for the flower shop.",
)
async def submit_order(order_data: OrderCreate) -> OrderResponse:
    """
    Submit a new order to the backend.
    
    The order must contain at least one item. Each item specifies:
    - Main colours for the bouquet
    - Size (S/M/L)
    - Optional comments
    
    Returns the created order with a unique order ID.
    """
    # Convert ItemCreate to Item with generated IDs
    items = [Item(**item.model_dump()) for item in order_data.items]
    
    # Create order object
    order = Order(
        items=items,
        buyer_full_name=order_data.buyer_full_name,
        delivery_address=order_data.delivery_address,
    )
    
    # Store order in database
    db = get_database_adapter()
    created_order = await db.create_order(order)
    
    return OrderResponse(**created_order.model_dump())


@router.get(
    "/{order_id}",
    response_model=OrderResponse,
    summary="Get order by ID",
    description="Retrieve all information about a specific order using its Order ID.",
)
async def get_order_by_id(order_id: UUID) -> OrderResponse:
    """
    Retrieve complete information about an order.
    
    Returns order details including:
    - All items in the order
    - Buyer information and delivery address
    - Payment status
    - Order processing status
    - Creation and update timestamps
    """
    db = get_database_adapter()
    order = await db.get_order(order_id)
    
    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Order with ID {order_id} not found"
        )
    
    return OrderResponse(**order.model_dump())

