![image](https://github.com/user-attachments/assets/aff9c589-000d-4898-bc1e-11d67e1ed574)

# Pointspay REST API Documentation

> **The canonical, always-up-to-date API specification is now served directly from the API itself.**
> This repository provides a quick-start overview and supplementary guides. For full endpoint details, request/response schemas, and interactive examples, use the links below.

---

## Live API Documentation (V5)

| Environment | Interactive Docs (Swagger UI) | Reference Docs (ReDoc) | OpenAPI Spec |
|:------------|:------------------------------|:-----------------------|:-------------|
| **UAT / Sandbox** | [uat-api.pointspay.com/v5/openapi/docs](https://uat-api.pointspay.com/v5/openapi/docs) | — | [openapi.json](https://uat-api.pointspay.com/v5/openapi.json) |
| **Production** | — | [api.pointspay.com/v5/openapi/redoc](https://api.pointspay.com/v5/openapi/redoc) | [openapi.json](https://api.pointspay.com/v5/openapi.json) |

> **Which link should I use?**
> - Use the **UAT Swagger UI** during development — it lets you execute requests directly from the browser against the sandbox.
> - Use the **Production ReDoc** as the polished reference when building or reviewing your integration.
> - Download the **OpenAPI JSON** to generate client SDKs (e.g. `openapi-generator`) or import into Postman.

---

## Supplementary Guides in This Repository

| Document | Description |
|:---------|:------------|
| [JWT Signature Verification](JWT_SIGNATURE_VERIFICATION.md) | Language-specific code examples (Python, Java, etc.) for verifying `pp_token` JWTs. |
| [S2S Integration Guide](S2S_INTEGRATION.md) | Technical guide for loyalty programs integrating their earn/burn endpoints with Pointspay. |
| [S2S Integration One-Pager](S2S_INTEGRATION_ONEPAGER.md) | Executive overview of the split-payment integration for business stakeholders. |
| [Category-Specific Commissions](REST%20API_Category-Specific%20Commission%20Implementation.md) | Appendix for merchants with category-varying commission rates. |

---

## Quick-Start Overview

### 1. Environments

| Environment | API Base URL | Checkout UI |
|:------------|:-------------|:------------|
| **UAT / Sandbox** | `https://uat-api.pointspay.com` | `https://uat-secure.pointspay.com` |
| **Production** | `https://api.pointspay.com` | `https://secure.pointspay.com` |

All V5 endpoints are prefixed with `/v5/`:

```
POST  /v5/payments                              – Initiate a payment
POST  /v5/refunds                               – Request a full or partial refund
GET   /v5/refunds/{payment_id}/attempts          – List all refund attempts
GET   /v5/transactions/{payment_id}/status       – Transaction status with refund breakdown
GET   /v5/transactions?order_id=ORD-123          – Search transactions by order ID
GET   /v5/.well-known/openid-configuration       – OIDC discovery
GET   /v5/.well-known/jwks.json                  – Public keys for JWT verification
```

### 2. Authentication (V5)

V5 uses **API-key authentication** — no certificates, keystores, or signature generation required.

| Header | Required | Description |
|:-------|:---------|:------------|
| `X-API-Key` | Yes | Your API key, provided during merchant onboarding. |
| `X-Shop-Code` | Yes | Your shop identifier. |
| `X-Idempotency-Key` | Yes (payments) / Recommended (refunds) | Unique string (≥ 16 chars, UUID recommended) to prevent duplicate processing. |

### 3. Payments

Initiate a payment by POSTing to `/v5/payments`. The response contains a `href` redirect URL and a `payment_id`. Redirect the shopper to `href` only when `status` is `ACCEPTED`.

**Request body:**

| Parameter | Type | Required | Description |
|:----------|:-----|:---------|:------------|
| `order_id` | string | Yes | Your order ID (max 64 chars). |
| `amount` | integer | Yes | Amount in minor units (e.g. USD 100.00 → `10000`). |
| `currency` | string | Yes | ISO 4217 currency code. |
| `language` | string | No | ISO 639-1 language code (default: `en`). |
| `additional_data` | object | No | Dynamic URLs, categories, custom data. |

**Response body:**

| Field | Type | Description |
|:------|:-----|:------------|
| `timestamp` | integer | Epoch ms when the payment was created. |
| `href` | string | Redirect URL for the Pointspay checkout (when `ACCEPTED`). |
| `order_id` | string | Echo of your order ID. |
| `payment_id` | string | Unique Pointspay payment ID (UUID). |
| `status` | string | `ACCEPTED` or `REJECTED`. |

> See the full schema, error responses, and sample payloads in the [live docs](https://api.pointspay.com/v5/openapi/redoc).

### 4. Redirects & IPN Notifications

After payment, Pointspay communicates the result via:

1. **Browser redirect** — shopper is sent to your `success`/`failure`/`cancel` URL with `?pp_token=<JWT>` appended.
2. **IPN callback** — server-to-server POST to your `ipn` URL with the JWT as the body.

IPN is sent for **terminal states only**: `SUCCESS` or `FAILED`.

Dynamic redirect/IPN URLs can be passed per-transaction in `additional_data.dynamic_urls`:

| Parameter | Description |
|:----------|:------------|
| `success` | Redirect URL on successful payment. |
| `failure` | Redirect URL on failed payment. |
| `cancel` | Redirect URL when user cancels. |
| `ipn` | Server-to-server callback URL. |

### 5. JWT Verification (`pp_token`)

V5 replaces the previous OAuth 1.0a signature scheme with signed **JWT tokens**.

**JWKS endpoints (public keys):**

| Environment | URL |
|:------------|:----|
| UAT | `https://uat-api.pointspay.com/v5/.well-known/jwks.json` |
| Production | `https://api.pointspay.com/v5/.well-known/jwks.json` |

**Required validations:**

| Claim | Check |
|:------|:------|
| Algorithm | RS256, RS384, or RS512 |
| `iss` (issuer) | `https://api.pointspay.com/v5` |
| `aud` (audience) | Your shop code |
| `exp` (expiration) | Not expired |

**Redirect token claims** (minimal):

| Claim | Type | Description |
|:------|:-----|:------------|
| `pid` | string | Pointspay payment ID |
| `oid` | string | Your order ID |
| `sts` | string | `SUCCESS` or `FAILED` |

**IPN token claims** (full):

| Claim | Type | Description |
|:------|:-----|:------------|
| `oid` | string | Your order ID |
| `pid` | string | Pointspay payment ID |
| `rid` | string | Refund ID (present when `typ` = `REFUND`) |
| `amt` | integer | Amount in minor units |
| `cur` | string | Currency code |
| `sts` | string | `SUCCESS` or `FAILED` |
| `typ` | string | `PAYMENT` or `REFUND` |

> **Security:** Never trust redirect URLs alone — always validate the `pp_token` signature server-side.
> See [JWT_SIGNATURE_VERIFICATION.md](JWT_SIGNATURE_VERIFICATION.md) for code examples in Python, Java, and more.

### 6. Refunds

Request a full or partial refund by POSTing to `/v5/refunds`. Refunds are **asynchronous** — the response returns immediately with `PENDING` status. Use polling or IPN to get the final result.

**Request body:**

| Parameter | Type | Required | Description |
|:----------|:-----|:---------|:------------|
| `amount` | integer | Yes | Refund amount in minor units. |
| `payment_id` | string | Yes | The original Pointspay payment ID. |
| `refund_reason` | string | No | Reason for refund (max 200 chars). |

**Polling for refund status:**

- `GET /v5/refunds/{payment_id}/attempts` — list all refund attempts with individual statuses.
- `GET /v5/transactions/{payment_id}/status` — full transaction status including cash/points breakdown and refund attempts.

**Refund statuses:** `PENDING` → `SUCCESS` or `FAILED` (terminal, immutable).

### 7. Transaction Status

`GET /v5/transactions/{payment_id}/status` returns the full transaction lifecycle:

| Field | Type | Description |
|:------|:-----|:------------|
| `payment_id` | string | Payment UUID. |
| `order_id` | string | Your order ID. |
| `status` | string | `SUCCESS`, `PENDING`, `FAILED`, `REFUNDED`, `PARTIALLY_REFUNDED`. |
| `total_amount` | integer | Original payment in minor units. |
| `cash_amount` | integer | Cash (card) portion. |
| `points_amount` | integer | Points portion. |
| `currency_code` | string | ISO 4217. |
| `total_refunded` | integer | Sum of all successful refunds. |
| `refund_attempts` | array | Individual refund attempts with `refund_id`, `status`, `refund_amount`. |

You can also search by order ID: `GET /v5/transactions?order_id=ORD-123` — useful when you don't have the `payment_id` stored.

---

## Key V5 Enhancements vs. Previous Versions

| Change | Before (V1/V4) | V5 |
|:-------|:----------------|:---|
| **Authentication** | OAuth 1.0a with certificate-based signatures | API key headers (`X-API-Key`, `X-Shop-Code`) |
| **Response verification** | Manual RSA signature verification | Standard JWT (`pp_token`) with JWKS |
| **Amounts** | Strings (`"10000"`) | Integers (`10000`) |
| **Refund flow** | Synchronous | Asynchronous with polling & IPN |
| **Payment breakdown** | Not available | `cash_amount` + `points_amount` fields |
| **Refund tracking** | Single status | Per-attempt tracking with `refund_id` |
| **Transaction search** | By `payment_id` only | Also by `order_id` |
| **Idempotency** | Not supported | `X-Idempotency-Key` header |

### Migration from V4

| V4 Path | V5 Path | Notes |
|:--------|:--------|:------|
| `/v4/payments` | `/v5/payments` | No breaking changes (thin wrapper). |
| `/v4/refunds` | `/v5/refunds` | New async response format. |
| `/v4/transactions/{id}/status` | `/v5/transactions/{id}/status` | Enhanced response with cash/points breakdown & refund attempts. |

---

## Dynamic Pointspay Logo

Use the dynamic logo URL when displaying Pointspay as a payment method:

| Environment | Example |
|:------------|:--------|
| Sandbox | `https://uat-secure.pointspay.com/checkout/user/btn-img-v2?shop_code=YOUR_SHOP_CODE` |
| Live | `https://secure.pointspay.com/checkout/user/btn-img-v2?shop_code=YOUR_SHOP_CODE` |

| Parameter | Required | Description |
|:----------|:---------|:------------|
| `shop_code` | Yes | Shop code provided during onboarding (max 32 chars). |
| `language` | No | ISO 639-1 language code (default: `en`). |

---

## Error Handling

All error responses follow a consistent JSON format:

```json
{
  "code": "TRANSACTION_NOT_FOUND",
  "message": "Payment with the provided ID was not found. Please check if Payment ID is valid.",
  "key": "TRANSACTION_NOT_FOUND"
}
```

For the full list of error codes and HTTP status codes, see the [live API docs](https://api.pointspay.com/v5/openapi/redoc).

---

## Additional Resources

- **Full API Specification:** [Production ReDoc](https://api.pointspay.com/v5/openapi/redoc) ・ [UAT Swagger UI](https://uat-api.pointspay.com/v5/openapi/docs)
- **OpenAPI JSON:** [Production](https://api.pointspay.com/v5/openapi.json) ・ [UAT](https://uat-api.pointspay.com/v5/openapi.json)
- **JWT Verification Examples:** [JWT_SIGNATURE_VERIFICATION.md](JWT_SIGNATURE_VERIFICATION.md)
- **S2S Integration (Loyalty Programs):** [S2S_INTEGRATION.md](S2S_INTEGRATION.md)
- **Category Commissions:** [Category Appendix](REST%20API_Category-Specific%20Commission%20Implementation.md)
