# Pointspay — Loyalty Orchestrator API Integration Guide

> 🚧 **Status: PLANNED, not yet available.** This API is in design and partner evaluation. The
> endpoints described below are **not callable yet**. Sandbox and production availability will be
> announced. This guide is shared for early integration planning and feedback, not for live use.

---

## Table of Contents

1. [Overview](#1-overview)
2. [Scenarios](#2-scenarios)
3. [Consent Model](#3-consent-model)
4. [Per-Program Capability](#4-per-program-capability)
5. [Authentication (Two Layers)](#5-authentication-two-layers)
   - 5.1 [Partner Authentication](#51-partner-authentication)
   - 5.2 [Member Context](#52-member-context)
6. [Endpoints](#6-endpoints)
7. [Example A: Earn](#7-example-a-earn)
8. [Example B: Burn](#8-example-b-burn)
9. [Example C: Earn and Burn Together (Split)](#9-example-c-earn-and-burn-together-split)
10. [Status Lifecycle](#10-status-lifecycle)
11. [Webhooks (Signed JWT)](#11-webhooks-signed-jwt)
12. [Reversals & Refunds](#12-reversals--refunds)
13. [Errors & Idempotency](#13-errors--idempotency)
14. [Onboarding Checklist](#14-onboarding-checklist)

---

## 1. Overview

`/loyalty/v1` is a REST API to **earn and burn loyalty points across four airline programs through
one contract**: Flying Blue (`FLB`), Etihad Guest (`ETHWL`), SAS EuroBonus (`SAS`), and Miles & More
(`MAM`). It exposes each program's authentication and redemption behaviour through one uniform
interface, and supports **earn** (accrue), **burn** (redeem), **split** (earn plus burn on one
order), full or partial reversal, status query, reconciliation, and signed-JWT webhooks.

**This API moves points, not money.** The cash leg is processed outside it, and no cardholder data
traverses `/loyalty/v1` (it adds no PCI scope).

| | |
|---|---|
| **Base URL (prod)** | `https://api.pointspay.com/loyalty/v1` |
| **Base URL (sandbox)** | `https://uat-api.pointspay.com/loyalty/v1` |
| **Partner auth** | `X-API-Key` plus `X-Partner-Code` (optional mTLS in production) |
| **Member auth** | `X-Member-Token` from a one-time member context, on member-scoped calls |
| **Format** | JSON. Integer point amounts. `{code, message, key}` error model |

> **Maturity.** Per-program *behaviours* in this guide (earn, no-redirect burn, OTP, redirect) are
> verified against Pointspay's production loyalty integrations. The `/loyalty/v1` surface is defined by
> this guide and the OpenAPI contract. Sandbox availability is delivered on a mutually agreed schedule.

---

## 2. Scenarios

The API supports three order scenarios:

```text
┌────────────────────────────────────────────────────────────┐
│                     SCENARIO 1: EARN ONLY                  │
│   Cash-only order. Points are EARNED on the amount.         │
│   Cash leg: €100.00    Earned: 500 pts    Burned: 0         │
├────────────────────────────────────────────────────────────┤
│             SCENARIO 2: SPLIT (EARN + BURN)                │
│   Points burned for part. Earned on the cash part.          │
│   Cash leg: €60.00     Burned: 2000 pts   Earned: 300       │
├────────────────────────────────────────────────────────────┤
│                     SCENARIO 3: FULL BURN                  │
│   Paid 100% with points. No cash, no earn-back.             │
│   Cash leg: €0.00      Burned: 5000 pts   Earned: 0         │
└────────────────────────────────────────────────────────────┘
```

Worked examples for each: [Earn](#7-example-a-earn) · [Burn](#8-example-b-burn) ·
[Split](#9-example-c-earn-and-burn-together-split).

---

## 3. Consent Model

A member is **not** logged in twice. One consent covers the whole transaction. Extra steps appear
**only** when the program itself mandates them (per-program detail in §4).

| Operation | Member login required? | Per-burn re-verification? |
|-----------|------------------------|----------------------------|
| **Burn (Redeem)** | **Always** (once) | Only if the program demands it: SAS = OTP every burn, M&M = redirect every burn, FLB/Etihad = none (Etihad OTP only if configured). |
| **Earn (Accrue)** | **Program-dependent.** Many programs allow earn with just a member id (no login). | Never. |
| **Reversal / Refund** | **Never.** Initiated via the partner key, no user. | Never. |

```text
                      ┌─────────────────┐
                      │  BURN or EARN?  │
                      └────┬───────┬────┘
                      BURN │       │ EARN
                           ▼       ▼
              ┌──────────────┐   ┌──────────────────────────┐
              │ Member login │   │ Program requires login    │
              │ ONCE         │   │ for earn?                  │
              │ (OAuth/SAML/ │   └────┬─────────────────┬────┘
              │  B2B token)  │     YES│                 │NO
              └──────┬───────┘        ▼                 ▼
                     │        ┌──────────────┐  ┌──────────────────┐
                     │        │ Member login │  │ member id only,  │
                     │        │ ONCE         │  │ no login         │
                     │        └──────────────┘  └──────────────────┘
                     ▼
          ┌────────────────────┐
          │ Program demands     │  SAS→OTP, M&M→redirect, FLB/ETH→no
          │ per-burn step?      │
          └───┬────────────┬────┘
           YES│            │NO
              ▼            ▼
   ┌────────────────┐  ┌────────────────────┐
   │ OTP / redirect │  │ burn completes      │
   │ for THIS burn  │  │ server-side (1-click)│
   └────────────────┘  └────────────────────┘
```

The single login establishes a **member context** (§5.2) that is reused for many operations,
including both legs of a split, so the earn-back never triggers a second login. See
[Example C](#9-example-c-earn-and-burn-together-split).

---

## 4. Per-Program Capability

Capability uses **two orthogonal axes plus one derived flag**, because a single label can't capture
the central nuance: *a program can need a redirect to authenticate but no redirect to burn.* Query it
at `GET /loyalty/v1/programs`.

- **`authMode`**: how member context is established, once. `MEMBER_OAUTH_REDIRECT`,
  `MEMBER_SAML_SSO`, or `B2B_MACHINE_TOKEN`.
- **`burnStep`**: what each burn needs beyond the call. `NONE`, `OTP_CHALLENGE`, or
  `EXTERNAL_REDIRECT`.
- **`oneClickEligible`**: derived per member by `POST /redemptions/quote`. `true` only when a valid
  member context exists **and** `burnStep == NONE`.

| Program | `authMode` (one-time) | `burnStep` (each burn) | Earn without member login? | Net after auth |
|---------|----------------------|------------------------|----------------------------|----------------|
| **Flying Blue** (`FLB`) | `MEMBER_OAUTH_REDIRECT` | `NONE` | Program-dependent | **No-redirect burn** |
| **Etihad Guest** (`ETHWL`) | `MEMBER_SAML_SSO` | `NONE` or `OTP_CHALLENGE`¹ | Program-dependent | **No-redirect burn** (OTP if configured) |
| **SAS EuroBonus** (`SAS`) | `B2B_MACHINE_TOKEN` | `OTP_CHALLENGE` | Program-dependent | No-redirect, **OTP every burn** |
| **Miles & More** (`MAM`) | `MEMBER_OAUTH_REDIRECT` | `EXTERNAL_REDIRECT` | Program-dependent | **Redirect every burn** (MCheckout) |

¹ Etihad's per-burn OTP is governed by that program's configuration. The capability descriptor flags
this with `burnStepConditional: true`, and a member's **quote** always returns the concrete answer.

No program is zero-redirect for a brand-new member. Each needs a one-time login. After that: Flying
Blue and Etihad burn server-side with no redirect (Etihad subject to its OTP config). SAS challenges
an OTP every burn. Miles & More needs a per-transaction MCheckout redirect. This is never hard-coded.
`quote` returns `oneClickEligible` and the concrete next step per member.

---

## 5. Authentication (Two Layers)

There are **two independent layers**. Keeping them separate is why a member is never logged in twice:
the partner layer has **no user**, and the member layer logs the user in **once** (per §3).

```text
   ┌─────────────────────────────────────────────────────────────┐
   │  LAYER 1: PARTNER AUTH  (client → Pointspay)                 │
   │  Machine-to-machine. NO user, NO login screen.               │
   │  X-API-Key + X-Partner-Code  (optional mTLS in production)   │
   │  Reused on every call, for the life of the credential.       │
   └─────────────────────────────────────────────────────────────┘
                              ▲ wraps every request
   ┌─────────────────────────────────────────────────────────────┐
   │  LAYER 2: MEMBER CONTEXT  (the user → their program)         │
   │  The ONLY login. Done ONCE per member (§3).                  │
   │  Reused for the whole transaction (burn AND earn-back).      │
   │  Re-verification only if the program demands it (OTP/redirect)│
   └─────────────────────────────────────────────────────────────┘
```

### 5.1 Partner Authentication

The client authenticates to `/loyalty/v1` with a **static API key**, the same model as Pointspay's
existing public API, so there is nothing new to build:

| Header | Value |
|--------|-------|
| `X-API-Key` | Secret API key (issued at onboarding). **Never exposed to the browser.** |
| `X-Partner-Code` | Partner identifier (the audience the key is scoped to). |

```bash
curl https://api.pointspay.com/loyalty/v1/programs \
  -H "X-API-Key: $POINTSPAY_API_KEY" \
  -H "X-Partner-Code: acme-travel"
```

**Key points**

- This authenticates the **calling server**, not a user. There is **no OAuth dance and no login
  screen** at this layer. The key is presented on every call and reused indefinitely.
- The key carries its **scopes** (`loyalty.read`, `loyalty.earn`, `loyalty.burn`, `loyalty.reverse`),
  set at onboarding (least privilege).
- **Production hardening (optional):** present a **client certificate (mTLS)** alongside the key.
  Recommended for production given the irreversibility of burns. Not required in sandbox.
- The key is **redacted** from Pointspay logs and error output. Store it as a server secret, and
  rotate it via the onboarding contact.

### 5.2 Member Context

To act on a member's points, first establish a **member context**, once, via a single endpoint that
hides each program's mechanics (OAuth for FLB/MAM, SAML SSO for Etihad, machine token for SAS B2B).
No SAML or OAuth implementation is required on the client side.

```bash
# Establish member context (once per member + program)
curl -X POST https://api.pointspay.com/loyalty/v1/auth/member-context \
  -H "X-API-Key: $POINTSPAY_API_KEY" -H "X-Partner-Code: acme-travel" \
  -H "Content-Type: application/json" \
  -d '{ "programCode": "FLB" }'   # redirectCompletionUrl is optional (see below)
```

The response is one of two shapes:

```jsonc
// (a) Ready: a member token was minted (e.g. SAS B2B, or a token already held)
{ "nextStep": "READY", "contextRef": "ctx_8Jk2p", "memberToken": "eyJ...", "memberRef": "mbr_FLB_77x", "expiresAt": "2026-06-30T13:00:00Z" }

// (b) Redirect: send the user's browser once to authenticate. The token is delivered to your backend
{ "nextStep": "AUTH_REDIRECT_REQUIRED", "contextRef": "ctx_8Jk2p", "redirectUrl": "https://api.pointspay.com/loyalty/v1/auth/redirect/ctx_8Jk2p", "expiresAt": "2026-06-30T12:15:00Z" }
```

#### Completing a redirect: how the client knows the user is back

Open `redirectUrl` in a web-view, in-app browser tab (iOS `ASWebAuthenticationSession`, Android
Custom Tabs), or the system browser. The member authenticates. Pointspay completes the program's
OAuth/SAML exchange **server-side**, mints the member token, and marks the context `READY`.

`redirectCompletionUrl` is **optional**:

- **Provide it** if you want the member's browser sent back to a link your app claims (mechanism A
  below). Pointspay 302-redirects there with `?contextRef=…&status=completed` on completion.
- **Omit it** to detect completion by polling (B) or by webhook (C). Pointspay then shows a default
  "you can close this page" screen when the member finishes.

Detect completion (and obtain the token) via any of:

```text
   App / web-view                Pointspay                 Program login
      │  open redirectUrl ─────────────────────────────────────>│
      │  member authenticates ─────────────────────────────────>│
      │                            │<── OAuth/SAML callback ──────│   (server-side, token minted)
      │  ── (A) if redirectCompletionUrl set: 302 → your link (contextRef, status) → close web-view
      │  ── (B) poll GET /auth/member-context/{contextRef} → READY
      │  ── (C) member-context.ready webhook (signed JWT) → carries memberToken to your backend
      │
      │  token to your backend (server-to-server): webhook (C, push) OR POST .../token (pull)
      │  POST /auth/member-context/{contextRef}/token ─────────>│  { memberToken, memberRef }
      │<───────────────────────────│
```

1. **Deep link / universal link (recommended for mobile).** Set `redirectCompletionUrl` to a link
   your app claims: an Android App Link / iOS Universal Link, or a custom scheme such as
   `acme://loyalty/callback`. The OS hands control back to your app, which dismisses the web-view.
2. **Poll (works everywhere, and is the deep-link fallback).** Poll
   `GET /auth/member-context/{contextRef}` until `status` is `READY` (or `EXPIRED`). Suggested
   interval about 2 s, with a timeout at `expiresAt`. Most robust for embedded web-views.
3. **`member-context.ready` webhook (push).** A signed JWT sent to your backend carrying the
   `memberToken` and `memberRef` directly (§11). No `POST .../token` call needed.

> **Security: the token never travels through the browser.** The redirect carries only `contextRef`
> and `status`. The `memberToken` reaches your **backend** only, either as a claim in the signed
> `member-context.ready` webhook (push) **or** by calling
> `POST /auth/member-context/{contextRef}/token` over your authenticated partner channel (pull).
> Either way it stays out of the web-view, URL history, deep-link payloads, and logs. This is the
> same reason OAuth returns a code, not a token, in the redirect.

Thereafter the **member token** is presented on member-scoped calls:

| Header | When |
|--------|------|
| `X-Member-Token` | On balance, quote, burn, and OTP-submit. Proves the **member session** (separate from the partner key). |

Member-context endpoints: `GET /auth/member-context/{contextRef}` (status: `PENDING_REDIRECT` /
`READY` / `EXPIRED`, used for polling above), `POST /auth/member-context/{contextRef}/token` (obtain
the member token once `READY`, and refresh it later, the pull alternative to the webhook),
`DELETE …/token` (revoke), and `GET …/introspect` (inspect validity, scope, expiry). **One member
context is reused for many operations**, including both legs of a split.

---

## 6. Endpoints

All under `https://api.pointspay.com/loyalty/v1` (prod) / `https://uat-api.pointspay.com/loyalty/v1`
(sandbox). Every call carries `X-API-Key` and `X-Partner-Code`.

| # | Endpoint | Method | Member token? | Idempotency? | Purpose | EARN | BURN |
|---|----------|--------|---------------|--------------|---------|------|------|
| 1 | `/programs`, `/programs/{code}` | GET | — | — | Catalog + capability descriptor | ✅ | ✅ |
| 2 | `/auth/member-context` | POST | — | — | Establish member context (once) | (1) | ✅ |
| 3 | `/members/{ref}/balance` | GET | ✅ | — | Member balance & eligibility | ✅ | ✅ |
| 4 | `/redemptions/quote` | POST | ✅ | — | Cost, balance, `oneClickEligible`, next step | — | ✅ |
| 5 | `/accruals` | POST | (1) | ✅ | **Earn** points | ✅ | — |
| 6 | `/redemptions` | POST | ✅ | ✅ | **Burn** points | — | ✅ |
| 7 | `/redemptions/{operationReference}/otp` | POST | ✅ | ✅ | Submit OTP (SAS always, Etihad if configured) | — | (2) |
| 8 | `/redemptions/{operationReference}`, `/accruals/{operationReference}` | GET | — | — | Status / lifecycle (resolves M&M two-phase) | ✅ | ✅ |
| 9 | `/accruals/{operationReference}/reverse`, `/redemptions/{operationReference}/reverse` | POST | — | ✅ | Reverse the points leg (full or partial) | ✅ | ✅ |
| 10 | `/redemptions?from=&to=` , `/accruals?from=&to=` | GET | — | — | List/query for reconciliation | ✅ | ✅ |
| 11 | Webhooks (signed JWT) | — | — | — | `member-context.ready` + settled-state notifications | ✅ | ✅ |

> **(1)** Member context is required for earn only if the program mandates login for earn. Otherwise
> earn is server-to-server with the member id. **(2)** Only when the program demands OTP.

---

## 7. Example A: Earn

Earn (accrue) points for a member with a single server-to-server call. The member authenticated once
(or, for programs that allow earn without login, just the member id is passed).

```text
   Client                                     Pointspay /loyalty/v1
        │ 1. Establish member context (once) ───────>│  { READY, memberRef, memberToken }   (only if the program requires login for earn)
        │<───────────────────────────────────────────│
        │ 2. Accrue points  POST /accruals ─────────>│  { operationReference, status: ACCRUED }
        │<───────────────────────────────────────────│
```

**Request**

```bash
curl -X POST https://api.pointspay.com/loyalty/v1/accruals \
  -H "X-API-Key: $POINTSPAY_API_KEY" -H "X-Partner-Code: acme-travel" \
  -H "X-Member-Token: $MEMBER_TOKEN" \
  -H "X-Idempotency-Key: 9f1c3b7e-earn-0001-ord-789" \
  -H "Content-Type: application/json" \
  -d '{
        "programCode": "FLB",
        "memberRef": "mbr_FLB_77x",
        "points": 500,
        "partnerReference": "ORD-2026-0099887",
        "productName": "Hotel reservation (3 nights)"
      }'
```

**Response** `200 OK`

```json
{
  "operationReference": "acc_FLB_1a2b",
  "programCode": "FLB",
  "memberRef": "mbr_FLB_77x",
  "status": "ACCRUED",
  "points": 500,
  "balanceAfter": 49000,
  "reversedPoints": 0,
  "partnerReference": "ORD-2026-0099887",
  "createdAt": "2026-06-30T12:05:00Z"
}
```

> Earn is idempotent on `X-Idempotency-Key`. A retry with the same body returns this same response,
> so points are never double-credited.

---

## 8. Example B: Burn

Burn points to pay for (part of) an order (Scenario 3, full burn). The member logs in **once**, then
the burn follows the program's `burnStep`.

**What is a quote, and why use it?** `POST /redemptions/quote` is an optional **pre-flight check**.
For a given member and points amount it returns: the exact points **cost**, the member's **balance**,
whether the burn is **one-click right now** (`oneClickEligible`), the concrete **`nextStep`**
(`BURN_NOW` / `OTP_REQUIRED` / `REDIRECT_REQUIRED` / `AUTH_REQUIRED`), and an opaque **`quoteRef`**.
Use it to (1) show the member the cost and render the right action **before** they commit, and
(2) echo the `quoteRef` on the burn so pricing and eligibility **can't drift** between quote and burn
(a stale quote returns `422`). It's optional (you can burn directly) but recommended.

```text
   Client                                     Pointspay /loyalty/v1
        │  1. Establish member context (once) ──────>│  { READY, memberRef, memberToken }
        │<───────────────────────────────────────────│
        │  2. Quote (optional pre-flight) ──────────>│  { quoteRef, oneClickEligible, nextStep }
        │<───────────────────────────────────────────│
        │  3. Burn  POST /redemptions ──────────────>│
        │     200 REDEEMED      ── FLB / Etihad(OTP-off): one-click, done
        │     202 PENDING_VERIFICATION:               │
        │        · OTP_CHALLENGE   → POST /{opRef}/otp → 200 REDEEMED   (SAS, Etihad OTP-on)
        │        · EXTERNAL_REDIRECT → user→MCheckout → GET /{opRef}    (M&M)
        │<───────────────────────────────────────────│
```

**Burn request**

```bash
curl -X POST https://api.pointspay.com/loyalty/v1/redemptions \
  -H "X-API-Key: $POINTSPAY_API_KEY" -H "X-Partner-Code: acme-travel" \
  -H "X-Member-Token: $MEMBER_TOKEN" \
  -H "X-Idempotency-Key: 7a2d-burn-0002-ord-789" \
  -H "Content-Type: application/json" \
  -d '{ "programCode": "FLB", "memberRef": "mbr_FLB_77x", "points": 12000, "quoteRef": "q_FLB_abc", "partnerReference": "ORD-2026-0099887" }'
```

**One-click response** (Flying Blue / Etihad OTP-off) `200 OK`

```json
{ "operationReference": "op_FLB_5b21", "programCode": "FLB", "status": "REDEEMED", "points": 12000, "balanceAfter": 36500, "reversedPoints": 0, "verification": null }
```

**OTP response** (SAS, or Etihad with OTP on) `202 Accepted`

```json
{
  "operationReference": "op_SAS_9c40", "programCode": "SAS", "status": "PENDING_VERIFICATION", "points": 9000,
  "verification": { "type": "OTP_CHALLENGE", "otpReceiver": "+46 70 *** ** 12", "otpExpiresAt": "2026-06-30T12:10:00Z" }
}
```

```bash
# Submit the code the member received
curl -X POST https://api.pointspay.com/loyalty/v1/redemptions/op_SAS_9c40/otp \
  -H "X-API-Key: $POINTSPAY_API_KEY" -H "X-Partner-Code: acme-travel" \
  -H "X-Member-Token: $MEMBER_TOKEN" -H "X-Idempotency-Key: 7a2d-otp-0003" \
  -H "Content-Type: application/json" -d '{ "otpCode": "482913" }'
# → 200 { "operationReference": "op_SAS_9c40", "status": "REDEEMED", "balanceAfter": 22000 }
```

**Redirect response** (Miles & More) `202 Accepted`

```json
{
  "operationReference": "op_MAM_7e88", "programCode": "MAM", "status": "PENDING_VERIFICATION", "points": 15000,
  "verification": { "type": "EXTERNAL_REDIRECT", "redirectUrl": "https://mcheckout.miles-and-more.com/checkout/op_MAM_7e88" }
}
```

Send the member's browser to `redirectUrl`. Resolve the terminal state by polling
`GET /redemptions/op_MAM_7e88` or by awaiting the [webhook](#11-webhooks-signed-jwt).

---

## 9. Example C: Earn and Burn Together (Split)

The flagship: the member burns points for part of the order **and** earns points on the cash part,
within **one** member context (Scenario 2). **Single login.** The cash leg is sequenced between the
two Pointspay calls.

```text
   Client                        Pointspay /loyalty/v1        PSP / card
        │ 1. member-context (ONCE) ───>│  { memberRef, memberToken }
        │<─────────────────────────────│                          │
        │ 2. quote (burn 2000) ───────>│  { quoteRef, oneClickEligible } │
        │<─────────────────────────────│                          │
        │ 3. BURN 2000 pts ───────────>│  200 REDEEMED  op=op_burn │      ← points leg
        │<─────────────────────────────│                          │
        │ 4. Charge €60.00 cash ─────────────────────────────────>│      ← cash leg (separate)
        │<─────────────────────────────────────────────────────────│
        │ 5. EARN-BACK 300 pts ───────>│  200 ACCRUED   op=acc_back│      ← earn leg, SAME member token
        │<─────────────────────────────│                          │
        │ 6. Order complete            │                          │
```

**Step 1. One member context, reused for both legs:**

```bash
curl -X POST https://api.pointspay.com/loyalty/v1/auth/member-context \
  -H "X-API-Key: $POINTSPAY_API_KEY" -H "X-Partner-Code: acme-travel" \
  -H "Content-Type: application/json" \
  -d '{ "programCode": "FLB" }'
# → { "nextStep": "READY", "memberRef": "mbr_FLB_77x", "memberToken": "<MEMBER_TOKEN>", ... }
```

**Step 3. Burn the points leg** (`X-Member-Token` = the token from step 1):

```bash
curl -X POST https://api.pointspay.com/loyalty/v1/redemptions \
  -H "X-API-Key: $POINTSPAY_API_KEY" -H "X-Partner-Code: acme-travel" \
  -H "X-Member-Token: $MEMBER_TOKEN" -H "X-Idempotency-Key: split-burn-ord-790" \
  -H "Content-Type: application/json" \
  -d '{ "programCode": "FLB", "memberRef": "mbr_FLB_77x", "points": 2000, "partnerReference": "ORD-2026-0100100" }'
# → 200 { "operationReference": "op_burn_3f", "status": "REDEEMED", "balanceAfter": 46500 }
```

**Step 4. Charge €60.00 on the card** (handled by the PSP, not Pointspay).

**Step 5. Earn-back on the cash part, *same* member token, no second login:**

```bash
curl -X POST https://api.pointspay.com/loyalty/v1/accruals \
  -H "X-API-Key: $POINTSPAY_API_KEY" -H "X-Partner-Code: acme-travel" \
  -H "X-Member-Token: $MEMBER_TOKEN" -H "X-Idempotency-Key: split-earn-ord-790" \
  -H "Content-Type: application/json" \
  -d '{ "programCode": "FLB", "memberRef": "mbr_FLB_77x", "points": 300, "partnerReference": "ORD-2026-0100100", "relatedOperationReference": "op_burn_3f" }'
# → 200 { "operationReference": "acc_back_9a", "status": "ACCRUED", "balanceAfter": 46800 }
```

**Orchestration and failure handling** (the client sequences the three legs):

| Failure point | Recommended action |
|---------------|--------------------|
| **Burn fails** | Do not charge the card. Surface the error to the user. |
| **Card charge fails** (after burn) | Call `POST /redemptions/{op_burn}/reverse` to return the points, and cancel the order. |
| **Earn-back fails** (after burn + charge) | Complete the order (the user has their reservation). Retry the accrual. It is idempotent on `X-Idempotency-Key`. |

> Both legs ran under the **one** member token from step 1. The member authenticated exactly once.
> The only time an extra step appears is if the program demands a per-burn OTP/redirect (§3).

---

## 10. Status Lifecycle

Every earn and burn carries a `status`. Read the current state from
`GET /redemptions/{operationReference}` or `GET /accruals/{operationReference}`, or receive it via
webhook (§11).

**Burn (redemption) statuses**

| Status | Meaning | Terminal |
|--------|---------|----------|
| `PENDING_VERIFICATION` | Awaiting an OTP submit or a redirect return. | — |
| `REDEEMED` | Points burned successfully. | ✅ |
| `REDEMPTION_FAILED` | The burn did not complete. | ✅ |
| `PARTIALLY_REVERSED` | Some (not all) burned points returned. | — (more reversals possible) |
| `REVERSED` | All burned points returned. | ✅ |
| `REVERSAL_PENDING` / `REVERSAL_FAILED` | A reversal is in progress / a reversal failed. | — |
| `EXPIRED` | A pending verification timed out. | ✅ |

**Earn (accrual) statuses**

| Status | Meaning | Terminal |
|--------|---------|----------|
| `ACCRUED` | Points credited successfully. | ✅ |
| `ACCRUAL_FAILED` | The accrual did not complete. | ✅ |
| `PARTIALLY_REVERSED` | Some (not all) earned points clawed back. | — |
| `REVERSED` | All earned points clawed back. | ✅ |
| `REVERSAL_PENDING` / `REVERSAL_FAILED` | In progress / failed. | — |

**Tracking (partial) reversals.** Each operation exposes the same shape as the V5 transaction status:

| Field | Meaning | V5 equivalent |
|-------|---------|---------------|
| `points` | Original amount. | `total_amount` |
| `reversedPoints` | Sum of successfully reversed points so far. | `total_refunded` |
| `reversals[]` | Each reversal attempt: `reversalReference`, `points`, `status` (`PENDING`/`SUCCESS`/`FAILED`), `createdAt`. | `refund_attempts[]` |
| `statusUpdates[]` | `timestamp`, `message`, `source` (`LOYALTY`/`INTERNAL`) for progress/error notes. | `status_updates[]` |

`status` follows `reversedPoints`: `0` means `REDEEMED`/`ACCRUED`, `0 < reversedPoints < points` means
`PARTIALLY_REVERSED`, and `== points` means `REVERSED`. Poll the operation (or a specific
`reversalReference`) until each reversal settles (`PENDING → SUCCESS | FAILED`).

---

## 11. Webhooks (Signed JWT)

Pointspay POSTs **signed JWTs (compact JWS)** to your registered webhook URL. Two event families,
both verified the same way:

- **`member-context.ready`**: sent after a redirect auth completes. Carries the `memberToken` and
  `memberRef` to your backend (the push alternative to `POST .../token`, §5.2).
- **operation settled-state**: sent when an earn/burn settles (`REDEEMED`, `REDEMPTION_FAILED`,
  `ACCRUED`, `ACCRUAL_FAILED`, `PARTIALLY_REVERSED`, `REVERSED`, `REVERSAL_FAILED`, `EXPIRED`).

**Verify exactly like Pointspay payment tokens**: standard JWT/JWKS verification per
[jwt.io](https://jwt.io) / RFC 7519, with ready-made code for Node.js, Python, PHP, and Java in
[`JWT_SIGNATURE_VERIFICATION.md`](./JWT_SIGNATURE_VERIFICATION.md). The only loyalty-specific values:

| | Value |
|---|---|
| Issuer (`iss`) | `https://api.pointspay.com/loyalty/v1`. **Distinct** from the payment issuer (`…/v4`), so loyalty key rotation is isolated. Verify exactly. |
| JWKS | `https://api.pointspay.com/loyalty/v1/.well-known/jwks.json` (via OIDC discovery). Pick the key by `kid` from the JWS header. |
| Algorithms | `RS256` / `RS384` / `RS512` (whitelist these three, reject `alg: none`). |
| Audience (`aud`) | your partner code. |

**Claim fields**, compact keys following the same convention as Pointspay payment tokens (e.g. V5's
`stat` / `oid`):

| Claim | Meaning |
|-------|---------|
| `iss`, `aud`, `iat`, `exp` | Standard JWT claims: issuer, audience, issued-at, expiry. |
| `jti` | Unique event id. Dedup on it (anti-replay). Also reject if `exp` is past or `iat` is older than 5 min. |
| `evt` | Event type: `operation.settled` or `member-context.ready`. |
| `opr` | Operation reference: the earn/burn this event is about. |
| `knd` | Operation kind: `EARN` or `BURN`. |
| `prg` | Program code: `FLB` / `ETHWL` / `SAS` / `MAM`. |
| `stat` | Settled status (see §10). |
| `pts`, `rpts` | Points (original) and reversed points (cumulative). |
| `pref` | Partner reference (your order reference). |
| `oat` | When the change occurred. |

```json
{
  "iss": "https://api.pointspay.com/loyalty/v1", "aud": "acme-travel", "jti": "evt_4c91a0",
  "iat": 1782820000, "exp": 1782820300, "evt": "operation.settled",
  "opr": "op_MAM_7e88", "knd": "BURN", "prg": "MAM",
  "stat": "REDEEMED", "pts": 15000, "rpts": 0,
  "pref": "ORD-2026-0100021", "oat": "2026-06-30T12:08:42Z"
}
```

The `member-context.ready` event instead carries `ctx` (context ref), `mrf` (member ref), `mtk`
(member token), and `prg`. Respond `2xx` to acknowledge. Pointspay retries with backoff on any non-2xx.

---

## 12. Reversals & Refunds

Reversals are initiated via the partner key, with **no member interaction**, and may be **full or
partial**.

**Full reversal** (omit `points` to reverse the full remaining amount):

```bash
curl -X POST https://api.pointspay.com/loyalty/v1/redemptions/op_burn_3f/reverse \
  -H "X-API-Key: $POINTSPAY_API_KEY" -H "X-Partner-Code: acme-travel" \
  -H "X-Idempotency-Key: rev-burn-ord-790" \
  -H "Content-Type: application/json" -d '{ "reason": "Order cancelled." }'
# → 200 { "operationReference": "op_burn_3f", "status": "REVERSED", "points": 2000, "reversedPoints": 2000, ... }
```

**Partial reversal** mirrors a partial refund by reversing only the affected share. Partials
accumulate up to the original, and the operation sits at `PARTIALLY_REVERSED` until fully reversed:

```bash
# return 800 of 2000 burned points (e.g. 1 of 3 nights refunded)
curl -X POST https://api.pointspay.com/loyalty/v1/redemptions/op_burn_3f/reverse \
  -H "X-API-Key: $POINTSPAY_API_KEY" -H "X-Partner-Code: acme-travel" \
  -H "X-Idempotency-Key: rev-burn-partial-1" \
  -H "Content-Type: application/json" -d '{ "points": 800, "reason": "Partial cancellation (1 of 3 nights)." }'
```

```json
{
  "operationReference": "op_burn_3f",
  "status": "PARTIALLY_REVERSED",
  "points": 2000,
  "reversedPoints": 800,
  "balanceAfter": 45300,
  "reversals": [
    { "reversalReference": "rev_7c", "points": 800, "status": "SUCCESS", "createdAt": "2026-06-30T15:20:00Z" }
  ]
}
```

A later reversal of the remaining 1200 points moves `status` to `REVERSED` (`reversedPoints == points`).

| Rule | Detail |
|------|--------|
| **Points only** | Reverses the points leg. **Any fiat refund (full or partial) is handled outside this API**, matched to the points reversal by `partnerReference` / `operationReference`. |
| **Partial** | Supply `points` no greater than the remaining amount (`points − reversedPoints`). Multiple partials accumulate, and `status` stays `PARTIALLY_REVERSED` until fully reversed (see §10). |
| **Both directions** | `…/redemptions/{op}/reverse` returns burned points. `…/accruals/{op}/reverse` claws back earned points. |
| **Idempotent** | Each call is idempotent on `X-Idempotency-Key`, so a retry never double-reverses. |
| **Program-dependent** | The reverse path exists for all four programs. Per-program reversibility and any time window are confirmed in the partnership SLA. A non-reversible case returns `422`. |

For a split refund, reverse the burn and the earn-back independently by their `operationReference`s.
Each can itself be partial.

---

## 13. Errors & Idempotency

**Error model.** Every error is `{code, message, key}`:

```json
{ "code": "LOYALTY_INSUFFICIENT_BALANCE", "message": "Member balance is insufficient for the requested redemption.", "key": "loyalty.redemption.insufficient_balance", "traceId": "…" }
```

Switch on `code`. Localize via `key`. Quote `traceId` to support.

**Idempotency.** Required on every mutating call (`/accruals`, `/redemptions`, `…/otp`, `…/reverse`)
via the **`X-Idempotency-Key`** header (at least 16 chars):

| Situation | Result |
|-----------|--------|
| Same key, **same body** | The **cached original response** is returned (safe to retry). |
| Same key, **different body** | `409 Conflict`. |
| Key **still processing** | `425 Too Early` (honor `Retry-After`). |

Keys are unique per partner, retained 24h, and SHA-256-bound to the request body. This makes the
irreversible burn safe to retry over flaky networks **without double-spending** a member's points.

---

## 14. Onboarding Checklist

| # | Item | Description | Provided? |
|---|------|-------------|-----------|
| 1 | **API key** | `X-API-Key` (partner auth) | ☐ |
| 2 | **Partner code** | `X-Partner-Code` identifier | ☐ |
| 3 | **Scopes** | `loyalty.read` / `loyalty.earn` / `loyalty.burn` / `loyalty.reverse` (least privilege) | ☐ |
| 4 | **mTLS certificate** (optional, prod) | Client cert for production hardening | ☐ |
| 5 | **Webhook URL** | HTTPS endpoint for `member-context.ready` and settled-state signed-JWT events | ☐ |
| 6 | **Programs** | Which of FLB / ETHWL / SAS / MAM to enable | ☐ |
| 7 | **Redirect completion URL** (optional) | App-claimed link for browser return after a member-context redirect | ☐ |
| 8 | **Sandbox access** | UAT base URL and test member accounts with known balances | ☐ |
| 9 | **End-to-end test** | member-context → quote → burn → earn-back → partial reverse → full reverse, webhook verified | ☐ |

---

*To begin onboarding, contact the Pointspay Integration Team. Companion documents:
[`JWT_SIGNATURE_VERIFICATION.md`](./JWT_SIGNATURE_VERIFICATION.md) (webhook/token verification) and
the OpenAPI 3.1 contract `loyalty-orchestrator-api.yaml`.*
