import os
from fastapi import FastAPI, HTTPException, Request, status, Depends
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import Optional
import stripe

# PUBLIC_INTERFACE
class PaymentIntentRequest(BaseModel):
    """Request body for creating a payment intent"""
    amount: int = Field(..., description="Amount in smallest currency unit (e.g., cents)")
    currency: str = Field(..., description="Currency code (e.g., 'usd', 'fjw')")
    provider: str = Field(..., description="Payment provider ('stripe', 'fijian')")
    description: Optional[str] = Field(None, description="Payment description")

# PUBLIC_INTERFACE
class PaymentIntentResponse(BaseModel):
    """Response body for payment creation"""
    success: bool
    provider: str
    client_secret: Optional[str]
    message: Optional[str]
    payment_id: Optional[str]

# PUBLIC_INTERFACE
class WebhookEvent(BaseModel):
    """Generic webhook event payload"""
    event_type: str = Field(..., description="The type of event received")
    payload: dict = Field(..., description="Raw event payload")

# Read config from env (do not hardcode secrets!)
STRIPE_API_KEY = os.getenv("STRIPE_API_KEY", "")
STRIPE_WEBHOOK_SECRET = os.getenv("STRIPE_WEBHOOK_SECRET", "")
FIJIAN_API_ENDPOINT = os.getenv("FIJIAN_API_ENDPOINT", "https://fijipayments.example.com")
FIJIAN_API_KEY = os.getenv("FIJIAN_API_KEY", "")

stripe.api_key = STRIPE_API_KEY

app = FastAPI(
    title="Payment Gateways Service",
    version="0.1.0",
    description="""
    This service exposes payment endpoints for Stripe and Fijian providers. 
    Use to create payment intents and handle webhooks for payment confirmations.
    See /docs for API or /payment/webhook/stripe for Stripe webhook registration.
    """,
    openapi_tags=[
        {"name": "Stripe", "description": "Stripe payment operations"},
        {"name": "FijianProvider", "description": "Fijian Payment Provider operations"},
    ]
)

# Allow cross-origin calls (for development)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Stripe integration logic
# PUBLIC_INTERFACE
@app.post("/payment/intent/stripe", response_model=PaymentIntentResponse, tags=["Stripe"], summary="Create Stripe Payment Intent", description="Create a payment intent with Stripe and return client secret.")
async def create_stripe_payment_intent(data: PaymentIntentRequest):
    """
    Create a Stripe payment intent for the given amount and currency.

    Parameters:
        data (PaymentIntentRequest): amount, currency, provider ('stripe'), description

    Returns:
        PaymentIntentResponse: Stripe client secret, payment_id, status.
    """
    if not STRIPE_API_KEY:
        raise HTTPException(status_code=500, detail="Stripe integration is not configured.")
    try:
        intent = stripe.PaymentIntent.create(
            amount=int(data.amount),
            currency=data.currency,
            description=data.description,
            # More Stripe parameters as required
        )
        return PaymentIntentResponse(
            success=True,
            provider="stripe",
            client_secret=intent.client_secret,
            payment_id=intent.id
        )
    except Exception as e:
        return PaymentIntentResponse(
            success=False,
            provider="stripe",
            message=f"Stripe error: {str(e)}"
        )

# Stripe webhook endpoint
# PUBLIC_INTERFACE
@app.post("/payment/webhook/stripe", tags=["Stripe"], summary="Stripe Webhook Handler", description="Endpoint for Stripe to POST payment events.")
async def stripe_webhook(request: Request):
    """
    Receives and validates Stripe webhook events.

    Returns:
        JSON dict with event handling status.
    """
    if not STRIPE_WEBHOOK_SECRET:
        raise HTTPException(status_code=500, detail="Stripe webhook not configured.")
    payload = await request.body()
    sig_header = request.headers.get("stripe-signature")
    try:
        event = stripe.Webhook.construct_event(
            payload=payload, sig_header=sig_header, secret=STRIPE_WEBHOOK_SECRET
        )
    except stripe.error.SignatureVerificationError:
        return JSONResponse({"error": "Invalid signature"}, status_code=400)
    # Handle successful payment event as example
    if event['type'] == 'payment_intent.succeeded':
        # Here you might update your database with payment confirmation, etc.
        pass
    return {"received": True, "type": event["type"]}

# Fijian payment provider integration stub
# PUBLIC_INTERFACE
@app.post("/payment/intent/fijian", response_model=PaymentIntentResponse, tags=["FijianProvider"], summary="Fijian Provider Payment Intent", description="Stub endpoint to initiate payment with Fijian provider.")
async def create_fijian_payment_intent(data: PaymentIntentRequest):
    """
    Integrate with Fijian local provider API.
    This is a stub; replace with actual HTTP request to Fijian payment system.

    Returns:
        PaymentIntentResponse: Provider payment status, id, etc.
    """
    # This is a stub, implement actual API call out to Fijian provider
    if not FIJIAN_API_KEY or not FIJIAN_API_ENDPOINT:
        return PaymentIntentResponse(
            success=False,
            provider="fijian",
            message="Fijian provider not configured."
        )
    # Simulate API call to local Fijian payment system
    # Example only: Replace with real HTTP request and parsing
    fake_response = {
        "payment_id": "FIJI123456",
        "client_secret": "example-fijian-token",
        "status": "pending"
    }
    return PaymentIntentResponse(
        success=True,
        provider="fijian",
        client_secret=fake_response["client_secret"],
        payment_id=fake_response["payment_id"],
        message="Fijian provider integration stub: replace with real transaction"
    )

# Fijian provider webhook stub
# PUBLIC_INTERFACE
@app.post("/payment/webhook/fijian", tags=["FijianProvider"], summary="Fijian Provider Webhook Handler", description="Stub endpoint for Fijian payment provider notifications.")
async def fijian_webhook(event: WebhookEvent):
    """
    Receives payment notification events from the Fijian provider.

    Returns:
        JSON dict acknowledging receipt.
    """
    # Implement actual verification and processing as required
    return {"received": True, "event_type": event.event_type, "info": "Stub handler"}

# Generic unified endpoints (router/broker for both providers)
# PUBLIC_INTERFACE
@app.post("/payment/intent", response_model=PaymentIntentResponse, tags=["Stripe", "FijianProvider"], summary="Create Payment Intent", description="Unified endpoint to create payment intent via specified provider.")
async def create_payment_intent(data: PaymentIntentRequest):
    """
    Route payment intent request to the specified provider (stripe/fijian)

    Returns:
        PaymentIntentResponse.
    """
    if data.provider == "stripe":
        return await create_stripe_payment_intent(data)
    elif data.provider == "fijian":
        return await create_fijian_payment_intent(data)
    else:
        return PaymentIntentResponse(
            success=False,
            provider=data.provider,
            message=f"Unknown provider: {data.provider}"
        )

# Health check endpoint
# PUBLIC_INTERFACE
@app.get("/health", summary="Service Health", tags=["Health"])
def health():
    """Check payment gateway service health."""
    return {"status": "ok"}

# Developer help / documentation for Stripe webhooks
# PUBLIC_INTERFACE
@app.get("/payment/webhook/stripe/docs", tags=["Stripe"], summary="Stripe Webhook Usage Help", response_class=JSONResponse)
def stripe_webhook_docs():
    """
    Provides doc/help for configuring Stripe webhook with correct endpoint URL and expected event types.

    Returns:
        JSON documentation on Stripe webhook usage for this API service.
    """
    return {
        "info": "Register this endpoint with your Stripe Dashboard for webhook events.",
        "endpoint": "/payment/webhook/stripe",
        "expected_events": [
            "payment_intent.succeeded",
            "payment_intent.payment_failed",
            "charge.succeeded"
        ]
    }

# PUBLIC_INTERFACE
@app.get("/payment/webhook/fijian/docs", tags=["FijianProvider"], summary="Fijian Provider Webhook Usage Help", response_class=JSONResponse)
def fijian_webhook_docs():
    """
    Documents Fijian payment provider webhook expectations and usage.

    Returns:
        JSON documentation on Fijian webhook expectations.
    """
    return {
        "info": "Fijian provider should POST notifications to this endpoint.",
        "endpoint": "/payment/webhook/fijian",
        "expected_fields": [
            "event_type",
            "payload"
        ],
        "note": "This is a stub; provide your event schema when available."
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8083, reload=True)
