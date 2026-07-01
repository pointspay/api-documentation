# Pointspay — Loyalty Orchestrator API Integration Guide

> 🚧 This API is PLANNED and not yet callable, shared for early integration planning and feedback.

It moves points, not money and holds no cardholder data, so it adds no PCI scope.

| | |
|---|---|
| Base URL (prod) | `https://api.pointspay.com/loyalty/v1` |
| Base URL (sandbox) | `https://uat-api.pointspay.com/loyalty/v1` |
| Partner auth | `X-API-Key` plus `X-Partner-Code` (optional mTLS in production) |
| Member auth | `X-Member-Token` from a one-time member context, on member-scoped calls |
| Format | JSON. Integer point amounts. `{code, message, key}` error model |

---

## Table of Contents

- [Pointspay — Loyalty Orchestrator API Integration Guide](#pointspay--loyalty-orchestrator-api-integration-guide)
  - [Table of Contents](#table-of-contents)
  - [1. Consent Model](#1-consent-model)
  - [2. Per-Program Capability](#2-per-program-capability)
  - [3. Authentication (Two Layers)](#3-authentication-two-layers)
    - [3.1 Partner Authentication](#31-partner-authentication)
    - [3.2 Member Context](#32-member-context)
  - [4. Endpoints](#4-endpoints)
  - [5. Example A: Burn](#5-example-a-burn)
  - [6. Example B: Earn](#6-example-b-earn)
  - [7. Example C: Earn and Burn Together (Split)](#7-example-c-earn-and-burn-together-split)
  - [8. Status Lifecycle](#8-status-lifecycle)
  - [9. Webhooks (Signed JWT)](#9-webhooks-signed-jwt)
  - [10. Reversals \& Refunds](#10-reversals--refunds)
  - [11. Errors \& Idempotency](#11-errors--idempotency)
  - [12. Onboarding Checklist](#12-onboarding-checklist)

---

## 1. Consent Model

A member is not logged in twice. One consent covers the whole transaction. Extra steps appear
only when the program itself mandates them (per-program detail in §2).

| Operation | Member login required? | Per-burn re-verification? |
|-----------|------------------------|----------------------------|
| Burn (Redeem) | Always (once) | Only if the program demands a per-burn OTP or redirect. The member's quote returns the concrete step. |
| Earn (Accrue) | Program-dependent. Many programs allow earn with just a member id (no login). | Never. |
| Reversal / Refund | Never. Initiated via the partner key, no user. | Never. |

The single login establishes a member context (§3.2) reused for the whole transaction, including
both legs of a split. See [Example C](#7-example-c-earn-and-burn-together-split).

---

## 2. Per-Program Capability

The catalog is dynamic: `GET /loyalty/v1/programs` returns the live set and, per program, a capability
descriptor. The rows below are examples of that descriptor, not the full catalog.

One flow fits every program. You always do the same three steps: `quote` → `burn` → follow
`nextStep`. The orchestrator handles member sign-in behind one endpoint, so the client never builds
a program's login. The only per-program question is: does a burn need an extra step and which one?

"One-click" means the burn finishes in a single `POST /redemptions` call: no OTP, no redirect, the
member does nothing extra. The quote tells you, before you burn, whether that applies:

- `oneClickEligible` (from `quote`): `true` when the burn will complete in one call, with no OTP
  and no redirect. (This holds when a valid member context exists and the program's `burnStep` is `NONE`.)
- `burnStep` (per program): what a burn needs beyond the call. `NONE` (one-click), `OTP_CHALLENGE`
  (an OTP), `EXTERNAL_REDIRECT` (a browser redirect), or a combination applied in order (SAS needs
  both). When a step is needed, the burn response carries the concrete OTP target or `redirectUrl`.

| Program (example) | Extra step per burn? | Runtime `nextStep` | What you call |
| --- | --- | --- | --- |
| Flying Blue (`FLB`) | Yes. A redirect each burn | `REDIRECT_REQUIRED` | `quote → burn → follow nextStep` |
| Etihad Guest (`ETH`) | No, unless the program enables OTP | `BURN_NOW` or `OTP_REQUIRED` | `quote → burn → follow nextStep` |
| SAS EuroBonus (`SAS`) | Yes. A redirect and an OTP | `REDIRECT_REQUIRED` then `OTP_REQUIRED` | `quote → burn → follow nextStep` |
| Miles & More (`MAM`) | Yes. A redirect each burn | `REDIRECT_REQUIRED` | `quote → burn → follow nextStep` |
| *(other programs)* | Per the descriptor | from `quote` | `quote → burn → follow nextStep` |

The last column never changes. Per-program behaviour lives in the data (`burnStep`, `nextStep`), not in
your integration.

Each `nextStep` maps to one client action. A burn can need more than one, so follow `nextStep`
until the burn is `REDEEMED` (SAS returns `REDIRECT_REQUIRED`, then `OTP_REQUIRED`):

| `nextStep` | Your next action |
| --- | --- |
| `BURN_NOW` | One call, no OTP and no redirect. The burn completes immediately. |
| `OTP_REQUIRED` | Burn, then submit the OTP the member receives (`POST /redemptions/{op}/otp`). |
| `REDIRECT_REQUIRED` | Burn, then send the member to the `redirectUrl` in the response to approve this burn. |
| `AUTH_REQUIRED` | The member is not signed in. Establish a member context (§3.2), then re-quote. |

Your code reads capabilities from the descriptor, `GET /loyalty/v1/programs/{code}`:

```json
{
  "programCode": "SAS",
  "displayName": "SAS EuroBonus",
  "burnStep": ["EXTERNAL_REDIRECT", "OTP_CHALLENGE"],
  "burnStepConditional": false,
  "earnRequiresMemberLogin": false,
  "reversible": true,
  "reversalWindowDays": 180
}
```

---

## 3. Authentication (Two Layers)

The client builds one thing: a static API key. Authentication has two independent layers:

- Layer 1, partner auth (client → Pointspay): machine-to-machine, no user, no login screen.
  `X-API-Key` + `X-Partner-Code`, reused on every call for the life of the credential.
- Layer 2, member context (user → their program): the only login, done once per member (§1),
  reused for the whole transaction. Re-verification only if the program demands it (OTP or redirect).

### 3.1 Partner Authentication

A static API key, scoped to `loyalty.read` / `loyalty.earn` / `loyalty.burn` / `loyalty.reverse`.

| Header | Value |
|--------|-------|
| `X-API-Key` | Secret API key (issued at onboarding). Never exposed to the browser. |
| `X-Partner-Code` | Partner identifier (the audience the key is scoped to). |

```bash
curl https://api.pointspay.com/loyalty/v1/programs \
  -H "X-API-Key: $POINTSPAY_API_KEY" \
  -H "X-Partner-Code: acme-travel"
```

### 3.2 Member Context

To act on a member's points, first establish a member context (once) via a single endpoint. The
client implements no program-specific login.

```bash
# Establish member context (once per member + program)
curl -X POST https://api.pointspay.com/loyalty/v1/auth/member-context \
  -H "X-API-Key: $POINTSPAY_API_KEY" -H "X-Partner-Code: acme-travel" \
  -H "Content-Type: application/json" \
  -d '{ "programCode": "FLB" }'   # redirectCompletionUrl is optional
```

The response is one of two shapes:

```jsonc
// (a) Ready: a member token is available immediately (no redirect needed)
{ "nextStep": "READY", "contextRef": "ctx_8Jk2p", "memberToken": "eyJ...", "memberRef": "mbr_FLB_77x", "expiresAt": "2026-06-30T13:00:00Z" }

// (b) Redirect: send the user's browser once to authenticate. The token is delivered to your backend
{ "nextStep": "AUTH_REDIRECT_REQUIRED", "contextRef": "ctx_8Jk2p", "redirectUrl": "https://api.pointspay.com/loyalty/v1/auth/redirect/ctx_8Jk2p", "expiresAt": "2026-06-30T12:15:00Z" }
```

When the response is `AUTH_REDIRECT_REQUIRED`, open `redirectUrl` for the member to sign in. Detect
completion by polling `GET /auth/member-context/{contextRef}` (its `status` is `PENDING_REDIRECT` until
`READY`) or by the `member-context.ready` webhook (§9). Optionally set `redirectCompletionUrl` to
return the browser to your app. The `memberToken` is delivered only to your backend, never through the
browser.

Thereafter the member token is presented on member-scoped calls (`X-Member-Token`): balance,
quote, burn and OTP-submit. It proves the member session, separate from the partner key.

Member-context endpoints: `GET /auth/member-context/{contextRef}` (status: `PENDING_REDIRECT` /
`READY` / `EXPIRED`, used for polling above), `POST /auth/member-context/{contextRef}/token` (obtain
the token once `READY` and refresh it later), `DELETE …/token` (revoke) and `GET …/introspect`
(inspect validity, scope, expiry). One member context serves the whole transaction, including both
legs of a split.

---

## 4. Endpoints

All paths are under the prod/sandbox base URLs shown at the top. Every call carries `X-API-Key` and
`X-Partner-Code`.

| # | Endpoint | Method | Member token? | Idempotency? | Purpose | EARN | BURN |
|---|----------|--------|---------------|--------------|---------|------|------|
| 1 | `/programs`, `/programs/{code}` | GET | — | — | Catalog + capability descriptor | ✅ | ✅ |
| 2 | `/auth/member-context` | POST | — | — | Establish member context (once) | ✅ | ✅ |
| 3 | `/members/{ref}/balance` | GET | ✅ | — | Member balance & eligibility | ✅ | ✅ |
| 4 | `/redemptions/quote` | POST | ✅ | — | Cost, balance, `oneClickEligible`, next step | — | ✅ |
| 5 | `/accruals` | POST | if login | ✅ | Earn points | ✅ | — |
| 6 | `/redemptions` | POST | ✅ | ✅ | Burn points | — | ✅ |
| 7 | `/redemptions/{operationReference}/otp` | POST | ✅ | ✅ | Submit OTP for a burn | — | ✅ |
| 8 | `/redemptions/{operationReference}`, `/accruals/{operationReference}` | GET | — | — | Status / lifecycle (resolves two-phase burns) | ✅ | ✅ |
| 9 | `/accruals/{operationReference}/reverse`, `/redemptions/{operationReference}/reverse` | POST | — | ✅ | Reverse the points leg (full or partial) | ✅ | ✅ |
| 10 | `/redemptions?from=&to=` , `/accruals?from=&to=` | GET | — | — | List/query for reconciliation | ✅ | ✅ |
| 11 | Webhooks (signed JWT) | — | — | — | `member-context.ready` + settled-state notifications | ✅ | ✅ |

---

## 5. Example A: Burn

Burn points to pay for part or all of an order. The member signs in once, then follow the runtime
`nextStep` until the burn is `REDEEMED`.

Quote (optional pre-flight). `POST /redemptions/quote` returns the point cost, balance,
`oneClickEligible`, a `quoteRef` and the `nextStep` (§2 explains each value; a burn can chain steps,
e.g. SAS returns a redirect then an OTP). Echo `quoteRef` on the burn to pin pricing. A stale quote
returns `422`.

```text
   Client                                     Pointspay /loyalty/v1
        │  1. Establish member context (once) ──────>│  { READY, memberRef, memberToken }
        │<───────────────────────────────────────────│
        │  2. Quote (optional pre-flight) ──────────>│  { quoteRef, oneClickEligible, nextStep }
        │<───────────────────────────────────────────│
        │  3. Burn  POST /redemptions ──────────────>│
        │     Follow nextStep until 200 REDEEMED:     │
        │        · BURN_NOW          → done in one call
        │        · REDIRECT_REQUIRED → member → redirectUrl, then re-check status
        │        · OTP_REQUIRED      → POST /{opRef}/otp
        │     SAS chains REDIRECT_REQUIRED then OTP_REQUIRED
        │<───────────────────────────────────────────│
```

Burn request

```bash
curl -X POST https://api.pointspay.com/loyalty/v1/redemptions \
  -H "X-API-Key: $POINTSPAY_API_KEY" -H "X-Partner-Code: acme-travel" \
  -H "X-Member-Token: $MEMBER_TOKEN" \
  -H "X-Idempotency-Key: 7a2d-burn-0002-ord-789" \
  -H "Content-Type: application/json" \
  -d '{ "programCode": "ETH", "memberRef": "mbr_ETH_77x", "points": 12000, "quoteRef": "q_ETH_abc", "partnerReference": "ORD-2026-0099887" }'
```

One-click response (`BURN_NOW`) `200 OK`

```json
{ "operationReference": "op_ETH_5b21", "programCode": "ETH", "status": "REDEEMED", "points": 12000, "balanceAfter": 36500, "reversedPoints": 0, "verification": null }
```

When the program needs a step, the same call returns `202` with a `verification` and the next `nextStep`.

Redirect response (FLB, MAM) `202 Accepted`

```json
{
  "operationReference": "op_FLB_7e88", "programCode": "FLB", "status": "PENDING_VERIFICATION", "nextStep": "REDIRECT_REQUIRED", "points": 12000,
  "verification": { "type": "EXTERNAL_REDIRECT", "redirectUrl": "https://api.pointspay.com/loyalty/v1/redemptions/op_FLB_7e88/redirect" }
}
```

Send the member to `redirectUrl`, then re-check status by polling `GET /redemptions/op_FLB_7e88` or the
[webhook](#9-webhooks-signed-jwt).

Redirect + OTP response (SAS) `202 Accepted`

SAS needs both. The burn returns the redirect first:

```json
{
  "operationReference": "op_SAS_9c40", "programCode": "SAS", "status": "PENDING_VERIFICATION", "nextStep": "REDIRECT_REQUIRED", "points": 9000,
  "verification": { "type": "EXTERNAL_REDIRECT", "redirectUrl": "https://api.pointspay.com/loyalty/v1/redemptions/op_SAS_9c40/redirect" }
}
```

After the member returns from the redirect, the same operation advances to an OTP:

```json
// GET /redemptions/op_SAS_9c40 (or the webhook) now returns:
{ "operationReference": "op_SAS_9c40", "status": "PENDING_VERIFICATION", "nextStep": "OTP_REQUIRED",
  "verification": { "type": "OTP_CHALLENGE", "otpReceiver": "+46 70 *  12", "otpExpiresAt": "2026-06-30T12:10:00Z" } }
```

Submit the OTP to finish:

```bash
curl -X POST https://api.pointspay.com/loyalty/v1/redemptions/op_SAS_9c40/otp \
  -H "X-API-Key: $POINTSPAY_API_KEY" -H "X-Partner-Code: acme-travel" \
  -H "X-Member-Token: $MEMBER_TOKEN" -H "X-Idempotency-Key: 7a2d-otp-0003" \
  -H "Content-Type: application/json" -d '{ "otpCode": "482913" }'
# → 200 { "operationReference": "op_SAS_9c40", "status": "REDEEMED", "balanceAfter": 22000 }
```

---

## 6. Example B: Earn

Earn (accrue) points for a member with a single server-to-server call.

```text
   Client                                     Pointspay /loyalty/v1
        │ 1. Establish member context (once) ───────>│  { READY, memberRef, memberToken }   (only if the program requires login for earn)
        │<───────────────────────────────────────────│
        │ 2. Accrue points  POST /accruals ─────────>│  { operationReference, status: ACCRUED }
        │<───────────────────────────────────────────│
```

Request

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

> Earn without member login. When the program's descriptor has `earnRequiresMemberLogin: false`,
> omit the `X-Member-Token` header and identify the member by `memberRef` in the body (the call above,
> minus that one header). When it is `true`, establish a member context first (step 1) and send the
> token as shown.

Response `200 OK`

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

## 7. Example C: Earn and Burn Together (Split)

The flagship: within one member context, the member burns points on one leg and earns
points on another. Both legs run under the same member token, so the member signs in only once.

```text
   Client                          Pointspay /loyalty/v1
        │ 1. member-context (ONCE) ───>│  { memberRef, memberToken }
        │<─────────────────────────────│
        │ 2. quote (burn 2000) ───────>│  { quoteRef, oneClickEligible }
        │<─────────────────────────────│
        │ 3. BURN 2000 pts ───────────>│  200 REDEEMED  op=op_burn   ← points leg
        │<─────────────────────────────│
        │ 4. EARN 300 pts ────────────>│  200 ACCRUED   op=acc_back  ← earn leg, SAME token
        │<─────────────────────────────│
        │ 5. Order complete            │
```

Step 1. Establish the member context:

```bash
curl -X POST https://api.pointspay.com/loyalty/v1/auth/member-context \
  -H "X-API-Key: $POINTSPAY_API_KEY" -H "X-Partner-Code: acme-travel" \
  -H "Content-Type: application/json" \
  -d '{ "programCode": "ETH" }'
# → { "nextStep": "READY", "memberRef": "mbr_ETH_77x", "memberToken": "<MEMBER_TOKEN>", ... }
```

Step 3. Burn the points leg (`X-Member-Token` = the token from step 1):

```bash
curl -X POST https://api.pointspay.com/loyalty/v1/redemptions \
  -H "X-API-Key: $POINTSPAY_API_KEY" -H "X-Partner-Code: acme-travel" \
  -H "X-Member-Token: $MEMBER_TOKEN" -H "X-Idempotency-Key: split-burn-ord-790" \
  -H "Content-Type: application/json" \
  -d '{ "programCode": "ETH", "memberRef": "mbr_ETH_77x", "points": 2000, "partnerReference": "ORD-2026-0100100" }'
# → 200 { "operationReference": "op_burn_3f", "status": "REDEEMED", "balanceAfter": 46500 }
```

Step 4. Earn-back, *same* member token, no second login:

```bash
curl -X POST https://api.pointspay.com/loyalty/v1/accruals \
  -H "X-API-Key: $POINTSPAY_API_KEY" -H "X-Partner-Code: acme-travel" \
  -H "X-Member-Token: $MEMBER_TOKEN" -H "X-Idempotency-Key: split-earn-ord-790" \
  -H "Content-Type: application/json" \
  -d '{ "programCode": "ETH", "memberRef": "mbr_ETH_77x", "points": 300, "partnerReference": "ORD-2026-0100100", "relatedOperationReference": "op_burn_3f" }'
# → 200 { "operationReference": "acc_back_9a", "status": "ACCRUED", "balanceAfter": 46800 }
```

Failure handling (the client sequences the two legs):

| Failure point | Recommended action |
|---------------|--------------------|
| Burn fails | Surface the error to the user. Do not proceed. |
| Earn-back fails (after burn) | The burn stands. Retry the accrual. It is idempotent on `X-Idempotency-Key`. |

> Both legs ran under the one member token from step 1. The member authenticated exactly once.
> The only time an extra step appears is if the program demands a per-burn OTP/redirect (§1).

---

## 8. Status Lifecycle

Every earn and burn carries a `status`. Read the current state from
`GET /redemptions/{operationReference}` or `GET /accruals/{operationReference}`, or receive it via
webhook (§9).

Burn (redemption) statuses

| Status | Meaning | Terminal |
|--------|---------|----------|
| `PENDING_VERIFICATION` | Awaiting an OTP submit or a redirect return. | — |
| `REDEEMED` | Points burned successfully. | ✅ |
| `REDEMPTION_FAILED` | The burn did not complete. | ✅ |
| `PARTIALLY_REVERSED` | Some (not all) burned points returned. | — (more reversals possible) |
| `REVERSED` | All burned points returned. | ✅ |
| `REVERSAL_PENDING` / `REVERSAL_FAILED` | A reversal is in progress / a reversal failed. | — |
| `EXPIRED` | A pending verification timed out. | ✅ |

Earn (accrual) statuses

| Status | Meaning | Terminal |
|--------|---------|----------|
| `ACCRUED` | Points credited successfully. | ✅ |
| `ACCRUAL_FAILED` | The accrual did not complete. | ✅ |
| `PARTIALLY_REVERSED` | Some (not all) earned points clawed back. | — |
| `REVERSED` | All earned points clawed back. | ✅ |
| `REVERSAL_PENDING` / `REVERSAL_FAILED` | In progress / failed. | — |

Tracking (partial) reversals. Each operation exposes the same shape as the V5 transaction status:

| Field | Meaning | V5 equivalent |
|-------|---------|---------------|
| `points` | Original amount. | `total_amount` |
| `reversedPoints` | Sum of successfully reversed points so far. | `total_refunded` |
| `reversals[]` | Each reversal attempt: `reversalReference`, `points`, `status` (`PENDING`/`SUCCESS`/`FAILED`), `createdAt`. | `refund_attempts[]` |
| `statusUpdates[]` | `timestamp`, `message`, `source` (`LOYALTY`/`INTERNAL`) for progress/error notes. | `status_updates[]` |

`status` follows `reversedPoints`: `0` means `REDEEMED`/`ACCRUED`, `0 < reversedPoints < points` means
`PARTIALLY_REVERSED` and `== points` means `REVERSED`. Poll the operation (or a specific
`reversalReference`) until each reversal settles (`PENDING → SUCCESS | FAILED`).

---

## 9. Webhooks (Signed JWT)

Pointspay POSTs signed JWTs (compact JWS) to your registered webhook URL. Two event families,
both verified the same way:

- `member-context.ready`: sent after a redirect auth completes. Carries the `memberToken` and
  `memberRef` to your backend (the push alternative to `POST .../token`, §3.2).
- operation settled-state: sent when an earn/burn settles (`REDEEMED`, `REDEMPTION_FAILED`,
  `ACCRUED`, `ACCRUAL_FAILED`, `PARTIALLY_REVERSED`, `REVERSED`, `REVERSAL_FAILED`, `EXPIRED`).

Verify exactly like Pointspay payment tokens: standard JWT/JWKS verification per
[jwt.io](https://jwt.io) / RFC 7519, with ready-made code for Node.js, Python, PHP and Java in
[`JWT_SIGNATURE_VERIFICATION.md`](./JWT_SIGNATURE_VERIFICATION.md). The only loyalty-specific values:

| | Value |
|---|---|
| Issuer (`iss`) | `https://api.pointspay.com/loyalty/v1`. Distinct from the payment issuer (`…/v4`), so loyalty key rotation is isolated. Verify exactly. |
| JWKS | `https://api.pointspay.com/loyalty/v1/.well-known/jwks.json` (via OIDC discovery). Pick the key by `kid` from the JWS header. |
| Algorithms | `RS256` / `RS384` / `RS512` (whitelist these three, reject `alg: none`). |
| Audience (`aud`) | your partner code. |

Claim fields, compact keys following the same convention as Pointspay payment tokens (e.g. V5's
`stat` / `oid`):

| Claim | Meaning |
|-------|---------|
| `iss`, `aud`, `iat`, `exp` | Standard JWT claims: issuer, audience, issued-at, expiry. |
| `jti` | Unique event id. Dedup on it (anti-replay). Also reject if `exp` is past or `iat` is older than 5 min. |
| `evt` | Event type: `operation.settled` or `member-context.ready`. |
| `opr` | Operation reference: the earn/burn this event is about. |
| `knd` | Operation kind: `EARN` or `BURN`. |
| `prg` | Program code (e.g. `FLB`, `ETH`), as returned by `GET /programs`. |
| `stat` | Settled status (see §8). |
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
(member token) and `prg`. Respond `2xx` to acknowledge. Pointspay retries with backoff on any non-2xx.

---

## 10. Reversals & Refunds

Reversals are initiated via the partner key, with no member interaction and may be full or
partial.

Full reversal (omit `points` to reverse the full remaining amount):

```bash
curl -X POST https://api.pointspay.com/loyalty/v1/redemptions/op_burn_3f/reverse \
  -H "X-API-Key: $POINTSPAY_API_KEY" -H "X-Partner-Code: acme-travel" \
  -H "X-Idempotency-Key: rev-burn-ord-790" \
  -H "Content-Type: application/json" -d '{ "reason": "Order cancelled." }'
# → 200 { "operationReference": "op_burn_3f", "status": "REVERSED", "points": 2000, "reversedPoints": 2000, ... }
```

Partial reversal mirrors a partial refund by reversing only the affected share. Partials
accumulate up to the original and the operation sits at `PARTIALLY_REVERSED` until fully reversed:

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
| Points only | Reverses the points leg. Any fiat refund (full or partial) is handled outside this API, matched to the points reversal by `partnerReference` / `operationReference`. |
| Partial | Supply `points` no greater than the remaining amount (`points − reversedPoints`). Multiple partials accumulate and `status` stays `PARTIALLY_REVERSED` until fully reversed (see §8). |
| Both directions | `…/redemptions/{op}/reverse` returns burned points. `…/accruals/{op}/reverse` claws back earned points. |
| Idempotent | Each call is idempotent on `X-Idempotency-Key`, so a retry never double-reverses. |
| Program-dependent | The reverse path exists for every program. Per-program reversibility and any time window are exposed in the capability descriptor (`reversible`, `reversalWindowDays`) and confirmed in the partnership SLA. A non-reversible case returns `422`. |

For a split refund, reverse the burn and the earn-back independently by their `operationReference`s.
Each can itself be partial.

---

## 11. Errors & Idempotency

Error model. Every error is `{code, message, key}`:

```json
{ "code": "LOYALTY_INSUFFICIENT_BALANCE", "message": "Member balance is insufficient for the requested redemption.", "key": "loyalty.redemption.insufficient_balance", "traceId": "…" }
```

Switch on `code`. Localize via `key`. Quote `traceId` to support.

Idempotency. Required on every mutating call (`/accruals`, `/redemptions`, `…/otp`, `…/reverse`)
via the `X-Idempotency-Key` header (at least 16 chars):

| Situation | Result |
|-----------|--------|
| Same key, same body | The cached original response is returned (safe to retry). |
| Same key, different body | `409 Conflict`. |
| Key still processing | `425 Too Early` (honor `Retry-After`). |

Keys are unique per partner, retained 24h and SHA-256-bound to the request body. This makes the
irreversible burn safe to retry over flaky networks without double-spending a member's points.

---

## 12. Onboarding Checklist

| # | Item | Description | Provided? |
|---|------|-------------|-----------|
| 1 | API key | `X-API-Key` (partner auth) | ☐ |
| 2 | Partner code | `X-Partner-Code` identifier | ☐ |
| 3 | Scopes | `loyalty.read` / `loyalty.earn` / `loyalty.burn` / `loyalty.reverse` (least privilege) | ☐ |
| 4 | mTLS certificate (optional, prod) | Client cert for production hardening | ☐ |
| 5 | Webhook URL | HTTPS endpoint for `member-context.ready` and settled-state signed-JWT events | ☐ |
| 6 | Programs | Which programs to enable (from the `GET /programs` catalog) | ☐ |
| 7 | Redirect completion URL (optional) | App-claimed link for browser return after a member-context redirect | ☐ |
| 8 | Sandbox access | UAT base URL and test member accounts with known balances | ☐ |
| 9 | End-to-end test | member-context → quote → burn → earn-back → partial reverse → full reverse, webhook verified | ☐ |

---

*To begin onboarding, contact the Pointspay Integration Team. Companion documents:
[`JWT_SIGNATURE_VERIFICATION.md`](./JWT_SIGNATURE_VERIFICATION.md) (webhook/token verification) and
the OpenAPI 3.1 contract `loyalty-orchestrator-api.yaml`.*
