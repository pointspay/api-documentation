# APM Partner Integration (Payment Facilitators)

> For payment service providers and aggregators offering Pointspay as an alternative payment method (APM) to their merchant portfolio.
> Covers: the facilitator model, per-transaction sub-merchant attribution, cash-leg options, and settlement.

---

## The Model

An APM partner integrates with Pointspay **once**, as a payment facilitator. The partner is onboarded as a single parent (facilitator) shop with one set of API credentials and transacts on behalf of any number of sub-merchant shops.

Each sub-merchant shop is registered under the facilitator and is identified **per transaction, not per credential**. There are no per-shop API keys and no per-shop integration work.

```
┌────────────────────┐  POST /v5/payments                 ┌──────────────────┐
│    APM Partner     │  X-API-Key, X-Shop-Code (parent)   │    Pointspay     │
│   (facilitator)    │───────────────────────────────────>│                  │
│                    │  additional_data.custom_data       │  attributes the  │
│  SHOP-A   SHOP-B   │    .child_shop_code = "SHOP-B"     │  payment to      │
│  SHOP-C   ...      │                                    │  SHOP-B          │
└────────────────────┘                                    └──────────────────┘
```

---

## Creating a Payment for a Sub-Merchant

It is the standard [`POST /v5/payments`](https://api.pointspay.com/v5/openapi/redoc) call with one extra field. Authenticate with your own facilitator credentials and name the transacting sub-merchant in `additional_data.custom_data.child_shop_code`:

```json
POST /v5/payments
X-API-Key: <your-api-key>
X-Shop-Code: <your-parent-shop-code>
X-Idempotency-Key: 3f2a9c64-8b1e-4f0a-9c7d-2e5b6a1d8f30

{
  "order_id": "ORD-2026-1234",
  "amount": 10000,
  "currency": "EUR",
  "additional_data": {
    "custom_data": {
      "child_shop_code": "CHILD-SHOP-001",
      "merchant_ref": "12345"
    }
  }
}
```

When `child_shop_code` is present, the payment is attributed to that sub-merchant shop. Pricing, reporting, and settlement all resolve against the sub-merchant, not against the facilitator envelope.

| Rule | Behavior |
|:-----|:---------|
| Named sub-merchant is linked to your facilitator shop | Payment is attributed to the sub-merchant |
| Named sub-merchant is not linked (or unknown) | Transaction is **rejected** (fail closed) |
| `child_shop_code` omitted | Normal single-shop payment on the authenticated shop |

A facilitator can only ever transact for its own linked sub-merchants.

---

## Two Ways to Run the Cash Leg

Pointspay always runs the loyalty-points leg. For the cash leg the partner picks one of two modes:

| | Mode A: Partner-hosted payment | Mode B: Pointspay-hosted checkout |
|:--|:-------------------------------|:----------------------------------|
| **Who owns the cash payment** | The partner | The partner (triggered by Pointspay) |
| **Customer experience** | Customer completes the cash payment inside the partner's existing payment experience, with the partner's own acquiring and methods | Pointspay owns the complete checkout (points balance, redemption, payment UI) and triggers the partner's payment endpoints in the background |
| **Partner-side work** | Reuse of the existing payment stack | API integration only, no customer-facing work |

In both modes Pointspay reconciles the points and cash legs into a single transaction with one `payment_id`.

---

## Settlement

Settlement runs as a scheduled batch process with each merchant. Pointspay shares a settlement report covering all transactions of the period, so the facilitator and its sub-merchants reconcile against one consistent statement.

---

## Getting Started

| Step | What happens |
|:-----|:-------------|
| 1. Facilitator onboarding | Pointspay registers your parent shop and issues API credentials |
| 2. Sub-merchant setup | Sub-merchant shops are linked under your facilitator shop, on your request or handled by Pointspay |
| 3. Sandbox integration | Build and test against the UAT sandbox |
| 4. Go live | Pick the cash-leg mode and switch to production credentials |

---

## API Reference

The APM flow uses the standard V5 surface:

| Endpoint | Purpose |
|:---------|:--------|
| `POST /v5/payments` | Create a payment. Carries `order_id`, `amount`, `currency`, and the optional `child_shop_code` |
| `GET /v5/transactions/{payment_id}/status` | Transaction status with cash/points breakdown and refund attempts |
| `POST /v5/refunds` | Full or partial refund (asynchronous) |
| `GET /v5/refunds/{payment_id}/attempts` | List all refund attempts for a payment |

Full schemas, error codes, and interactive examples: [Production ReDoc](https://api.pointspay.com/v5/openapi/redoc) ・ [UAT Swagger UI](https://uat-api.pointspay.com/v5/openapi/docs)

For redirect and IPN handling, JWT verification, and idempotency, see the [main quick-start](README.md) and [JWT_SIGNATURE_VERIFICATION.md](JWT_SIGNATURE_VERIFICATION.md).
