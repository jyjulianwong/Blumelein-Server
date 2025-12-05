"""Payments router for handling Stripe payments."""

from uuid import UUID

import stripe
from fastapi import APIRouter, HTTPException, status, Header, Request
from fastapi.responses import JSONResponse

from ..config import settings
from ..models import PaymentIntent, PaymentIntentResponse, PaymentStatus
from ..database import get_database_adapter

# Configure Stripe
stripe.api_key = settings.stripe_api_key

router = APIRouter(
    prefix="/payments",
    tags=["payments"],
)


@router.post(
    "/create-payment-intent",
    response_model=PaymentIntentResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a Stripe payment intent",
    description="Create a payment intent for an order using Stripe.",
)
async def create_payment_intent(payment_data: PaymentIntent) -> PaymentIntentResponse:
    """
    Create a Stripe payment intent for processing payment.
    
    This endpoint should be called when a user is ready to pay for their order.
    The client_secret returned should be used on the frontend to complete the payment.
    
    Args:
        payment_data: Payment information including order_id, amount, and currency
    
    Returns:
        Payment intent details including client_secret for frontend processing
    """
    # Verify order exists
    db = get_database_adapter()
    order = await db.get_order(payment_data.order_id)
    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Order with ID {payment_data.order_id} not found"
        )
    
    # Check if order is already paid
    if order.payment_status == PaymentStatus.COMPLETED:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Order has already been paid"
        )
    
    try:
        # Create Stripe payment intent
        intent = stripe.PaymentIntent.create(
            amount=payment_data.amount,
            currency=payment_data.currency,
            metadata={
                "order_id": str(payment_data.order_id),
            },
            automatic_payment_methods={
                "enabled": True,
            },
        )
        
        return PaymentIntentResponse(
            client_secret=intent.client_secret,
            payment_intent_id=intent.id,
            amount=intent.amount,
            currency=intent.currency,
        )
    
    except stripe.error.StripeError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Stripe error: {str(e)}"
        )


@router.post(
    "/webhook",
    status_code=status.HTTP_200_OK,
    summary="Handle Stripe webhook events",
    description="Process webhook events from Stripe for payment status updates.",
)
async def stripe_webhook(
    request: Request,
    stripe_signature: str = Header(None, alias="stripe-signature")
) -> JSONResponse:
    """
    Handle Stripe webhook events.
    
    This endpoint receives notifications from Stripe about payment events,
    such as successful payments, failed payments, etc.
    
    The webhook secret must be configured in your Stripe dashboard and
    in the STRIPE_WEBHOOK_SECRET environment variable.
    """
    if not stripe_signature:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Missing Stripe signature"
        )
    
    payload = await request.body()
    
    try:
        event = stripe.Webhook.construct_event(
            payload,
            stripe_signature,
            settings.stripe_webhook_secret
        )
    
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid payload"
        )
    
    except stripe.error.SignatureVerificationError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid signature"
        )
    
    # Handle payment intent succeeded event
    if event["type"] == "payment_intent.succeeded":
        payment_intent = event["data"]["object"]
        order_id_str = payment_intent.get("metadata", {}).get("order_id")
        
        if order_id_str:
            try:
                order_id = UUID(order_id_str)
                db = get_database_adapter()
                updated_order = await db.update_order_payment_status(
                    order_id,
                    PaymentStatus.COMPLETED
                )
                
                if not updated_order:
                    # Log error but don't fail webhook
                    print(f"Warning: Order {order_id} not found for payment update")
            
            except ValueError:
                print(f"Warning: Invalid order_id in payment metadata: {order_id_str}")
    
    return JSONResponse(content={"status": "success"})

