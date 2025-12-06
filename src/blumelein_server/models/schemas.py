"""Pydantic models for request/response validation."""

from datetime import datetime
from enum import Enum
from typing import Optional
from uuid import UUID, uuid4

from pydantic import BaseModel, Field, ConfigDict


class BouquetSize(str, Enum):
    """Size options for bouquets."""
    SMALL = "S"
    MEDIUM = "M"
    LARGE = "L"


class PaymentStatus(str, Enum):
    """Payment status for orders."""
    INCOMPLETE = "Incomplete"
    COMPLETED = "Completed"


class OrderStatus(str, Enum):
    """Order processing status for admin management."""
    NOT_STARTED = "Not Started"
    IN_PROGRESS = "In Progress"
    COMPLETED = "Completed"


# Item Schemas
class ItemCreate(BaseModel):
    """Schema for creating a new item in an order."""
    main_colours: list[str] = Field(
        ...,
        min_length=1,
        description="List of main colours the bouquet should consist of",
        examples=[["red", "pink", "white"]]
    )
    size: BouquetSize = Field(
        ...,
        description="Size of the bouquet (S/M/L)"
    )
    comments: Optional[str] = Field(
        None,
        max_length=500,
        description="Additional user-supplied comments about requests for this item"
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "main_colours": ["red", "pink"],
                "size": "M",
                "comments": "Please include roses and lilies"
            }
        }
    )


class Item(ItemCreate):
    """Schema for an item with ID."""
    item_id: UUID = Field(default_factory=uuid4, description="Unique item identifier")
    created_at: datetime = Field(default_factory=datetime.utcnow)

    model_config = ConfigDict(from_attributes=True)


# Order Schemas
class OrderCreate(BaseModel):
    """Schema for creating a new order."""
    items: list[ItemCreate] = Field(
        ...,
        min_length=1,
        description="List of items in the order"
    )
    buyer_full_name: str = Field(
        ...,
        min_length=1,
        max_length=100,
        description="Full name of the buyer"
    )
    buyer_email: str = Field(
        ...,
        min_length=3,
        max_length=254,
        description="Email address of the buyer"
    )
    buyer_phone: str = Field(
        ...,
        min_length=1,
        max_length=20,
        description="Phone number of the buyer"
    )
    delivery_address: str = Field(
        ...,
        min_length=1,
        max_length=300,
        description="Delivery address for the order"
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "items": [
                    {
                        "main_colours": ["red", "pink"],
                        "size": "M",
                        "comments": "Please include roses"
                    }
                ],
                "buyer_full_name": "Jane Smith",
                "buyer_email": "jane.smith@example.com",
                "buyer_phone": "+1-555-0123",
                "delivery_address": "123 Main St, New York, NY 10001"
            }
        }
    )


class Order(BaseModel):
    """Schema for a complete order."""
    order_id: UUID = Field(default_factory=uuid4, description="Unique order identifier")
    items: list[Item] = Field(..., description="List of items in the order")
    buyer_full_name: str = Field(..., description="Full name of the buyer")
    buyer_email: str = Field(..., description="Email address of the buyer")
    buyer_phone: str = Field(..., description="Phone number of the buyer")
    delivery_address: str = Field(..., description="Delivery address for the order")
    payment_status: PaymentStatus = Field(
        default=PaymentStatus.INCOMPLETE,
        description="Payment status of the order"
    )
    order_status: OrderStatus = Field(
        default=OrderStatus.NOT_STARTED,
        description="Processing status of the order"
    )
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    model_config = ConfigDict(from_attributes=True)


class OrderResponse(BaseModel):
    """Response schema for order operations."""
    order_id: UUID
    items: list[Item]
    buyer_full_name: str
    buyer_email: str
    buyer_phone: str
    delivery_address: str
    payment_status: PaymentStatus
    order_status: OrderStatus
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


# Payment Schemas
class PaymentIntent(BaseModel):
    """Schema for creating a payment intent."""
    order_id: UUID = Field(..., description="Order ID to associate with the payment")
    amount: int = Field(
        ...,
        gt=0,
        description="Payment amount in cents (e.g., 1000 = $10.00)"
    )
    currency: str = Field(
        default="usd",
        description="Three-letter ISO currency code"
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "order_id": "550e8400-e29b-41d4-a716-446655440000",
                "amount": 5000,
                "currency": "usd"
            }
        }
    )


class PaymentIntentResponse(BaseModel):
    """Response schema for payment intent creation."""
    client_secret: str = Field(..., description="Client secret for completing payment")
    payment_intent_id: str = Field(..., description="Stripe payment intent ID")
    amount: int = Field(..., description="Payment amount in cents")
    currency: str = Field(..., description="Three-letter ISO currency code")

    model_config = ConfigDict(from_attributes=True)


# Admin Schemas
class OrderStatusUpdate(BaseModel):
    """Schema for updating order status."""
    order_status: OrderStatus = Field(..., description="New status for the order")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "order_status": "In Progress"
            }
        }
    )

