# Pointspay — Loyalty Orchestrator API Integration Guide

> 🚧 **Planned, not yet callable.** Shared for integration planning and feedback. The contract is stable enough to
> start building against the mock (see [R5](#r5-sandbox-and-mock)).

**One unified API for every loyalty program.** Link a member, show their balance, quote, burn, earn and reverse points
with the same calls for Flying Blue, Etihad Guest, SAS EuroBonus, Miles & More and every program added later.

Programs differ only in data: the program descriptor's capability flags, and the `nextStep` in each response. If you
find yourself writing `if program == …`, the docs are wrong. Tell us.

You keep the cash and the customer. Pointspay moves only points, so this API holds no card data and adds no PCI scope.

| | |
|---|---|
| Base URL | `https://api.pointspay.com/loyalty/v1` (planned) |
| Mock | Local: run the contract with Prism ([R5](#r5-sandbox-and-mock)). Hosted: `https://lorch-sandbox.pointspay.com/loyalty/v1` (planned) |
| Contract | [`loyalty-orchestrator-api.yaml`](./loyalty-orchestrator-api.yaml) (OpenAPI 3.1, with examples for every response) |
| Partner auth | `X-API-Key` + `X-Partner-Code`, or an OAuth2 client-credentials token. Optional mTLS |
| Member auth | `X-Member-Token` on member-scoped calls |
| Format | JSON. Points are integers. Money is `{value, currency}` in minor units |

---

## Contents

- [0. Start here](#0-start-here)
- Recipes
  - [1. List programs at checkout](#1-list-programs-at-checkout)
  - [2. Link a member](#2-link-a-member)
  - [3. Check a member number](#3-check-a-member-number)
  - [4. Balance, tier, benefits, expiry](#4-balance-tier-benefits-expiry)
  - [5. Show earnings before booking](#5-show-earnings-before-booking)
  - [6. Pay with points](#6-pay-with-points)
  - [7. Earn on a booking](#7-earn-on-a-booking)
  - [8. Cancel, amend, correct](#8-cancel-amend-correct)
  - [9. Track status](#9-track-status)
  - [10. Reconcile and settle](#10-reconcile-and-settle)
  - [11. Handle failure](#11-handle-failure)
  - [12. Secure and go live](#12-secure-and-go-live)
- Reference
  - [R1. Status lifecycles](#r1-status-lifecycles)
  - [R2. Webhooks](#r2-webhooks)
  - [R3. Versioning and deprecation](#r3-versioning-and-deprecation)
  - [R4. Performance targets](#r4-performance-targets)
  - [R5. Sandbox and mock](#r5-sandbox-and-mock)

---

## 0. Start here

### Three objects

| Object | What it is | Key |
|---|---|---|
| Program | A loyalty program and what it supports (the descriptor) | `programCode` |
| Member link | One member of one program, linked to you | `memberRef` |
| Operation | A burn (`BURN`) or an earn (`EARN`), with its reversals | `operationRef` |

Every other call either creates one of these or reads one.

### Who calls what

Every API call is made **by your server**. Your browser or app does only three things:

1. Opens a `redirectUrl` we give you, when the member signs in at the program or approves a burn.
2. Hosts your completion page, where that `redirectUrl` returns.
3. Collects an OTP the member types, and hands it to your server.

Keys and member tokens never reach a browser or an app.

### Authentication

**Partner.** Use one of two methods on every call, never both (`400`):

- **API key:** `X-API-Key: <secret>` plus `X-Partner-Code: <your code>`.
- **OAuth2 client credentials:** `POST /oauth2/token` with HTTP Basic (client id = partner code, secret = API key) and
  the scopes you need. Then send `Authorization: Bearer <token>`. The token lasts 900 seconds. See
  [recipe 12](#12-secure-and-go-live) for scopes.

```bash
curl -X POST https://api.pointspay.com/loyalty/v1/oauth2/token \
  -u "acme-travel:$POINTSPAY_API_KEY" \
  -d grant_type=client_credentials -d "scope=loyalty.read loyalty.member loyalty.burn"
# → { "access_token": "eyJ...", "token_type": "Bearer", "expires_in": 900, "scope": "loyalty.read loyalty.member loyalty.burn" }
```

**Member.** Balance, quote, burn and OTP calls act on a member's points, so they also carry
`X-Member-Token`. The member gets one by signing in once ([recipe 2](#2-link-a-member)). Then
`POST /members/{memberRef}/token` returns a token that lasts 15 minutes and works only for that member and for you.
Ask for a new one when it expires. You never build a program's login.

### Conventions

| Rule | Detail |
|---|---|
| References | All identifiers are opaque strings ending in `Ref`. Ours: `memberRef`, `contextRef`, `quoteRef`, `estimateRef`, `operationRef`, `reversalRef`. Yours: `partnerOrderRef`, `partnerReversalRef`, `componentRef`, `itemRef`. Never parse ours |
| One "what next" | `nextStep` is `NONE` (done), `REDIRECT` (open `redirectUrl`), `SUBMIT_OTP` (ask for the code) or `SIGN_IN` (link the member first). It appears on sign-in, quote and burn responses |
| Money | `{ "value": 12345, "currency": "EUR" }` is EUR 123.45. Points are integers |
| Idempotency | Every `POST` and `DELETE` needs `X-Idempotency-Key`. A repeat with the same key and body returns the original response ([recipe 11](#11-handle-failure)) |
| Open enums | New values can appear in any enum. An unknown `programCode`, `nextStep`, `status` or capability means "not supported": hide it |
| Errors | `{code, message, key, retryable, traceId}`. Switch on `code`, localise with `key`, quote `traceId` to support |
| Times | ISO 8601, UTC |

### Endpoints at a glance

| Endpoint | Purpose | Scope | Member token | Sync / async | Recipe |
|---|---|---|---|---|---|
| `POST /oauth2/token` | Partner access token | — | — | sync | 12 |
| `GET /programs`, `/programs/{programCode}` | Catalog and descriptors. Cache 5 min | read | — | sync | 1 |
| `POST /auth/member-context` | Start a member sign-in | member | — | async: `member-context.completed` | 2 |
| `GET` / `DELETE /auth/member-context/{contextRef}` | Poll or cancel a sign-in | member | — | sync | 2 |
| `POST /members/{memberRef}/token` | Member token (15 min) | member | — | sync | 2 |
| `GET` / `DELETE /members/{memberRef}` | Profile (tier, benefits) or unlink | member | — | sync | 2, 4 |
| `POST /members/validate` | Check a member number, no sign-in | member | — | sync | 3 |
| `GET /members/{memberRef}/balance` | Balance | member | yes | sync | 4 |
| `POST /accruals/estimate` | Earn estimate for up to 100 items. Cache 15 min | read | — | sync | 5 |
| `POST /redemptions/quote` | Price a burn | burn | yes | sync | 6 |
| `POST /redemptions` | Burn | burn | yes | sync, or async on a step: `operation.updated` | 6 |
| `POST /redemptions/{operationRef}/otp`, `…/otp/resend` | Finish a burn that needs an OTP | burn | yes | sync | 6 |
| `POST /accruals` | Earn now, or schedule it | earn | only if the program needs sign-in to earn | sync, or scheduled: `operation.updated` | 7 |
| `POST /redemptions/{operationRef}/reverse`, `/accruals/{operationRef}/reverse` | Return or claw back points | reverse | — | sync or async: `reversal.updated` | 8 |
| `GET /redemptions/{operationRef}`, `/accruals/{operationRef}` | One operation | read | — | sync | 9 |
| `GET /operations` | Every operation, for reconciliation | read | — | sync | 10 |
| `GET /events` | Replay webhooks (30 days) | read | — | sync | 9 |

Latency targets are in [R4](#r4-performance-targets).

---

## 1. List programs at checkout

**Use it for:** showing loyalty as a payment option, and deciding what else to show for each program.

```text
Your server                                   Pointspay
    │ GET /programs ─────────────────────────────>│
    │<──────────── { programs: [ descriptor, … ] }│   cache up to 5 minutes
```

A descriptor carries display data, the sign-in and burn steps, and the capability flags. Your UI reads these instead of
the program's name:

```json
{
  "programCode": "SAS",
  "displayName": "SAS EuroBonus",
  "logoUrl": "https://static.pointspay.com/programs/sas.svg",
  "pointsUnitLabel": "Points",
  "availability": "AVAILABLE",
  "authMode": "REDIRECT",
  "burnStep": "SUBMIT_OTP",
  "burnStepConditional": false,
  "savedLinkDays": null,
  "memberNumber": { "label": "EuroBonus number", "pattern": "^[0-9A-Z]{6,20}$", "nameFields": ["lastName"] },
  "verticals": ["STAYS", "CARS", "FLIGHTS", "ATTRACTIONS"],
  "eligibleLineTypes": ["ROOM", "CAR", "FLIGHT", "OTHER"],
  "capabilities": {
    "memberNumberCheck": true, "savedLink": false, "earnWithoutSignIn": false,
    "tier": false, "benefits": false, "pointsExpiry": false, "partialReversal": true
  }
}
```

| Field | What your code does with it |
|---|---|
| `availability` | `UNAVAILABLE`: hide the program. `DEGRADED`: show it, but expect retryable errors |
| `authMode` | `REDIRECT`: sign-in opens the program's page ([recipe 2](#2-link-a-member)). `DIRECT_OTP`: a code, no page |
| `burnStep` | Tells you in advance what a burn will need: `NONE`, `SUBMIT_OTP` or `REDIRECT`. `burnStepConditional: true` means the program asks only sometimes. At run time, always follow the response's `nextStep` |
| `memberNumber` | Label, format and name fields for a member-number check |
| `capabilities` | A false flag means "not yet": hide that feature for this program |

**Current programs.** These are the values the descriptors return today. They change as programs enable features. Always
read them from `GET /programs`, never from this table.

| | Flying Blue | Etihad Guest | SAS EuroBonus | Miles & More |
|---|---|---|---|---|
| Sign-in | Program page | Program page | Program page | Program page |
| Extra step on each burn | None | OTP when Etihad asks | OTP | Approve at the program (redirect) |
| Member-number check | Yes | Yes | Yes | Not yet |
| Saved link | Yes | Yes | Not yet | Not yet |
| Earn without sign-in | Yes | Yes | Not yet | Not yet |
| Tier, benefits, points expiry | Not yet | Not yet | Not yet | Not yet |
| Full and partial reversal | Yes | Yes | Yes | Yes |

**Adding a program** needs no work on your side. It appears in `GET /programs`, and every recipe below works unchanged.

**Errors:** `503 LOYALTY_PROGRAM_UNAVAILABLE` on any call means hide that program or offer cash. Other programs are
unaffected.

---

## 2. Link a member

**Use it for:** signing the member in to their program without leaving your checkout, once, and keeping the link if the
member opts in.

Sign-in happens on the program's own page, in a popup (web) or a system browser sheet (app). Programs do not allow
their sign-in page inside an iframe.

```text
Browser / app            Your server                            Pointspay                 Program
  │ member clicks "Link"    │                                      │                         │
  │ open blank popup ──┐    │                                      │                         │
  │ ask server ────────┼───>│ POST /auth/member-context ──────────>│                         │
  │                    │    │<──── { contextRef, redirectUrl, PENDING }                      │
  │ popup → redirectUrl┘    │ start polling, or wait for webhook   │                         │
  │ ──────────────────────────────────────────────────────────────>│ ── sign-in page ───────>│
  │                         │                                      │<── member signed in ────│
  │ popup → your completion page ?contextRef=…&status=READY        │                         │
  │ page tells checkout, closes (a hint only)                      │                         │
  │                         │<─── webhook member-context.completed, or GET …/{contextRef} READY
  │                         │ POST /members/{memberRef}/token ────>│                         │
  │                         │<────────── { memberToken, expiresAt }│                         │
```

### Steps

1. **On the member's click, open a blank popup at once.** Browsers block a popup opened after an async call.
2. **Your server starts the sign-in:**

   ```bash
   curl -X POST https://api.pointspay.com/loyalty/v1/auth/member-context \
     -H "X-API-Key: $POINTSPAY_API_KEY" -H "X-Partner-Code: acme-travel" \
     -H "X-Idempotency-Key: link-7f3a-0001-ctx-000001" -H "Content-Type: application/json" \
     -d '{ "programCode": "FLB", "redirectCompletionUrl": "https://acme.example/loyalty/complete", "saveLink": true }'
   # → { "contextRef": "ctx_8Jk2p", "status": "PENDING", "nextStep": "REDIRECT",
   #     "redirectUrl": "https://api.pointspay.com/loyalty/v1/auth/redirect/ctx_8Jk2p", "expiresAt": "2026-06-30T12:15:00Z" }
   ```

   - `redirectCompletionUrl` must be on an origin you registered at onboarding.
   - If a saved link is still valid, the answer is `status: READY` with `memberRef`, and there is no popup: go to step 5.
3. **Point the popup at `redirectUrl`.** The member signs in at the program.
4. **Learn the result on your server, not from the browser.** Start this the moment the popup opens:
   - **Push:** the `member-context.completed` webhook ([R2](#r2-webhooks)).
   - **Pull:** poll `GET /auth/member-context/{contextRef}` every 1–2 seconds until `status` is not `PENDING`, or until
     `expiresAt`.

   When the member finishes, the popup lands on `redirectCompletionUrl?contextRef=…&status=READY|FAILED|CANCELLED`. That
   page may tell your checkout and close itself, but treat its status as a hint. `window.opener` can be empty, for
   example under a Cross-Origin-Opener-Policy header or in an app browser. If the popup closes while the status is
   still `PENDING`, call `DELETE /auth/member-context/{contextRef}`: the status becomes `CANCELLED`. On a sign-in that
   has already finished, `DELETE` changes nothing and returns its status.
5. **Get a member token:** `POST /members/{memberRef}/token` returns `{memberToken, expiresAt}`. Keep it on your server.
6. **Store `memberRef`** against your customer. It is the same for this member every time you link them. It works across
   your whole site: search, product pages, checkout and after the trip.

### Browser snippet (web)

Your own server endpoints (`/api/loyalty/...`) wrap the calls above.

```js
async function linkLoyaltyAccount(programCode) {
  const popup = window.open('about:blank', 'loyalty-link', 'width=480,height=680'); // on the click, before any await
  const ctx = await (await fetch('/api/loyalty/sign-in', { method: 'POST', body: JSON.stringify({ programCode }) })).json();
  if (ctx.status === 'READY') { popup.close(); return ctx; }
  popup.location.href = ctx.redirectUrl;

  const url = `/api/loyalty/sign-in/${ctx.contextRef}`; // your server asks Pointspay
  return new Promise((resolve) => {
    let done = false;
    const finish = (s) => { if (done) return; done = true; clearInterval(poll); if (!popup.closed) popup.close(); resolve(s); };
    const poll = setInterval(async () => {
      const s = await (await fetch(url)).json();
      if (s.status !== 'PENDING') return finish(s);                                     // the server's answer is the truth
      if (popup.closed) finish(await (await fetch(url, { method: 'DELETE' })).json()); // closed early: CANCELLED
    }, 1500);
  });
}
```

### Apps and full-page redirects

- **iOS and Android apps:** open `redirectUrl` in `ASWebAuthenticationSession` (iOS) or Chrome Custom Tabs (Android),
  and use an app-claimed link (universal link or app link) as `redirectCompletionUrl`. Do not use an embedded WebView:
  program sign-in pages may refuse it. Your app's server confirms the result exactly as in step 4.
- **Full-page redirect** (no popup): send the whole page to `redirectUrl`, and set `redirectCompletionUrl` to the
  checkout page to return to. Confirm on your server as in step 4.

### Saved link

- Send `saveLink: true` when the member ticks "stay linked" in your UI. It applies where `capabilities.savedLink` is true,
  for `savedLinkDays`.
- While the link is valid, `POST /members/{memberRef}/token` keeps returning tokens, and a new sign-in answers `READY`
  at once.
- A program can still ask the member to sign in again at any time. Then member calls answer `401
  LOYALTY_RELINK_REQUIRED`: run this recipe again.
- A member context is not tied to an order. Link on a search page, a product page or in the account area, as well as at
  checkout.
- **Unlink:** `DELETE /members/{memberRef}`. It revokes tokens and forgets the saved link. Scheduled earns still run unless
  you reverse them, and operation records are kept for accounting.

**Errors:** `failureReason` on the sign-in is `MEMBER_CANCELLED`, `SIGN_IN_FAILED`, `PROGRAM_UNAVAILABLE` or `EXPIRED`.
Offer "try again" or cash.

---

## 3. Check a member number

**Use it for:** letting a member earn, or be recognised, by typing their member number, with no sign-in. Examples: a
frequent-flyer number on a flight or car booking, or earning on a stay.

```bash
curl -X POST https://api.pointspay.com/loyalty/v1/members/validate \
  -H "X-API-Key: $POINTSPAY_API_KEY" -H "X-Partner-Code: acme-travel" \
  -H "X-Idempotency-Key: chk-100200300-000001" -H "Content-Type: application/json" \
  -d '{ "programCode": "ETH", "memberNumber": "100200300", "firstName": "Ada", "lastName": "Doe" }'
# → 200 { "result": "VERIFIED", "memberRef": "mbr_ETH_4kP9", "programCode": "ETH",
#         "linkLevel": "NUMBER_VERIFIED", "memberNumberMasked": "*****0300" }
```

- Ask for what `memberNumber.label` and `memberNumber.nameFields` say in the descriptor. Only offer this where
  `capabilities.memberNumberCheck` is true.
- The call always answers `200` with `result`. `NOT_VERIFIED` covers every "no", so it does not reveal whether a number
  exists. Show "Check the number and the name as they appear on your card."
- **What `NUMBER_VERIFIED` allows:** tier lookup, and earning where `capabilities.earnWithoutSignIn` is true. It does not
  allow balance or burn. For those, link the member ([recipe 2](#2-link-a-member)). The same member keeps the same
  `memberRef`, and `linkLevel` becomes `SIGNED_IN`.
- The check reaches the program live. Use a 5-second client timeout. On `LOYALTY_TIMEOUT` or
  `LOYALTY_PROGRAM_UNAVAILABLE`, let the member continue without the number and add it later
  ([recipe 8](#8-cancel-amend-correct)).
- Limit: 5 checks per member number per hour, then `429 LOYALTY_VELOCITY_LIMIT`.

---

## 4. Balance, tier, benefits, expiry

**Balance** (member token):

```bash
curl "https://api.pointspay.com/loyalty/v1/members/mbr_7Qx2/balance?currency=EUR" \
  -H "X-API-Key: $POINTSPAY_API_KEY" -H "X-Partner-Code: acme-travel" -H "X-Member-Token: $MEMBER_TOKEN"
# → { "memberRef": "mbr_7Qx2", "programCode": "FLB", "points": 48500, "pointsUnitLabel": "Miles",
#     "cashValue": { "value": 48500, "currency": "EUR" }, "expiringPoints": [],
#     "asOf": "2026-06-30T12:04:31Z", "source": "CACHED" }
```

- The balance is served from a cache no more than 60 seconds old (`source: CACHED`, `asOf`). This keeps it fast
  enough for every page view.
- `?fresh=true` asks the program live (`source: LIVE`). Use it just before you show a final amount, if you want it.
- `cashValue` is the balance at the program's rate, in the `currency` you ask for. Use it to show one number across a
  multi-product basket.
- `expiringPoints[{points, expiresAt}]` appears where `capabilities.pointsExpiry` is true.

**Tier and benefits:** `GET /members/{memberRef}` returns the profile. `tier` appears where `capabilities.tier` is true.
`benefits` appears where `capabilities.benefits` is true.

```json
{
  "memberRef": "mbr_7Qx2", "programCode": "FLB", "memberNumberMasked": "******4321", "linkLevel": "SIGNED_IN",
  "savedLink": { "active": true, "expiresAt": "2026-09-28T12:00:00Z" },
  "tier": { "standard": "GOLD", "programTierCode": "G", "programTierName": "Gold" },
  "benefits": [ { "code": "PRIORITY_CHECKIN", "description": "Priority check-in", "validUntil": "2027-03-31" } ]
}
```

- `tier.standard` is one scale for every program (`BASE`, `SILVER`, `GOLD`, `PLATINUM`), for your own rules.
  `programTierCode` and `programTierName` are the program's own, for display.
- `benefits[].code` is `FREE_BAGGAGE`, `PRIORITY_CHECKIN`, `SEAT_SELECTION`, `LOUNGE` or `OTHER`.
- Tier works for a `NUMBER_VERIFIED` member too. Recognising a tier needs no burn.

---

## 5. Show earnings before booking

**Use it for:** "Earn 1,350 Miles" on search results and product pages, before anyone signs in.

```bash
curl -X POST https://api.pointspay.com/loyalty/v1/accruals/estimate \
  -H "X-API-Key: $POINTSPAY_API_KEY" -H "X-Partner-Code: acme-travel" -H "Content-Type: application/json" \
  -d '{ "programCodes": ["FLB"],
        "items": [ { "itemRef": "hotel-123", "vertical": "STAYS", "amount": { "value": 45000, "currency": "EUR" } } ] }'
```

```json
{
  "validUntil": "2026-07-01T12:00:00Z",
  "items": [ { "itemRef": "hotel-123", "estimates": [ {
    "programCode": "FLB", "estimateRef": "est_9Hc1", "points": 1350,
    "breakdown": { "base": 450, "promotion": 900, "tier": 0 },
    "appliedPromotions": [ { "code": "SUMMER3X", "label": "3x Miles", "multiplier": 3 } ],
    "creditDelayDays": 14 } ] } ]
}
```

- **No member token needed.** Up to 100 items and any number of programs per call. The call never reaches the program,
  so it is fast enough for search pages ([R4](#r4-performance-targets)).
- **Cache for display** up to 15 minutes (`Cache-Control`).
- **Same number everywhere:** keep each item's `estimateRef`. Pass it when you register the earn ([recipe 7](#7-earn-on-a-booking)),
  before `validUntil`, and the member gets exactly the points you showed.
- **Campaigns and tier:** add `memberRef` to include tier bonuses and campaigns targeted at this member.
  `appliedPromotions[].label` is ready-made badge text. Campaign multipliers are set on our side. You cannot choose them
  in the request.
- **Credit date:** show "credited about `creditDelayDays` days after your stay".

---

## 6. Pay with points

**Use it for:** paying all or part of an order with points. You charge the rest in cash.

```text
Your server                                          Pointspay
  │ POST /redemptions/quote   (lines, points?) ──────────>│  no side effects, never calls the program
  │<── { quoteRef, eligibleAmount, points, cashRemainder, rate, limits, nextStep }
  │ POST /redemptions         (quoteRef, points) ────────>│
  │<── 200 REDEEMED                                       │  nextStep NONE: done
  │<── 202 PENDING_VERIFICATION, nextStep SUBMIT_OTP ─────│  → POST …/otp with the member's code
  │<── 202 PENDING_VERIFICATION, nextStep REDIRECT ───────│  → popup to redirectUrl, then confirm (recipe 2, step 4)
  │ charge cashRemainder on your own rails
  │ cash failed, or order not completed → POST …/reverse (recipe 8)
```

### Quote

Send the whole order as `lines`. Pointspay works out which lines points can pay for (the program's `eligibleLineTypes`),
so your code holds no program rules about taxes, fees or extras.

```bash
curl -X POST https://api.pointspay.com/loyalty/v1/redemptions/quote \
  -H "X-API-Key: $POINTSPAY_API_KEY" -H "X-Partner-Code: acme-travel" -H "X-Member-Token: $MEMBER_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{ "programCode": "ETH", "memberRef": "mbr_ETH_4kP9", "points": 8000,
        "lines": [ { "type": "ROOM", "amount": { "value": 20000, "currency": "EUR" } },
                   { "type": "TAX",  "amount": { "value": 5000,  "currency": "EUR" } } ] }'
```

```json
{
  "quoteRef": "q_ETH_abc1", "expiresAt": "2026-06-30T12:20:00Z",
  "totalAmount": { "value": 25000, "currency": "EUR" }, "eligibleAmount": { "value": 20000, "currency": "EUR" },
  "points": 8000, "pointsValue": { "value": 8000, "currency": "EUR" }, "cashRemainder": { "value": 17000, "currency": "EUR" },
  "rate": { "points": 100, "amount": { "value": 100, "currency": "EUR" } },
  "minPoints": 1000, "maxPoints": 20000, "pointsIncrement": 100, "balance": 48500,
  "appliedPromotions": [], "nextStep": "NONE"
}
```

- **Full payment:** omit `points`, and the quote prices the whole eligible amount.
- **Partial payment:** send the `points` the member chose.
- **`nextStep`** tells you now what the burn will need, so you can prepare the UI.
- **Price adjustments:** `rate` already includes any burn promotion. `appliedPromotions` says which.

**Slider without a round trip.** Compute in the browser, with integers only:

| Quantity | Formula |
|---|---|
| Value of N points (minor units) | `floor(N × rate.amount.value / rate.points)` |
| Points to cover amount A (minor units) | `ceil(A × rate.points / rate.amount.value)` |
| Allowed N | a multiple of `pointsIncrement`, from `minPoints` to `maxPoints`. `maxPoints` is already capped by the eligible amount and the balance |
| Cash to charge | `totalAmount − value of N points` |

Quote again when the member confirms. The quote has no side effects and each call returns a new `quoteRef`, so call it
as often as you need.

### Burn

```bash
curl -X POST https://api.pointspay.com/loyalty/v1/redemptions \
  -H "X-API-Key: $POINTSPAY_API_KEY" -H "X-Partner-Code: acme-travel" -H "X-Member-Token: $MEMBER_TOKEN" \
  -H "X-Idempotency-Key: burn-ord-0099887-000001" -H "Content-Type: application/json" \
  -d '{ "quoteRef": "q_ETH_abc1", "points": 8000, "partnerOrderRef": "ORD-2026-0099887", "entityCode": "NL01" }'
# → 200 { "operationRef": "op_E5b21", "status": "REDEEMED", "nextStep": "NONE", "points": 8000,
#         "pointsValue": { "value": 8000, "currency": "EUR" }, "balanceAfter": 40500, … }
```

- `quoteRef` is required, and `points` must equal the quote's points (else `422 LOYALTY_QUOTE_MISMATCH`). A quote past
  `expiresAt` gives `422 LOYALTY_QUOTE_EXPIRED`: quote again.
- **`nextStep: SUBMIT_OTP`.** The response carries
  `otp: {maskedDestination, expiresAt, attemptsRemaining, resendsRemaining}`.
  - Show "Enter the code sent to +46 70 *** ** 12".
  - Send the code with `POST /redemptions/{operationRef}/otp` and `{ "otpCode": "482913" }`.
  - `POST …/otp/resend` sends a new code while `resendsRemaining > 0`.
- **`nextStep: REDIRECT`.** Open `redirectUrl` in a popup exactly as in [recipe 2](#2-link-a-member).
  - Pass `redirectCompletionUrl` on the burn. It returns to `?operationRef=…&status=…`.
  - Confirm on your server with `GET /redemptions/{operationRef}` or the `operation.updated` webhook.

### Order of legs

1. Burn first. Charge `cashRemainder` only after `REDEEMED`.
2. If the cash charge fails, or you do not complete the order for any reason, reverse the burn in full
   (`reasonCode: PAYMENT_FAILED` or `CANCELLATION`).

You own this step. `GET /operations?kind=BURN&status=REDEEMED&updatedSince=…` lists burns to match against your
completed orders ([recipe 10](#10-reconcile-and-settle)).

### Variations

| Case | How |
|---|---|
| Pay later | Burn at booking. Charge the cash on the due date. If the charge fails or the booking is cancelled first, reverse in full. There is no separate hold: burn plus reversal covers it, for every program |
| Multi-product basket | One quote with all the basket's `lines`, and one burn for the basket. The points leg succeeds or fails as a whole. Keep your own split of points per product, for partial cancellations ([recipe 8](#8-cancel-amend-correct)). One program per basket |
| Earn on the cash part | After the burn, register an earn with `basisAmount` = the cash paid and `relatedOperationRef` = the burn ([recipe 7](#7-earn-on-a-booking)) |
| Discounts | Apply your own discounts to the lines first, then quote. Precedence is always: your discounts, then burn, then earn |

---

## 7. Earn on a booking

**Use it for:** crediting points for a booking, now or after the trip, with no member present where the program allows
it.

```bash
curl -X POST https://api.pointspay.com/loyalty/v1/accruals \
  -H "X-API-Key: $POINTSPAY_API_KEY" -H "X-Partner-Code: acme-travel" \
  -H "X-Idempotency-Key: earn-ord-0100100-000001" -H "Content-Type: application/json" \
  -d '{ "programCode": "FLB", "memberRef": "mbr_7Qx2", "partnerOrderRef": "ORD-2026-0100100",
        "estimateRef": "est_9Hc1", "creditAfter": "2026-07-04",
        "travel": { "vertical": "STAYS", "startDate": "2026-07-01", "endDate": "2026-07-04" } }'
# → 202 { "operationRef": "acc_F1a2b", "status": "SCHEDULED", "points": 1350, "creditAfter": "2026-07-04", … }
```

- **What to earn:** send exactly one of these:
  - `estimateRef`: the points you showed ([recipe 5](#5-show-earnings-before-booking)).
  - `basisAmount`: the cash paid. Pointspay applies the earn rules and campaigns.
  - `points`: an explicit number.
- **When to earn:**
  - Register at booking with `creditAfter` (for example the end of the stay). The earn is `SCHEDULED`: Pointspay holds
    it and credits the program on that date, with no member present.
  - If the booking is cancelled first, reverse it. A scheduled earn is simply cancelled, with nothing sent to the
    program.
  - Without `creditAfter`, the program is credited now (`200 ACCRUED`).
- **Member token:** needed only where `capabilities.earnWithoutSignIn` is false. There, earn while the member is signed
  in, at booking.
- **Confirmation page:** show the points, and "credited about `creditDelayDays` days after your stay".
  - After crediting, the accrual carries `expectedCreditDate` for when the member sees the points at the program.
  - `operation.updated` tells you when that happens.
- **Earn on a redemption booking:** register the earn with `basisAmount` = the cash part and `relatedOperationRef` = the
  burn. The member signed in once for both.

**Member number added or changed later:**

1. Check the new number ([recipe 3](#3-check-a-member-number)).
2. If the earn is still `SCHEDULED`, reverse it (`reasonCode: MEMBER_CHANGE`) and register a new one for the new member.
3. If it is `ACCRUED`, reverse it the same way, then register the new one.

This API credits the points you fund. Flight miles for an airline ticket itself come from the airline, through the PNR.

---

## 8. Cancel, amend, correct

Reversals need no member. They work the same for burns (`/redemptions/{operationRef}/reverse`, points go back to the
member) and earns (`/accruals/{operationRef}/reverse`, points are taken back).

```bash
# return 800 of 2000 burned points, for one cancelled product in a basket
curl -X POST https://api.pointspay.com/loyalty/v1/redemptions/op_B7n2/reverse \
  -H "X-API-Key: $POINTSPAY_API_KEY" -H "X-Partner-Code: acme-travel" \
  -H "X-Idempotency-Key: rev-cxl-2026-0001-000001" -H "Content-Type: application/json" \
  -d '{ "points": 800, "reasonCode": "CANCELLATION", "partnerReversalRef": "CXL-2026-0001", "componentRef": "car-1" }'
```

```json
{
  "operationRef": "op_B7n2", "status": "PARTIALLY_REVERSED", "points": 2000, "reversedPoints": 800,
  "reversals": [ { "reversalRef": "rev_7c", "points": 800, "pointsValue": { "value": 800, "currency": "EUR" },
    "status": "SUCCESS", "reasonCode": "CANCELLATION", "partnerReversalRef": "CXL-2026-0001", "componentRef": "car-1",
    "initiatedBy": { "type": "API_KEY", "id": "key_acme_01" }, "createdAt": "2026-06-30T15:20:00Z" } ]
}
```

| Case | Call |
|---|---|
| Full cancellation | Reverse the burn and the earn, omitting `points` |
| Cancellation with a penalty | You compute the points to return after your penalty, and send them as `points` |
| One product of a basket | `points` = that product's share, and `componentRef` = your label for it |
| Price goes down on amendment | Partial reverse, `reasonCode: AMENDMENT` |
| Price goes up on amendment | A new quote and burn with `relatedOperationRef` = the first burn. This needs the member present (a token, and the program's OTP or redirect). If they are not, charge the difference in cash |
| Failed or late partner payment | Reverse the earn, `reasonCode: PAYMENT_FAILED` |
| Dispute or chargeback | Reverse, `reasonCode: DISPUTE` or `CHARGEBACK` |

**Rules**

- `200` means the reversal succeeded. `202` means it is `PENDING`: wait for `reversal.updated`, and do not re-submit.
- After a `FAILED` reversal, send a new reverse with a new idempotency key.
- The sum of reversals never exceeds the original: `422 LOYALTY_REVERSAL_EXCEEDS_REMAINING`. Keep your own split per
  product, because Pointspay caps only at what remains on the operation.
- Taking back earned points that the member has already spent fails with `failureCode: INSUFFICIENT_BALANCE`. The
  difference is settled in money through the statement ([recipe 10](#10-reconcile-and-settle)).
- The cash side of any refund is yours. Match it to the reversal with `partnerReversalRef`.

---

## 9. Track status

Every change reaches you both ways. Use either, or both:

- **Push:** signed webhooks: `member-context.completed`, `operation.updated`, `reversal.updated` ([R2](#r2-webhooks)).
- **Pull:** `GET /redemptions/{operationRef}`, `GET /accruals/{operationRef}`, `GET /auth/member-context/{contextRef}`.

| You show | Read |
|---|---|
| "Points used" on the confirmation | `points`, `pointsValue` and `balanceAfter` from the burn |
| "Points to earn" and the credit date | The estimate's `points` and `creditDelayDays`, then `expectedCreditDate` |
| "Refund of points complete" in the customer's bookings | A `reversals[]` entry with `status: SUCCESS` |
| Points per product in a basket | Your own split, plus `reversals[]` by `componentRef` |

Webhooks can arrive late or out of order. The GET is always the truth. Missed some? `GET /events?since=…` replays the
last 30 days.

---

## 10. Reconcile and settle

**Every transaction, through the API.** `GET /operations` lists every burn and earn, with its reversals.

```bash
curl "https://api.pointspay.com/loyalty/v1/operations?updatedSince=2026-06-30T00:00:00Z&limit=500" \
  -H "X-API-Key: $POINTSPAY_API_KEY" -H "X-Partner-Code: acme-travel"
# → { "items": [ { "operationRef": "op_B7n2", "kind": "BURN", "partnerOrderRef": "ORD-2026-0100100", "entityCode": "NL01",
#                  "status": "PARTIALLY_REVERSED", "points": 2000, "pointsValue": {…}, "reversals": [ … ], … } ],
#     "nextCursor": "cur_…" }
```

- **Filters:** `updatedSince`, `kind`, `status`, `partnerOrderRef`, `entityCode`.
- **Order:** by (`updatedAt`, `operationRef`). A reversal updates its parent's `updatedAt`, so an incremental pull by
  `updatedSince` catches it.
- **Paging:** follow `nextCursor` until it is `null`.
- **Keys to match on:** your `partnerOrderRef` and `partnerReversalRef`, and our `operationRef` and `reversalRef`.

**Settlement statement: a file, not an API.**

- **Delivery:** the statement for day T (cut-off 00:00 UTC) arrives by 06:00 UTC on T+1, over SFTP. Details are agreed at
  onboarding.
- **Rows:** one per operation and one per reversal.
- **Columns:** `statementDate`, `entityCode`, `kind` (`BURN`, `EARN`, `BURN_REVERSAL`, `EARN_REVERSAL`), `operationRef`,
  `reversalRef`, `programCode`, `partnerOrderRef`, `partnerReversalRef`, `points`, `amount`, `currency`, `direction`
  (`POINTSPAY_OWES_PARTNER` or `PARTNER_OWES_POINTSPAY`), `occurredAt`.
- **Values:** each row is valued at the rate of the original operation.
- **Matching:** every row matches a list entry by `operationRef` and `reversalRef`.

**Multiple legal entities:** set `entityCode` on each burn and earn. Reversals inherit it, and the list filter and the
file carry it, so each entity reconciles on its own.

---

## 11. Handle failure

### Error catalog

| Code | HTTP | Retry? | Tell the member | Your action |
|---|---|---|---|---|
| `LOYALTY_VALIDATION_FAILED` | 400 | No | — | Fix the request |
| `LOYALTY_UNAUTHENTICATED` | 401 | No | — | Check the key or token |
| `LOYALTY_RELINK_REQUIRED` | 401 | No | "Please sign in to your program again" | Run [recipe 2](#2-link-a-member) |
| `LOYALTY_SCOPE_MISSING` | 403 | No | — | Request the scope |
| `LOYALTY_RISK_DECLINED` | 403 | No | "We can't use points for this booking" | Offer cash |
| `LOYALTY_MEMBER_BLOCKED` | 403 | No | "Contact your program" | Offer cash |
| `LOYALTY_OPERATION_NOT_FOUND` / `LOYALTY_MEMBER_NOT_FOUND` | 404 | No | — | Check the reference |
| `LOYALTY_IDEMPOTENCY_CONFLICT` | 409 | No | — | You reused a key with a different body |
| `LOYALTY_OPERATION_IN_PROGRESS` | 409 | Yes | — | Retry after `Retry-After` |
| `LOYALTY_IDEMPOTENCY_IN_PROGRESS` | 425 | Yes | — | Retry after `Retry-After` |
| `LOYALTY_INSUFFICIENT_BALANCE` | 422 | No | "Not enough points" | Quote fewer points |
| `LOYALTY_QUOTE_EXPIRED` / `LOYALTY_QUOTE_MISMATCH` | 422 | No | — | Quote again |
| `LOYALTY_POINTS_OUT_OF_RANGE` | 422 | No | Show the allowed range | Use `minPoints`, `maxPoints`, `pointsIncrement` |
| `LOYALTY_ESTIMATE_EXPIRED` | 422 | No | — | Send `points` or `basisAmount` instead |
| `LOYALTY_OTP_INVALID` | 422 | No | "Wrong code" | Ask again while `attemptsRemaining > 0` |
| `LOYALTY_OTP_EXPIRED` / `LOYALTY_OTP_ATTEMPTS_EXHAUSTED` | 422 | No | "The code expired" | Resend, or start a new burn |
| `LOYALTY_REVERSAL_EXCEEDS_REMAINING` | 422 | No | — | Reverse at most `points − reversedPoints` |
| `LOYALTY_CAPABILITY_NOT_SUPPORTED` | 422 | No | — | Hide the feature (check `capabilities`) |
| `LOYALTY_VELOCITY_LIMIT` / `LOYALTY_RATE_LIMITED` | 429 | Yes | "Too many attempts, try later" | Retry after `Retry-After` |
| `LOYALTY_PROGRAM_UNAVAILABLE` | 503 | Yes | — | Hide the program or offer cash |
| `LOYALTY_TIMEOUT` | 504 | Yes | — | For a write, the outcome is unknown: see below |

### Timeouts and unknown outcomes

- **Client timeouts:** 5 seconds on reads and checks, 10 seconds on burn, earn and reverse.
- **A write that timed out may still have happened.** Repeat it with the **same** idempotency key. You get the original
  result, or `425` while it is still running.
- **Never retry with a new key.** That can burn twice.

### Idempotency

| Situation | Result |
|---|---|
| Same key, same body | The original response is returned, status code and body. Safe to retry |
| Same key, different body | `409 LOYALTY_IDEMPOTENCY_CONFLICT` |
| Key still processing | `425` with `Retry-After` |
| Missing key on a `POST` or `DELETE` | `400` |

- **Format:** keys are at least 16 characters and unique per operation. They are kept for 24 hours.
- **After 24 hours:** before retrying, check `GET /operations?partnerOrderRef=…` to see whether the first attempt landed.

### Falling back to cash

If a program is unavailable, it stays unavailable only for that program. Hide it, or let the member pay in cash, and keep
the checkout moving.

---

## 12. Secure and go live

### Scopes

Ask only for what you use. Each API key is granted scopes at onboarding. With OAuth2, you can narrow them further per
token.

| Scope | Allows |
|---|---|
| `loyalty.read` | Catalog, estimates, operation reads, `GET /operations`, `GET /events` |
| `loyalty.member` | Sign-in, member-number check, member profile, member token, balance, unlink |
| `loyalty.burn` | Quote, burn, OTP |
| `loyalty.earn` | Accruals |
| `loyalty.reverse` | Reversals of burns and earns |

- **Tokens.** OAuth2 access tokens are JWTs (`typ: at+jwt`, audience `https://api.pointspay.com/loyalty/v1`) and last
  900 seconds.
- **Key rotation.** You can hold two active API keys, so you rotate without downtime.
- **mTLS.** Optional in production, on top of either method.

### Member protection

- **Sign-in stays with the program.** Members sign in only on the program's page, with the program's own second factor
  and OTPs. Your pages never see their password.
- **Member tokens** last 15 minutes and work for one member and one partner only. They never reach a browser, an app or a
  webhook.
- **Risk signals.** Send your fraud signals as `riskContext`: `ipAddress`, `deviceId`, and `partnerRiskScore` from 0 to
  100, higher meaning riskier. Send it on sign-in, member-number check, quote, burn and earn. A refusal is
  `403 LOYALTY_RISK_DECLINED`.
- **Velocity limits** apply to sign-ins, member-number checks and burns: `429 LOYALTY_VELOCITY_LIMIT`.
- **Minimal personal data.** Names are used only to match a member number and are never returned. Member numbers come
  back masked. Data is stored in the EU (AWS, Ireland).
- **Audit trail.** Every status change and reversal records `initiatedBy: {type: API_KEY|OAUTH_CLIENT|OPERATOR, id}` and a
  time. `GET /operations` and `GET /events` export it.

### Go-live checklist

| # | Item |
|---|---|
| 1 | Credentials: API key and partner code, and OAuth2 if you use it, with the scopes you need |
| 2 | Registered origins for `redirectCompletionUrl` (web, and app links) |
| 3 | Webhook URL, with signature verification ([R2](#r2-webhooks)) |
| 4 | SFTP details for the settlement file |
| 5 | Programs to enable, from `GET /programs` |
| 6 | Mock run: every recipe against the contract ([R5](#r5-sandbox-and-mock)) |
| 7 | End-to-end in the sandbox, per program: link, quote, burn with each `nextStep`, cash failure then reverse, scheduled earn then cancel, partial reverse, webhook verified, reconciliation pull |

---

## R1. Status lifecycles

**Burn** (`kind: BURN`)

| Status | Meaning |
|---|---|
| `PENDING_VERIFICATION` | Waiting for the OTP or the member's approval (`nextStep`) |
| `REDEEMED` | Points burned. Can still be reversed |
| `FAILED` | The burn did not happen. Final |
| `EXPIRED` | The OTP or approval was not completed in time. Final |
| `PARTIALLY_REVERSED` | Some points returned. More reversals are possible |
| `REVERSED` | All points returned. Final |

**Earn** (`kind: EARN`)

| Status | Meaning |
|---|---|
| `SCHEDULED` | Held until `creditAfter`. A reversal cancels it |
| `ACCRUED` | Credited to the program. `expectedCreditDate` says when the member sees it. Can still be reversed |
| `FAILED` | Not credited. Final. No points exist to claw back |
| `PARTIALLY_REVERSED` / `REVERSED` | As for burns |

**Reversal** (`reversals[].status`): `PENDING`, then `SUCCESS` or `FAILED`. A pending or failed reversal never changes
the operation's `status`. Only a successful one does, through `reversedPoints`: `0 < reversedPoints < points` is
`PARTIALLY_REVERSED`, and `reversedPoints == points` is `REVERSED`.

**Sign-in** (`GET /auth/member-context/{contextRef}`): `PENDING`, then `READY`, `FAILED`, `CANCELLED` or `EXPIRED`.

---

## R2. Webhooks

Pointspay POSTs a signed JWT (compact JWS, `Content-Type: application/jwt`) to your webhook URL. Verify it like any JWT,
with the code in [`JWT_SIGNATURE_VERIFICATION.md`](./JWT_SIGNATURE_VERIFICATION.md), using these values:

| | Value |
|---|---|
| Issuer (`iss`) | `https://api.pointspay.com/loyalty/v1`. Check it exactly |
| JWKS | `https://api.pointspay.com/loyalty/v1/.well-known/jwks.json`. Pick the key by the header's `kid` |
| Algorithms | `RS256`, `RS384`, `RS512` only. Reject `alg: none` |
| Audience (`aud`) | Your partner code |
| Freshness | Reject if `exp` is past. Dedupe on `jti` |

| Event (`evt`) | When | Claims |
|---|---|---|
| `member-context.completed` | A sign-in left `PENDING` | `ctx` (contextRef), `stat`, `mrf` (memberRef, when `READY`), `rsn` (failure reason), `prg` |
| `operation.updated` | A burn or earn changed status | `opr`, `knd`, `prg`, `stat`, `pts`, `rpts`, `pref` (your partnerOrderRef), `oat` |
| `reversal.updated` | A reversal changed status | as `operation.updated`, plus `rvr` (reversalRef), `rstat`, `cref` (componentRef) |

```json
{ "iss": "https://api.pointspay.com/loyalty/v1", "aud": "acme-travel", "jti": "evt_4c91a0", "iat": 1782820000, "exp": 1782820300,
  "evt": "operation.updated", "opr": "op_E5b21", "knd": "BURN", "prg": "ETH", "stat": "REDEEMED",
  "pts": 12000, "rpts": 0, "pref": "ORD-2026-0099887", "oat": "2026-06-30T12:08:42Z" }
```

- **No tokens in webhooks.** After `member-context.completed` with `READY`, fetch a member token with
  `POST /members/{memberRef}/token`.
- **Acknowledge with any `2xx`** within 10 seconds.
- **Retries** on anything else: after 1 min, 5 min, 30 min, 2 h and 6 h, then every 12 h for 3 days.
- **Order is not guaranteed.** On doubt, read the resource.
- **Recovery:** `GET /events?since=…` replays every event from the last 30 days.

---

## R3. Versioning and deprecation

- **Versioning:** the version is in the path, `/loyalty/v1`. Within v1 we only add things: new endpoints, new optional
  fields, new enum values. Enums are open, so handle unknown values ([Conventions](#conventions)).
- **Breaking changes** go into a new version (`/loyalty/v2`). The old version stays live for at least **12 months** after
  we announce its end.
- **Signals during that period:** responses from the old version carry a `Deprecation` header (RFC 9745), a `Sunset`
  header with the end date (RFC 8594), and `Link: <…>; rel="deprecation"` pointing to the migration notes.

---

## R4. Performance targets

Targets are p99, measured at our edge.

| Call | Target | Why it holds |
|---|---|---|
| `GET /programs` | < 100 ms | Static, cacheable |
| `POST /redemptions/quote` | < 300 ms | Config only, never calls the program |
| `GET /members/{memberRef}/balance` | < 300 ms | Served from a cache no more than 60 s old (`source: CACHED`). `fresh=true` reaches the program live and has no target |
| `POST /accruals/estimate` (100 items) | < 300 ms | Config only, never calls the program |
| Burn, earn, reverse, member-number check | Depends on the program | These reach the program. Use the client timeouts in [recipe 11](#11-handle-failure), then read the outcome |

Rate limits are set per partner at onboarding. Beyond them the answer is `429` with `Retry-After`.

---

## R5. Sandbox and mock

- **Local mock.** The contract's examples act as sandbox data. Run it locally:

  ```bash
  npx @stoplight/prism-cli mock loyalty-orchestrator-api.yaml        # serves http://127.0.0.1:4010
  scripts/verify-recipes.sh                                         # one request per recipe, against the mock
  ```

  The mock checks your requests against the contract, including auth headers, idempotency keys and required fields.
  Send `Prefer: example=SAS` for SAS's descriptor, or `Prefer: code=202, example=otp` for a burn that asks for an OTP.
- **Test members.** Use the example references in the contract, such as `mbr_7Qx2` (Flying Blue, signed in) and
  `mbr_ETH_4kP9` (Etihad Guest). Sandbox test members with known balances for every program are issued with sandbox
  access.
- **Hosted mock:** `https://lorch-sandbox.pointspay.com/loyalty/v1` (planned).

---

*To begin, contact the Pointspay Integration Team. Companion documents: the OpenAPI contract
[`loyalty-orchestrator-api.yaml`](./loyalty-orchestrator-api.yaml) and
[`JWT_SIGNATURE_VERIFICATION.md`](./JWT_SIGNATURE_VERIFICATION.md) (webhook verification).*
