# Payment Gateways Service – EVISA Portal

This microservice acts as a broker for payment requests and notifications from Stripe and local Fijian payment providers.

## Features

- Create payment intents for Stripe and a Fijian provider
- Handles webhooks for payment completion/refund notifications
- Clean separation between gateway integrations
- Environment-based configuration and secrets

## API Endpoints

| Endpoint                      | Method | Description                                            | Tags          |
|-------------------------------|--------|--------------------------------------------------------|---------------|
| `/payment/intent/stripe`      | POST   | Create Stripe payment intent                           | Stripe        |
| `/payment/webhook/stripe`     | POST   | Handle Stripe payment webhook events                   | Stripe        |
| `/payment/intent/fijian`      | POST   | Create payment intent with Fijian provider (STUB)      | FijianProvider|
| `/payment/webhook/fijian`     | POST   | Handle Fijian provider webhook notifications (STUB)    | FijianProvider|
| `/payment/intent`             | POST   | Unified payment creation endpoint                      | Stripe, FijianProvider |
| `/health`                     | GET    | Service health check                                   | Health        |

Swagger UI: [http://localhost:8083/docs](http://localhost:8083/docs)

## Environment Variables

Create a `.env` file or set environment variables as follows:

- `STRIPE_API_KEY` - **Required for Stripe**: Your Stripe secret key.
- `STRIPE_WEBHOOK_SECRET` - **Required for Stripe webhooks**: Webhook signing secret from Stripe dashboard.
- `FIJIAN_API_ENDPOINT` - **Optional**: Endpoint for Fijian provider (default: demo URL).
- `FIJIAN_API_KEY` - **Optional**: API key for Fijian provider.

## Setup & Run

1. Install dependencies:
   ```
   pip install -r requirements.txt
   ```
2. Set required environment variables.
3. Start the server:
   ```
   uvicorn main:app --reload --host 0.0.0.0 --port 8083
   ```
4. Open `/docs` for Swagger UI.

## Stripe Setup Guide

- Register your webhook: Point Stripe's webhook configuration to `/payment/webhook/stripe`.
- Listen for events: `payment_intent.succeeded`, `payment_intent.payment_failed`, etc.
- Use `/payment/intent/stripe` to create payment intents from applications.

## Fijian Provider Integration Notes

- `/payment/intent/fijian` and `/payment/webhook/fijian` are STUBS.
- Replace stub logic in `main.py` with real API requests and verification as required by provider's documentation.
- Review `PaymentIntentRequest` and `WebhookEvent` model in `main.py` for expected payloads.

## Security & Compliance

- Never commit secrets or API keys to source control.
- Use HTTPS in production for webhook endpoints.
- Validate all webhook requests for authenticity (see Stripe docs).

---
Task completed: Payment Gateways microservice (Stripe & Fijian providers) scaffolded with endpoints, config, hooks, docs.
