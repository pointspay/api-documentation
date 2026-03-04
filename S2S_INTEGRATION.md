# Pointspay — Loyalty Program S2S Integration Guide

> **Audience**: Technical teams at loyalty programs integrating with Pointspay's split payment system.
> **Version**: 1.0 — March 2026

---

## Table of Contents

1. [Overview](#1-overview)
2. [Glossary](#2-glossary)
3. [Payment Scenarios](#3-payment-scenarios)
4. [Integration Tiers](#4-integration-tiers)
5. [Checkout Flow — End-to-End](#5-checkout-flow--end-to-end)
6. [Authentication](#6-authentication)
   - 6.1 [OAuth2 Authorization Code (User Consent)](#61-oauth2-authorization-code-user-consent--recommended)
   - 6.2 [Machine Token — Client Credentials (S2S)](#62-machine-token--client-credentials-s2s)
   - 6.3 [SAML 2.0 (Variant)](#63-saml-20-variant)
   - 6.4 [OTP / In-App Approval (Variant)](#64-otp--in-app-approval-variant)
7. [User Consent](#7-user-consent)
8. [Required S2S Endpoints](#8-required-s2s-endpoints)
9. [Earn (Accrue) Flow](#9-earn-accrue-flow)
10. [Burn (Redeem) Flow](#10-burn-redeem-flow)
11. [Split Payment Orchestration](#11-split-payment-orchestration)
12. [Refunds & Reversals](#12-refunds--reversals)
13. [Error Handling & Idempotency](#13-error-handling--idempotency)
14. [Onboarding Checklist](#14-onboarding-checklist)

---

## 1. Overview

Pointspay enables merchants to accept **loyalty points as a payment method** alongside traditional card payments. When a customer checks out at a participating merchant, they can:

- Pay entirely with a card and **earn** loyalty points on the purchase.
- **Split** the payment between their card and loyalty points.
- Pay entirely with loyalty points.

This document describes the **Server-to-Server (S2S) integration** that your loyalty program must implement so that Pointspay can securely earn and burn points on behalf of authenticated members.

```
┌──────────────────────────────────────────────────────────────────┐
│                        MERCHANT CHECKOUT                         │
│                                                                  │
│   ┌─────────────┐    ┌──────────────┐    ┌────────────────────┐  │
│   │  Cash Leg    │    │  Points Leg  │    │  Earn-Back Leg     │  │
│   │  (Card Pay)  │ +  │  (Redeem)    │ +  │  (Accrue on Cash)  │  │
│   └─────────────┘    └──────────────┘    └────────────────────┘  │
│                                                                  │
│   Total Order = Cash Amount + Points Amount                      │
│   Earn-Back   = Points accrued on the Cash Amount                │
└──────────────────────────────────────────────────────────────────┘
```

Pointspay acts as the **orchestrator** between the merchant, the payment provider (card processing), and your loyalty program (points processing). Your program exposes a set of S2S endpoints; Pointspay calls them at the appropriate stage of the checkout.

---

## 2. Glossary

| Term | Definition |
|------|-----------|
| **Earn / Accrue** | Credit loyalty points to a member's account (reward for a purchase). |
| **Burn / Redeem** | Debit loyalty points from a member's account to pay for (part of) a purchase. |
| **Split Payment** | A single order paid with both a card (cash leg) and loyalty points (points leg). |
| **Cash Leg** | The portion of the order paid via card through the payment provider. |
| **Points Leg** | The portion of the order paid with loyalty points via your program's redeem endpoint. |
| **Earn-Back** | Points accrued on the cash portion of a split payment. |
| **Member ID** | The unique identifier of a loyalty member in your program (e.g., frequent-flyer number). |
| **Machine Token** | An S2S access token obtained via OAuth2 `client_credentials` grant; used for server-to-server calls that do not require user presence. |
| **Member Token** | A user-scoped access token obtained via OAuth2 `authorization_code` grant; proves user consent. |
| **User Consent** | Explicit authorization by the loyalty member to allow Pointspay to access their account and/or spend their points. |
| **OTP** | One-Time Password — an additional verification step some programs require before a burn transaction. |
| **Operation Reference** | A unique identifier returned by your program for each earn/burn operation. Used for reversals. |
| **Order Number** | Pointspay's unique identifier for the merchant order. Sent with every operation for traceability. |

---

## 3. Payment Scenarios

A checkout with Pointspay results in one of three scenarios:

```
┌────────────────────────────────────────────────────────────┐
│                     SCENARIO 1: EARN ONLY                  │
│                                                            │
│   User pays 100% with card.                                │
│   Points are EARNED on the full amount.                    │
│                                                            │
│   Card Payment: $100.00                                    │
│   Points Earned: 500 pts                                   │
│   Points Spent:  0 pts                                     │
├────────────────────────────────────────────────────────────┤
│                   SCENARIO 2: SPLIT PAYMENT                │
│                                                            │
│   User pays partially with card, partially with points.    │
│   Points are BURNED for the points portion.                │
│   Points are EARNED on the cash portion.                   │
│                                                            │
│   Card Payment:  $60.00                                    │
│   Points Spent:  2000 pts  (equivalent to $40.00)          │
│   Points Earned: 300 pts   (on the $60.00 cash portion)    │
├────────────────────────────────────────────────────────────┤
│                  SCENARIO 3: FULL BURN                     │
│                                                            │
│   User pays 100% with points.                              │
│   No card payment. No earn-back.                           │
│                                                            │
│   Card Payment:  $0.00                                     │
│   Points Spent:  5000 pts  (equivalent to $100.00)         │
│   Points Earned: 0 pts                                     │
└────────────────────────────────────────────────────────────┘
```

---

## 4. Integration Tiers

Your program can support one or more tiers. The tier determines which S2S endpoints you must implement.

| Tier | Code | Description | Required Endpoints |
|------|------|-------------|--------------------|
| **Earn Only** | `EARN` | Members earn points on card purchases. No point spending. | Token, Member Profile, Accrue, Reverse Accrue |
| **Burn Only** | `BURN` | Members spend points as payment. No earning. | Token, Member Profile, Redeem, OTP (if applicable), Reverse Redeem |
| **Earn + Burn** | `ALL` | Full split payment support. Members can earn AND spend points. | All of the above |

> **Recommendation**: Most programs integrate at the `ALL` (Earn + Burn) tier to provide the complete split payment experience.

---

## 5. Checkout Flow — End-to-End

The diagram below shows the complete checkout lifecycle for a **split payment** (Earn + Burn), which is the most comprehensive flow.

```
    Customer              Merchant            Pointspay           Your Program
       │                    │                    │                     │
       │  1. Checkout       │                    │                     │
       │───────────────────>│                    │                     │
       │                    │  2. Create Txn     │                     │
       │                    │───────────────────>│                     │
       │                    │                    │                     │
       │  3. Select loyalty program              │                     │
       │────────────────────────────────────────>│                     │
       │                    │                    │                     │
       │  4. Redirect to program login           │                     │
       │<────────────────────────────────────────│                     │
       │                    │                    │                     │
       │  5. Log in & authorize ────────────────────────────────────> │
       │                    │                    │                     │
       │  6. Redirect back with auth code        │                     │
       │<─────────────────────────────────────────────────────────────│
       │                    │                    │                     │
       │  7. Auth code      │                    │                     │
       │────────────────────────────────────────>│                     │
       │                    │                    │  8. Exchange code    │
       │                    │                    │     for token        │
       │                    │                    │────────────────────>│
       │                    │                    │    member_token      │
       │                    │                    │<────────────────────│
       │                    │                    │                     │
       │                    │                    │  9. Fetch profile    │
       │                    │                    │     & balance        │
       │                    │                    │────────────────────>│
       │                    │                    │  { balance: 5000 }   │
       │                    │                    │<────────────────────│
       │                    │                    │                     │
       │  10. Show balance & split options       │                     │
       │<────────────────────────────────────────│                     │
       │                    │                    │                     │
       │  11. Choose split: $60 card + 2000 pts  │                     │
       │────────────────────────────────────────>│                     │
       │                    │                    │                     │
       │                    │                    │  12. OTP (if req.)   │
       │                    │                    │────────────────────>│
       │                    │                    │  { otpSent: true }   │
       │                    │                    │<────────────────────│
       │  13. Enter OTP     │                    │                     │
       │────────────────────────────────────────>│                     │
       │                    │                    │                     │
       │                    │                    │  14. Redeem points   │
       │                    │                    │  (2000 pts + OTP)    │
       │                    │                    │────────────────────>│
       │                    │                    │  { ref: "R-123" }    │
       │                    │                    │<────────────────────│
       │                    │                    │                     │
       │                    │                    │  15. Charge card     │
       │                    │                    │  ($60.00)            │
       │                    │                    │──> Payment Provider  │
       │                    │                    │                     │
       │                    │                    │  16. Accrue points   │
       │                    │                    │  (300 pts on $60)    │
       │                    │                    │────────────────────>│
       │                    │                    │  { ref: "A-456" }    │
       │                    │                    │<────────────────────│
       │                    │                    │                     │
       │  17. Confirmation  │                    │                     │
       │<────────────────────────────────────────│                     │
       │                    │                    │                     │
```

**Steps at a glance**:

| # | Step | Actor | Notes |
|---|------|-------|-------|
| 1–2 | Customer initiates checkout | Merchant → Pointspay | Transaction is created in Pointspay |
| 3–4 | Customer selects loyalty program | Customer → Pointspay | Pointspay provides redirect URL |
| 5–6 | User authenticates with program | Customer → Program | OAuth2 Authorization Code flow |
| 7–8 | Token exchange | Pointspay → Program (S2S) | `authorization_code` → `access_token` |
| 9 | Fetch profile & balance | Pointspay → Program (S2S) | Determines available points |
| 10–11 | Customer chooses split | Customer → Pointspay | UI shows balance & options |
| 12–13 | OTP (if required) | Pointspay → Program → Customer | Only if program requires OTP for burn |
| 14 | Redeem (points leg) | Pointspay → Program (S2S) | Debit points from member |
| 15 | Card charge (cash leg) | Pointspay → Payment Provider | Standard card processing |
| 16 | Accrue (earn-back) | Pointspay → Program (S2S) | Credit points for cash portion |
| 17 | Confirmation | Pointspay → Customer | Order complete |

> **Note**: Steps 12–13 (OTP) only apply if your program requires additional verification before a burn. See [Section 6.4](#64-otp--in-app-approval-variant).

---

## 6. Authentication

Pointspay supports multiple authentication models. Each model serves a different purpose in the integration.

### 6.1 OAuth2 Authorization Code (User Consent) — Recommended

This is the **primary and recommended** authentication model for user consent. It follows the standard OAuth2 Authorization Code flow.

**Purpose**: Obtain user consent to access their loyalty account and (for burn) spend their points.

**What you must provide**:

| Requirement | Description |
|-------------|-------------|
| **Authorize URL** | The URL where Pointspay redirects the user to log in (e.g., `https://your-program.com/oauth/authorize`) |
| **Token URL** | The S2S endpoint where Pointspay exchanges the authorization code for an access token |
| **Client Credentials** | `client_id` and `client_secret` issued to Pointspay |
| **Redirect URI whitelist** | You must whitelist Pointspay's callback URL in your OAuth2 configuration |
| **Scopes** | Define what scopes are needed (e.g., `profile`, `balance`, `redeem`) |

**Flow**:

```
    Customer               Pointspay              Your Program (IdP)
       │                      │                          │
       │  1. Click "Log in    │                          │
       │     with Program"    │                          │
       │─────────────────────>│                          │
       │                      │                          │
       │  2. HTTP 302 Redirect to:                       │
       │     {authorize_url}?                            │
       │       response_type=code                        │
       │       &client_id={client_id}                    │
       │       &redirect_uri={callback}                  │
       │       &scope={scopes}                           │
       │       &state={session_state}                    │
       │<─────────────────────│                          │
       │                      │                          │
       │  3. User logs in at your program ──────────────>│
       │     (username / password / SSO)                 │
       │                      │                          │
       │  4. User authorizes Pointspay ─────────────────>│
       │     to access their account                     │
       │                      │                          │
       │  5. Redirect to Pointspay callback:             │
       │     {redirect_uri}?code={auth_code}             │
       │       &state={session_state}                    │
       │<─────────────────────────────────────────────── │
       │                      │                          │
       │                      │  6. POST {token_url}     │
       │                      │     grant_type=           │
       │                      │       authorization_code  │
       │                      │     code={auth_code}      │
       │                      │     client_id=...         │
       │                      │     client_secret=...     │
       │                      │     redirect_uri=...      │
       │                      │─────────────────────────>│
       │                      │                          │
       │                      │  7. { access_token,      │
       │                      │       token_type,         │
       │                      │       expires_in }        │
       │                      │<─────────────────────────│
       │                      │                          │
```

**Key points**:
- The `access_token` (member token) proves the user has consented.
- Pointspay uses this token to call protected endpoints (e.g., fetch profile).
- The `state` parameter is used to correlate the callback with the original session.
- Token expiration should be long enough to cover the checkout session (recommended: ≥ 30 minutes).

---

### 6.2 Machine Token — Client Credentials (S2S)

**Purpose**: Authenticate Pointspay's server for backend operations that do not require user presence — such as accruing points, performing reversals, or fetching balance by member ID.

**What you must provide**:

| Requirement | Description |
|-------------|-------------|
| **Token URL** | Endpoint accepting `grant_type=client_credentials` |
| **Client Credentials** | `client_id` and `client_secret` for the S2S application |
| **Audience** (optional) | If your token endpoint requires an `audience` parameter |

**Flow**:

```
    Pointspay                         Your Program
       │                                  │
       │  POST {token_url}                │
       │    grant_type=client_credentials  │
       │    client_id={s2s_client_id}      │
       │    client_secret={s2s_secret}     │
       │    audience={audience}            │
       │─────────────────────────────────>│
       │                                  │
       │  { access_token, expires_in }    │
       │<─────────────────────────────────│
       │                                  │
       │  (Token is cached and reused     │
       │   until near expiry)             │
       │                                  │
```

**Key points**:
- Pointspay caches the machine token and refreshes it before expiry.
- If a cached token is rejected (e.g., revoked), Pointspay will automatically fetch a new one and retry the request **once**.
- Token lifetime recommendation: 60 minutes.
- The machine token is used in a header (e.g., `Authorization: Bearer {token}` or a custom header as agreed).

---

### 6.3 SAML 2.0 (Variant)

Some programs use SAML 2.0 for user authentication instead of OAuth2. If your organization already uses a SAML Identity Provider (e.g., Okta, Azure AD), Pointspay can integrate via SAML.

**What you must provide**:

| Requirement | Description |
|-------------|-------------|
| **IdP SSO URL** | The URL where Pointspay sends the SAML `AuthnRequest` (HTTP-POST binding) |
| **IdP Certificate** | Your IdP's X.509 signing certificate for response verification |
| **SP Entity ID** | Agreed Service Provider entity ID for Pointspay |
| **Attribute Mapping** | Which SAML attribute contains the Member ID (e.g., `FFP Number`) |
| **ACS URL whitelist** | Pointspay's Assertion Consumer Service URL must be registered at your IdP |

**Flow**:

```
    Customer               Pointspay              Your IdP (e.g., Okta)
       │                      │                          │
       │  1. Select program   │                          │
       │─────────────────────>│                          │
       │                      │  2. Build SAML           │
       │                      │     AuthnRequest         │
       │                      │     (signed, POST)       │
       │  3. Auto-POST form   │                          │
       │     to IdP SSO URL   │                          │
       │<─────────────────────│                          │
       │─────────────────────────────────────────────── >│
       │                      │                          │
       │  4. User logs in at IdP                         │
       │─────────────────────────────────────────────── >│
       │                      │                          │
       │  5. IdP returns signed SAML Response            │
       │     (HTTP-POST to Pointspay ACS URL)            │
       │<────────────────────────────────────────────────│
       │─────────────────────>│                          │
       │                      │  6. Validate response    │
       │                      │     Extract Member ID    │
       │                      │     from attribute       │
       │                      │                          │
```

---

### 6.4 OTP / In-App Approval (Variant)

Some programs — particularly banks in certain regions — require an explicit **One-Time Password** or **in-app push approval** before a burn (redeem) transaction can proceed. This is an additional security layer on top of user authentication.

There are two sub-patterns:

#### Pattern A — OTP via SMS / Email

Pointspay requests an OTP to be sent to the member. The member enters the OTP in the Pointspay checkout UI. Pointspay re-submits the redeem request with the OTP code.

```
    Customer               Pointspay                  Your Program
       │                      │                            │
       │  (User already       │                            │
       │   authenticated)     │                            │
       │                      │  1. Request OTP            │
       │                      │     POST /request-otp      │
       │                      │     { memberId }           │
       │                      │───────────────────────────>│
       │                      │                            │
       │                      │  2. { otpSent: true,       │
       │                      │    otpReceiver: "+XX**89",  │
       │                      │    otpExpiration: "..." }   │
       │                      │<───────────────────────────│
       │                      │                            │
       │                      │      ┌──── SMS/Email ─────>│ Member's
       │                      │      │    with OTP code     │ phone/email
       │                      │      │                      │
       │  3. Enter OTP code   │      │                      │
       │─────────────────────>│      │                      │
       │                      │                            │
       │                      │  4. Redeem + OTP           │
       │                      │     POST /redeem           │
       │                      │     { ..., otpCode }       │
       │                      │───────────────────────────>│
       │                      │                            │
       │                      │  5. { success, ref }       │
       │                      │<───────────────────────────│
       │                      │                            │
```

**Key points**:
- The OTP request returns a **masked recipient** (e.g., `+XX****89`) so the customer knows where to expect the code.
- The OTP has an **expiration time** — Pointspay displays a timer in the UI.
- If the OTP expires, the customer can request a new one.

#### Pattern B — In-App Push Approval (UAE Banks)

For certain programs (notably UAE banks), the burn requires approval via the member's banking app. Instead of entering an OTP code, the user approves the transaction directly in their app.

```
    Customer               Pointspay                  Your Program
       │                      │                            │
       │  (User already       │                            │
       │   authenticated)     │                            │
       │                      │  1. Request approval       │
       │                      │     POST /request-approval │
       │                      │     { memberId, amount,    │
       │                      │       orderRef }           │
       │                      │───────────────────────────>│
       │                      │                            │
       │                      │  2. { approvalId,          │
       │                      │    status: "PENDING" }     │
       │                      │<───────────────────────────│
       │                      │                            │
       │                      │          Push notification │
       │  ┌───────────────────│──────────────────────────>│ Member's
       │  │  3. Approve in    │                            │ banking app
       │  │     banking app   │                            │
       │  └──────────────────>│                            │
       │                      │                            │
       │                      │  4. Callback / webhook     │
       │                      │     { approvalId,          │
       │                      │       status: "APPROVED" } │
       │                      │<───────────────────────────│
       │                      │                            │
       │                      │  5. Redeem points          │
       │                      │     POST /redeem           │
       │                      │     { ..., approvalId }    │
       │                      │───────────────────────────>│
       │                      │                            │
       │                      │  6. { success, ref }       │
       │                      │<───────────────────────────│
       │                      │                            │
```

**Key points**:
- Your program pushes a notification to the member's mobile app.
- The member approves (or rejects) the transaction in the app.
- Your program notifies Pointspay via a **webhook callback** once the approval status changes.
- If the member does not approve within a timeout, the transaction is cancelled.

> **Which pattern applies?** This is determined during onboarding based on your program's security requirements. Most airline loyalty programs use **Pattern A** (OTP) or no OTP at all. Bank programs in the UAE/Middle East typically use **Pattern B** (in-app push).

---

## 7. User Consent

User consent is a critical part of the integration. It ensures that the loyalty member has **explicitly authorized** Pointspay to interact with their loyalty account.

### When Is Consent Required?

| Operation | Consent Required? | Rationale |
|-----------|------------------|-----------|
| **Burn (Redeem)** | **Always** | Spending a member's points is a financial transaction. The member must explicitly authorize it. |
| **Earn (Accrue)** | **Depends on program** | Some programs allow earning with just a member ID or email (no login required). Others require full authentication to prevent unauthorized point accrual. |
| **Reversal (Refund)** | **Never** | Reversals are initiated by Pointspay unilaterally via S2S. No user interaction required. |

### What Constitutes Valid Consent?

Valid consent is obtained when the member completes one of the following:

```
┌──────────────────────────────────────────────────────────────┐
│                    CONSENT MECHANISMS                         │
├──────────────┬───────────────────────────────────────────────┤
│  Mechanism   │  Description                                  │
├──────────────┼───────────────────────────────────────────────┤
│  OAuth2      │  Member logs in at your program's login page  │
│  Login       │  and authorizes Pointspay. The resulting      │
│              │  access_token serves as proof of consent.      │
├──────────────┼───────────────────────────────────────────────┤
│  SAML SSO    │  Member authenticates via your IdP. The       │
│              │  signed SAML assertion serves as proof.        │
├──────────────┼───────────────────────────────────────────────┤
│  OTP /       │  Member enters an OTP or approves a push      │
│  Push        │  notification. This is additional per-txn     │
│  Approval    │  consent on top of the login session.          │
├──────────────┼───────────────────────────────────────────────┤
│  Member ID   │  For EARN-ONLY programs that do not require   │
│  Only        │  login: the member provides their loyalty ID  │
│              │  or email at checkout. This is implicit        │
│              │  consent for earning only.                     │
└──────────────┴───────────────────────────────────────────────┘
```

### Consent Flow Decision Tree

```
                          ┌─────────────────┐
                          │  Is it a BURN   │
                          │  (redeem)?      │
                          └────┬───────┬────┘
                            YES│       │NO (Earn)
                               │       │
                               ▼       ▼
                    ┌──────────────┐  ┌───────────────────────┐
                    │ ALWAYS       │  │ Does program require  │
                    │ require user │  │ login for earn?       │
                    │ login        │  └────┬────────────┬─────┘
                    │ (OAuth2/SAML)│     YES│            │NO
                    └──────┬───────┘       │            │
                           │               ▼            ▼
                           │    ┌────────────┐  ┌──────────────┐
                           │    │ OAuth2/SAML│  │ Member ID or │
                           │    │ login      │  │ email only   │
                           │    │ required   │  │ (no login)   │
                           │    └────────────┘  └──────────────┘
                           │
                           ▼
                  ┌──────────────────┐
                  │ Does program     │
                  │ require OTP /    │
                  │ push approval?   │
                  └───┬──────────┬───┘
                   YES│          │NO
                      ▼          ▼
           ┌──────────────┐  ┌──────────────┐
           │ OTP or push  │  │ Redeem       │
           │ approval     │  │ proceeds     │
           │ before       │  │ directly     │
           │ redeem       │  │ after login  │
           └──────────────┘  └──────────────┘
```

### Earn Without Login — Configuration

If your program allows earning points **without** requiring user login, you must still provide:

1. A way for Pointspay to identify the member (member ID or email entered at checkout).
2. An **Accrue** endpoint that accepts the member identifier and credits points.
3. A **Reverse Accrue** endpoint for refund scenarios.

In this mode, the member is **not** redirected to your login page. Pointspay calls your accrue endpoint directly using the machine token (S2S authentication) and the member identifier.

---

## 8. Required S2S Endpoints

The following table lists all endpoints your program must expose for each integration tier.

| # | Endpoint | Method | Auth | Description | EARN | BURN | ALL |
|---|----------|--------|------|-------------|------|------|-----|
| 1 | **Authorize** | GET | — | OAuth2 authorization page (user-facing redirect) | (1) | ✅ | ✅ |
| 2 | **Token** | POST | Client credentials | OAuth2 token exchange (`authorization_code` and `client_credentials` grants) | ✅ | ✅ | ✅ |
| 3 | **Fetch Member Profile** | GET | Machine Token or Member Token | Return member details (name, email) and/or points balance | ✅ | ✅ | ✅ |
| 4 | **Accrue Points** | POST | Machine Token | Credit points to a member's account | ✅ | — | ✅ |
| 5 | **Redeem Points** | POST | Machine Token | Debit points from a member's account | — | ✅ | ✅ |
| 6 | **Request OTP** | POST | Machine Token | Trigger OTP/push for burn authorization (if applicable) | — | (2) | (2) |
| 7 | **Reverse Accrue** | POST | Machine Token | Undo a prior accrual (partial or full) | ✅ | — | ✅ |
| 8 | **Reverse Redeem** | POST | Machine Token | Undo a prior redemption (partial or full) | — | ✅ | ✅ |

> **(1)** Required only if your program mandates user login for earn. Otherwise, member ID is collected at checkout without redirect.
> **(2)** Required only if your program mandates OTP/push approval for burn transactions.

### Data Requirements Per Endpoint

#### Token Endpoint

| Field | Direction | Description |
|-------|-----------|-------------|
| `grant_type` | Request | `authorization_code` or `client_credentials` |
| `code` | Request | Authorization code (for `authorization_code` grant) |
| `redirect_uri` | Request | Must match the original redirect URI |
| `client_id` | Request | Pointspay's client ID |
| `client_secret` | Request | Pointspay's client secret |
| `audience` | Request | (Optional) Target API audience identifier |
| `access_token` | Response | The issued token |
| `token_type` | Response | Token type (typically `Bearer`) |
| `expires_in` | Response | Token lifetime in seconds |

#### Fetch Member Profile

| Field | Direction | Description |
|-------|-----------|-------------|
| `memberId` | Request | Member's loyalty program identifier |
| `firstName` | Response | Member's first name |
| `lastName` | Response | Member's last name |
| `email` | Response | Member's email address |
| `loyaltyPointsBalance` | Response | Current available points balance |
| `currencyName` | Response | Name of the points currency (e.g., "EuroBonus Points") |

#### Accrue Points

| Field | Direction | Description |
|-------|-----------|-------------|
| `memberId` | Request | Member's loyalty program identifier |
| `loyaltyPoints` | Request | Number of points to credit |
| `orderNumber` | Request | Pointspay order reference |
| `orderDate` | Request | Date of the transaction |
| `productName` | Request | Description of the purchased product/service |
| `operationReference` | Response | Unique ID for this accrual (used for reversal) |
| `balance` | Response | Updated points balance after accrual |

#### Redeem Points

| Field | Direction | Description |
|-------|-----------|-------------|
| `memberId` | Request | Member's loyalty program identifier |
| `loyaltyPoints` | Request | Number of points to debit |
| `orderNumber` | Request | Pointspay order reference |
| `productName` | Request | Description of the purchased product/service |
| `otpCode` | Request | OTP code (if your program requires it) |
| `operationReference` | Response | Unique ID for this redemption (used for reversal) |
| `balance` | Response | Updated points balance after redemption |

#### Request OTP

| Field | Direction | Description |
|-------|-----------|-------------|
| `memberId` | Request | Member's loyalty program identifier |
| `otpSent` | Response | Whether OTP was successfully dispatched |
| `otpReceiver` | Response | Masked phone/email where OTP was sent |
| `otpExpiration` | Response | Expiry time of the OTP |

#### Reverse Accrue

| Field | Direction | Description |
|-------|-----------|-------------|
| `memberId` | Request | Member's loyalty program identifier |
| `loyaltyPoints` | Request | Number of points to reverse |
| `orderNumber` | Request | Original Pointspay order reference |
| `operationReference` | Request | The `operationReference` returned by the original accrual |
| `reversalReference` | Response | Unique ID for this reversal |
| `balance` | Response | Updated points balance after reversal |

#### Reverse Redeem

| Field | Direction | Description |
|-------|-----------|-------------|
| `memberId` | Request | Member's loyalty program identifier |
| `loyaltyPoints` | Request | Number of points to reverse |
| `orderNumber` | Request | Original Pointspay order reference |
| `operationReference` | Request | The `operationReference` returned by the original redemption |
| `reversalReference` | Response | Unique ID for this reversal |
| `balance` | Response | Updated points balance after reversal |

---

## 9. Earn (Accrue) Flow

The earn flow credits points to a member's account after a purchase. This is a **server-to-server** operation with no user interaction.

```
    Pointspay                              Your Program
       │                                       │
       │  1. GET Machine Token                 │
       │     POST /token                       │
       │     { grant_type: client_credentials } │
       │──────────────────────────────────────>│
       │     { access_token: "M-xxx" }         │
       │<──────────────────────────────────────│
       │                                       │
       │  2. Accrue Points                     │
       │     POST /accrue                      │
       │     Authorization: Bearer M-xxx       │
       │     {                                 │
       │       memberId: "FFP-12345",          │
       │       loyaltyPoints: 500,             │
       │       orderNumber: "ORD-789",         │
       │       orderDate: "2026-03-04",        │
       │       productName: "Flight Booking"   │
       │     }                                 │
       │──────────────────────────────────────>│
       │                                       │
       │     {                                 │
       │       operationReference: "A-456",    │
       │       balance: 5500                   │
       │     }                                 │
       │<──────────────────────────────────────│
       │                                       │
```

**Important**: Pointspay persists the `operationReference` returned by your accrue endpoint. This reference is **required** for reversal in case of a refund.

**Idempotency**: If Pointspay sends the same accrue request twice (e.g., due to a network retry) with the same `orderNumber`, your endpoint should return the same `operationReference` without double-crediting points.

---

## 10. Burn (Redeem) Flow

The redeem flow debits points from a member's account to pay for (part of) a purchase.

### 10.1 Standard Redeem (No OTP)

```
    Pointspay                              Your Program
       │                                       │
       │  (Machine token already obtained)     │
       │                                       │
       │  1. Redeem Points                     │
       │     POST /redeem                      │
       │     Authorization: Bearer M-xxx       │
       │     {                                 │
       │       memberId: "FFP-12345",          │
       │       loyaltyPoints: 2000,            │
       │       orderNumber: "ORD-789",         │
       │       productName: "Flight Booking"   │
       │     }                                 │
       │──────────────────────────────────────>│
       │                                       │
       │     {                                 │
       │       operationReference: "R-123",    │
       │       balance: 3000                   │
       │     }                                 │
       │<──────────────────────────────────────│
       │                                       │
```

### 10.2 Redeem with OTP

When your program requires OTP, the flow is a **two-step** process:

```
    Pointspay                              Your Program
       │                                       │
       │  Step 1: Request OTP                  │
       │  POST /request-otp                    │
       │  { memberId: "FFP-12345" }            │
       │──────────────────────────────────────>│
       │                                       │
       │  {                                    │
       │    otpSent: true,                     │
       │    otpReceiver: "+XX****89",          │
       │    otpExpiration: "2026-03-04T..."     │
       │  }                                    │
       │<──────────────────────────────────────│
       │                                       │
       │  ... Customer enters OTP in UI ...    │
       │                                       │
       │  Step 2: Redeem with OTP              │
       │  POST /redeem                         │
       │  {                                    │
       │    memberId: "FFP-12345",             │
       │    loyaltyPoints: 2000,               │
       │    orderNumber: "ORD-789",            │
       │    otpCode: "123456"                  │
       │  }                                    │
       │──────────────────────────────────────>│
       │                                       │
       │  {                                    │
       │    operationReference: "R-123",       │
       │    balance: 3000                      │
       │  }                                    │
       │<──────────────────────────────────────│
       │                                       │
```

> **Behavioral note**: When Pointspay calls the redeem endpoint **without** an OTP code, your program should interpret this as a signal to trigger OTP delivery. When called **with** an OTP code, proceed to redeem.

---

## 11. Split Payment Orchestration

In a split payment, Pointspay orchestrates three operations in sequence:

```
                    SPLIT PAYMENT LIFECYCLE
                    
    Step 1              Step 2              Step 3
    POINTS LEG          CASH LEG            EARN-BACK
    ┌──────────┐        ┌──────────┐        ┌──────────┐
    │  Redeem  │──OK──>│  Charge  │──OK──>│  Accrue  │
    │  Points  │        │  Card    │        │  Points  │
    └──────────┘        └──────────┘        └──────────┘
         │                   │                   │
       FAIL                FAIL                FAIL
         │                   │                   │
         ▼                   ▼                   ▼
    Transaction          Reverse             Logged &
    Cancelled            Redeem              Retried
                         + Cancel
```

### Orchestration Sequence

```
    Pointspay              Your Program          Payment Provider
       │                       │                       │
       │  1. Redeem 2000 pts   │                       │
       │──────────────────────>│                       │
       │  { ref: "R-123" }    │                       │
       │<──────────────────────│                       │
       │                       │                       │
       │  2. Charge $60.00     │                       │
       │──────────────────────────────────────────────>│
       │  { paymentRef: "P-1" }│                       │
       │<──────────────────────────────────────────────│
       │                       │                       │
       │  3. Accrue 300 pts    │                       │
       │  (earn-back on $60)   │                       │
       │──────────────────────>│                       │
       │  { ref: "A-456" }    │                       │
       │<──────────────────────│                       │
       │                       │                       │
       │  Transaction Complete │                       │
       │                       │                       │
```

### Failure Scenarios

| Failure Point | Pointspay Action |
|---------------|------------------|
| **Redeem fails** | Transaction is cancelled. No card charge occurs. Customer is notified. |
| **Card charge fails** (after redeem succeeded) | Pointspay issues an immediate **Reverse Redeem** to return points to the member. Transaction is cancelled. |
| **Accrue fails** (after redeem + card charge succeeded) | The transaction completes (customer received their product). Accrual is logged and **retried automatically**. |

---

## 12. Refunds & Reversals

When a merchant issues a refund, Pointspay **unilaterally reverses** the loyalty operations without any user interaction. This is a **mandatory** requirement — your program **must** expose reversal endpoints.

### Refund Orchestration

```
    Pointspay              Your Program          Payment Provider
       │                       │                       │
       │  REFUND INITIATED     │                       │
       │                       │                       │
       │  1. Reverse Redeem    │                       │
       │  (return points)      │                       │
       │  {                    │                       │
       │    memberId,          │                       │
       │    loyaltyPoints,     │                       │
       │    orderNumber,       │                       │
       │    operationRef:      │                       │
       │      "R-123"          │                       │
       │  }                    │                       │
       │──────────────────────>│                       │
       │  { reversalRef }      │                       │
       │<──────────────────────│                       │
       │                       │                       │
       │  2. Refund card       │                       │
       │  ($60.00)             │                       │
       │──────────────────────────────────────────────>│
       │  { refundRef }        │                       │
       │<──────────────────────────────────────────────│
       │                       │                       │
       │  3. Reverse Accrue    │                       │
       │  (claw back points)   │                       │
       │  {                    │                       │
       │    memberId,          │                       │
       │    loyaltyPoints,     │                       │
       │    orderNumber,       │                       │
       │    operationRef:      │                       │
       │      "A-456"          │                       │
       │  }                    │                       │
       │──────────────────────>│                       │
       │  { reversalRef }      │                       │
       │<──────────────────────│                       │
       │                       │                       │
       │  REFUND COMPLETE      │                       │
       │                       │                       │
```

### Reversal Rules

| Rule | Details |
|------|---------|
| **Unilateral** | Pointspay initiates reversals entirely via S2S. No user consent or interaction is needed. |
| **Mandatory** | Your program **must** support both `Reverse Accrue` and `Reverse Redeem` endpoints for all tiers that include that operation. |
| **Idempotent** | If Pointspay sends the same reversal request twice (same `operationReference` + `orderNumber`), your endpoint must return success without double-reversing. |
| **Partial** | The `loyaltyPoints` in a reversal request may be less than the original operation (partial refund). Your endpoint must support partial reversals. |
| **Full** | A full reversal sends the same `loyaltyPoints` value as the original operation. |
| **Reference required** | Pointspay always sends the `operationReference` from the original earn/burn. Your reversal endpoint must accept this to identify the original transaction. |

### Retry Mechanism

If a reversal call fails (network error, temporary unavailability), Pointspay will **automatically retry** the operation:

```
┌────────────────────────────────────────────────────┐
│              REVERSAL RETRY STRATEGY                │
├────────────────────────────────────────────────────┤
│                                                    │
│  Attempt 1:  Immediate                             │
│       │                                            │
│     FAIL                                           │
│       │                                            │
│  Attempt 2:  Automatic retry (scheduled)           │
│       │                                            │
│     FAIL                                           │
│       │                                            │
│  Attempt N:  Retries continue on schedule          │
│       │                                            │
│  All retries exhausted → Alert & manual review     │
│                                                    │
└────────────────────────────────────────────────────┘
```

> **Important**: Because Pointspay retries reversals, your endpoint **must be idempotent**. Receiving the same reversal request multiple times must not result in multiple reversals.

---

## 13. Error Handling & Idempotency

### Expected Error Response Format

Your endpoints should return errors in a structured format. The exact schema is agreed during onboarding, but must include at minimum:

| Field | Description |
|-------|-------------|
| `errorCode` | Machine-readable error code |
| `errorMessage` | Human-readable description |

### Common Error Scenarios

| Scenario | Expected Behavior |
|----------|-------------------|
| **Invalid member ID** | Return an error indicating the member was not found. |
| **Insufficient balance** | Return an error with the current balance so Pointspay can inform the customer. |
| **Expired OTP** | Return an error indicating OTP expiry. Pointspay will request a new OTP. |
| **Invalid OTP** | Return an error. Pointspay will prompt the customer to re-enter. |
| **Duplicate operation** (same `orderNumber`) | Return the same `operationReference` as the original call. Do **not** process a second time. |
| **Duplicate reversal** (same `operationReference`) | Return success. Do **not** reverse a second time. |
| **Original operation not found** (for reversal) | Return an error indicating the referenced operation was not found. |
| **Service unavailable** | Return HTTP 503. Pointspay will retry according to retry policy. |

### Idempotency Requirements

All mutating endpoints (Accrue, Redeem, Reverse Accrue, Reverse Redeem) **must be idempotent** on the combination of:

- `orderNumber` (for accrue and redeem)
- `operationReference` (for reversals)

This means:
- If Pointspay sends the same accrue request twice with the same `orderNumber`, your endpoint should return the same `operationReference` and **not** credit points a second time.
- If Pointspay sends the same reversal request twice with the same `operationReference`, your endpoint should return success and **not** reverse points a second time.

---

## 14. Onboarding Checklist

Use this checklist to track what your program needs to provide during onboarding.

### Credentials & Configuration

| # | Item | Description | Provided? |
|---|------|-------------|-----------|
| 1 | **Client ID** (OAuth2) | For the `authorization_code` grant (user consent) | ☐ |
| 2 | **Client Secret** (OAuth2) | Paired with the client ID above | ☐ |
| 3 | **S2S Client ID** | For the `client_credentials` grant (machine token) | ☐ |
| 4 | **S2S Client Secret** | Paired with the S2S client ID | ☐ |
| 5 | **Redirect URI whitelist** | Pointspay's callback URL added to your OAuth2 config | ☐ |
| 6 | **API Base URL** (Production) | Base URL for all S2S endpoints | ☐ |
| 7 | **API Base URL** (Sandbox/Staging) | Base URL for testing | ☐ |
| 8 | **API Key / Subscription Key** | If your API gateway requires an additional key | ☐ |
| 9 | **mTLS Certificates** | If your program requires mutual TLS for S2S calls | ☐ |

### Endpoint URLs

| # | Endpoint | URL | Status |
|---|----------|-----|--------|
| 1 | Authorize (OAuth2) | | ☐ |
| 2 | Token (OAuth2) | | ☐ |
| 3 | Fetch Member Profile | | ☐ |
| 4 | Accrue Points | | ☐ |
| 5 | Redeem Points | | ☐ |
| 6 | Request OTP (if applicable) | | ☐ |
| 7 | Reverse Accrue | | ☐ |
| 8 | Reverse Redeem | | ☐ |

### Security & Compliance

| # | Item | Description | Status |
|---|------|-------------|--------|
| 1 | **User consent model** | Confirmed: OAuth2 / SAML / OTP / Push | ☐ |
| 2 | **OTP required for burn?** | Yes / No | ☐ |
| 3 | **Login required for earn?** | Yes / No | ☐ |
| 4 | **Idempotency** | All mutating endpoints are idempotent on `orderNumber` / `operationReference` | ☐ |
| 5 | **Partial reversals** | Reversal endpoints support partial amounts | ☐ |
| 6 | **mTLS** | If required, certificates exchanged | ☐ |

### Testing

| # | Item | Description | Status |
|---|------|-------------|--------|
| 1 | **Sandbox environment** | Available and accessible | ☐ |
| 2 | **Test member accounts** | At least 2 test accounts with known balance | ☐ |
| 3 | **End-to-end test** | Successful OAuth2 login → profile → accrue → redeem → reverse | ☐ |
| 4 | **Error scenarios tested** | Insufficient balance, invalid OTP, duplicate requests | ☐ |
| 5 | **Technical contact** | Name and email for integration support | ☐ |

---

## Appendix A: Integration Modes Summary

```
┌────────────────────────────────────────────────────────────────────┐
│                     INTEGRATION MODE MATRIX                        │
├──────────────┬─────────┬──────────┬───────────┬───────────────────┤
│  Capability  │  EARN   │  BURN    │  ALL      │  Notes            │
├──────────────┼─────────┼──────────┼───────────┼───────────────────┤
│  OAuth2 Auth │  (opt.) │   ✅     │   ✅      │  User login       │
│  Machine Tok │   ✅    │   ✅     │   ✅      │  S2S calls        │
│  Profile     │   ✅    │   ✅     │   ✅      │  Balance + info   │
│  Accrue      │   ✅    │   —      │   ✅      │  Credit points    │
│  Redeem      │   —     │   ✅     │   ✅      │  Debit points     │
│  OTP         │   —     │  (opt.)  │  (opt.)   │  If required      │
│  Rev. Accrue │   ✅    │   —      │   ✅      │  Refund earn      │
│  Rev. Redeem │   —     │   ✅     │   ✅      │  Refund burn      │
└──────────────┴─────────┴──────────┴───────────┴───────────────────┘
```

## Appendix B: Sequence Diagram — Full Refund on Split Payment

This shows the complete refund of an order that was originally paid with a split (cash + points).

```
    Merchant              Pointspay              Your Program        Payment Provider
       │                      │                       │                     │
       │  1. Request refund   │                       │                     │
       │     for ORD-789      │                       │                     │
       │─────────────────────>│                       │                     │
       │                      │                       │                     │
       │                      │  2. Reverse Redeem    │                     │
       │                      │     (return 2000 pts) │                     │
       │                      │     ref: "R-123"      │                     │
       │                      │──────────────────────>│                     │
       │                      │  { OK }               │                     │
       │                      │<──────────────────────│                     │
       │                      │                       │                     │
       │                      │  3. Refund card $60   │                     │
       │                      │────────────────────────────────────────────>│
       │                      │  { OK }               │                     │
       │                      │<────────────────────────────────────────────│
       │                      │                       │                     │
       │                      │  4. Reverse Accrue    │                     │
       │                      │     (claw back 300)   │                     │
       │                      │     ref: "A-456"      │                     │
       │                      │──────────────────────>│                     │
       │                      │  { OK }               │                     │
       │                      │<──────────────────────│                     │
       │                      │                       │                     │
       │  5. Refund confirmed │                       │                     │
       │<─────────────────────│                       │                     │
       │                      │                       │                     │
```

**Result**: The member's points balance is restored to its pre-purchase state. The card payment is refunded. Any earn-back points are clawed back.

---

*For questions or to begin the onboarding process, contact the Pointspay Integration Team.*
