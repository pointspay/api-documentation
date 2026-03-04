# Pointspay — Split Payment Integration Overview

> For business and product stakeholders at loyalty and rewards programs considering integration with Pointspay.
> Covers: security, member consent, regulatory alignment, and operational controls.

---

## What Is Pointspay?

Pointspay lets your rewards members **use their points as a payment method** at thousands of online merchants — alongside or instead of their card. Every checkout has up to three components:

```
┌─────────────────────────────────────────────────────────────────────┐
│                                                                     │
│   CUSTOMER CHECKOUT ($100 order)                                    │
│                                                                     │
│   ┌───────────────────┐  ┌───────────────────┐  ┌───────────────┐   │
│   │   PAY WITH CARD   │  │  PAY WITH POINTS  │  │  EARN POINTS  │   │
│   │   (Cash Leg)      │  │  (Points Leg)     │  │  (Earn-Back)  │   │
│   │                   │  │                   │  │               │   │
│   │   $60 on card     │  │  2,000 pts =  $40 │  │  +300 pts on  │   │
│   │                   │  │                   │  │  the $60 cash │   │
│   └───────────────────┘  └───────────────────┘  └───────────────┘   │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

Your members get **three options** at checkout:

| Option | Card Payment | Points Used | Points Earned |
|--------|-------------|-------------|---------------|
| **Earn only** | Full amount | None | Yes — on full amount |
| **Split payment** | Partial | Partial | Yes — on the card portion |
| **Points only** | None | Full amount | None |

---

## How Does the Integration Work?

Pointspay connects to your loyalty platform via **secure Server-to-Server (S2S) APIs**. There is no SDK to install, no widget to embed — Pointspay calls your backend directly.

```
┌──────────┐       ┌──────────────┐        ┌──────────────────┐
│ Customer │──────>│  Pointspay   │──S2S──>│  Your Loyalty    │
│ at       │       │  (payment    │  APIs  │  Platform        │
│ merchant │       │  orchestrator)│       │                  │
└──────────┘       └──────┬───────┘        └──────────────────┘
                          │
                          │ S2S
                          ▼
                   ┌──────────────┐
                   │   Payment    │
                   │   Provider   │
                   │   (cards)    │
                   └──────────────┘
```

**What your platform needs to expose** (REST or SOAP — we support both):

| Capability | What It Does | When Pointspay Calls It |
|------------|-------------|------------------------|
| **Member Profile** | Returns member name, email, points balance | After member logs in |
| **Accrue (Earn)** | Credits points to the member | After a purchase (on the card portion) |
| **Redeem (Burn)** | Debits points from the member | During checkout (points portion) |
| **Reverse Accrue** | Undoes an earn (claws back points) | When the merchant issues a refund |
| **Reverse Redeem** | Undoes a burn (returns points) | When the merchant issues a refund |
| **OTP / Approval** | Triggers member verification before burn | Before redeeming points (if required) |

---

## Member Authentication & Consent

Before Pointspay can access a member's account or spend their points, the member must **explicitly authorize it**. This works like "Log in with Google" — the member is redirected to your login page, authenticates, and grants permission.

```
    ┌───────────────────────────────────────────────────────────────┐
    │                  MEMBER CONSENT FLOW                          │
    │                                                               │
    │  1. Member clicks "Pay with [Your Program]" at checkout       │
    │                         │                                     │
    │                         ▼                                     │
    │  2. Redirected to YOUR login page (your domain, your brand)   │
    │     Member enters credentials on YOUR system                  │
    │                         │                                     │
    │                         ▼                                     │
    │  3. Member authorizes Pointspay to view balance / spend pts   │
    │                         │                                     │
    │                         ▼                                     │
    │  4. Redirected back to checkout with balance visible          │
    │     Member chooses how to split the payment                   │
    │                                                               │
    └───────────────────────────────────────────────────────────────┘
```

**Key trust & compliance points:**

- Pointspay **never sees or stores** your member's login credentials.
- The member authenticates **on your domain**, under your control.
- Pointspay receives only a time-limited access token — not a password.
- The member **sees their balance and explicitly chooses** how many points to spend.
- You define the scopes — what Pointspay can and cannot do with the token.

---

## Transaction-Level Security: OTP & In-App Approval

Pointspay enforces **per-transaction member authorization** before any points are spent. No points leave a member's account without their explicit, real-time consent.

### In-App Push Approval (Recommended for Banks)

For banks — particularly those operating under Central Bank regulations (e.g., CBUAE) — Pointspay supports approval via your existing mobile banking app. **This is the recommended model for UAE-based programs.**

```
┌──────────────────────────────────────────────────────────────────-┐
│               IN-APP APPROVAL — HOW IT WORKS                      │
│                                                                   │
│  1. Member selects points payment at merchant checkout            │
│                         │                                         │
│                         ▼                                         │
│  2. Pointspay sends approval request to YOUR backend              │
│     (amount, merchant, order reference)                           │
│                         │                                         │
│                         ▼                                         │
│  3. YOUR SYSTEM pushes notification to the member's               │
│     banking app — your app, your UX, your security                │
│                         │                                         │
│                         ▼                                         │
│  4. Member reviews the transaction details IN YOUR APP            │
│     and taps Approve or Decline                                   │
│                         │                                         │
│              ┌──────────┴──────────┐                              │
│              ▼                     ▼                              │
│         APPROVED              DECLINED / TIMEOUT                  │
│              │                     │                              │
│              ▼                     ▼                              │
│  5a. Your system sends         5b. Transaction cancelled.         │
│      webhook to Pointspay          NO points are touched.         │
│      Points are debited.           Member is notified.            │
│                                                                   │
└──────────────────────────────────────────────────────────────────-┘
```

**Why this matters for your risk team:**
- The approval happens **entirely within your banking app** — your UX, your security stack, your audit trail.
- Pointspay **cannot bypass** the approval. Without your webhook confirmation, the transaction does not proceed.
- If the member declines **or** the request times out, the transaction is cancelled — **zero points are debited**.
- Every approval request includes the **exact amount and merchant name**, so the member knows exactly what they are authorizing.
- Your system controls the **timeout duration** — typically 2–5 minutes.

### OTP via SMS / Email (Alternative)

For programs that prefer traditional OTP over in-app push:

```
  Member sees checkout ──> Pointspay requests OTP from your system
                           ──> YOUR system sends SMS/email to member
  Member enters OTP    ──> Pointspay submits redeem + OTP code
  in checkout UI           ──> YOUR system verifies OTP, debits points
```

- The OTP is generated and sent **by your system** to your member's registered phone/email.
- Pointspay **never generates, stores, or has access to** the OTP — we only relay the code the member enters.
- The member sees a **masked phone number** (e.g., `+971****89`) confirming where to expect the code.
- Your system controls OTP **length, expiration, and retry limits**.

---

## Refunds — Fully Automated, No Member Involvement

When a merchant issues a refund, Pointspay **automatically and unilaterally reverses** all loyalty operations:

```
┌──────────────────────────────────────────────────────────────────┐
│                     REFUND PROCESS                               │
│                                                                  │
│  Original order: $60 card + 2,000 pts + 300 pts earned           │
│                                                                  │
│  Refund triggers:                                                │
│    ✅  2,000 points RETURNED to member     (reverse redeem)      │
│    ✅  $60 REFUNDED to card                (card refund)         │
│    ✅  300 earned points CLAWED BACK       (reverse accrue)      │
│                                                                  │
│  Result: Member's account restored to pre-purchase state         │
│                                                                  │
│  ⚠️  No member login or approval needed for refunds              │
│  ⚠️  Pointspay retries automatically if your system is           │
│      temporarily unavailable                                     │
└──────────────────────────────────────────────────────────────────┘
```

**Why refunds don't need member consent**: A refund returns value *to* the member (points restored, money returned). It is in the member's interest. Requiring the member to log in and approve a refund would delay the process and create a poor customer experience. This is consistent with how card refunds work — the bank credits the account without asking the cardholder to approve.

**Liability**: Once Pointspay calls your reversal API and receives a success response, the points are considered returned. If your system is temporarily unavailable, Pointspay will **automatically retry** on a schedule. If all retries fail, the Pointspay operations team escalates to your designated contact. The member is never left out of pocket.

Your reversal endpoints **must** be available and **must** support being called multiple times for the same transaction without double-processing (idempotency).

---

## What You Provide — At a Glance

| Item | Description |
|------|-------------|
| **Login page** | Your OAuth2 / SAML login — members authenticate on your domain |
| **API credentials** | Client ID + secret for Pointspay to call your APIs |
| **6 API endpoints** | Profile, Accrue, Redeem, Reverse Accrue, Reverse Redeem, OTP (if applicable) |
| **Sandbox** | A test environment with test member accounts |
| **Technical contact** | An engineer we can work with during integration |

**What you do NOT need to provide:**
- No SDK or JavaScript widget
- No PCI compliance burden (card processing is handled by Pointspay)
- No changes to your member-facing app (unless you want in-app push approval)

---

## Security, Control & Compliance

This section addresses the most common concerns from risk, compliance, and information security teams.

### Data & Privacy

| Question | Answer |
|----------|--------|
| Does Pointspay store member credentials? | **No.** Members authenticate on YOUR system. Pointspay receives only a time-limited access token. |
| What member data does Pointspay handle? | Name, email, member ID, and points balance — only what is needed to display checkout options and process the transaction. |
| Where is data processed? | Pointspay infrastructure is hosted in secure cloud environments. Data residency requirements can be discussed during onboarding. |
| Is data shared with merchants? | Merchants see only the payment outcome (success/failure and amount). They do **not** see member names, balances, or loyalty IDs. |

### Operational Controls

| Control | Details |
|---------|--------|
| **Kill switch** | You can revoke Pointspay's API credentials at any time, instantly suspending all integration activity. No points can be earned, spent, or reversed until credentials are reissued. |
| **Transaction limits** | Your redeem endpoint can enforce per-transaction and daily/monthly spending limits. Pointspay respects whatever limits your system returns. If a redeem is rejected for exceeding a limit, the member is informed and can adjust the split. |
| **Velocity controls** | Your system can reject requests that exceed configured velocity thresholds (e.g., max N redemptions per day per member). |
| **Transaction monitoring** | Every S2S call includes a unique order reference and member ID. Your system can log, audit, and flag anomalies independently. |
| **Sandbox isolation** | All testing happens in a dedicated sandbox environment — production member accounts are never touched during integration and testing. |

### Regulatory Alignment

| Concern | How It Is Addressed |
|---------|--------------------|
| **Member consent (CBUAE / consumer protection)** | Every burn transaction requires explicit member authorization — either via in-app push approval or OTP. Pointspay cannot spend points without real-time member consent. |
| **Dispute resolution** | If a member disputes a transaction, Pointspay provides the full audit trail: timestamps, amounts, operation references, and consent proof (OTP/approval webhook records). |
| **Refund obligations** | Pointspay guarantees that refunded transactions result in full point restoration. The automated retry mechanism ensures reversals complete even if your system has temporary downtime. |
| **AML / KYC** | Pointspay does not onboard end customers. Your program retains full responsibility for KYC. Pointspay interacts only with members who have already been authenticated by your system. |

### What Pointspay Cannot Do

To be explicit about boundaries:

- **Cannot debit points** without real-time member consent (OTP or in-app approval).
- **Cannot access** member login credentials.
- **Cannot override** your system's transaction limits or velocity controls.
- **Cannot process** a transaction if your system returns an error or reject.
- **Cannot retain** member tokens beyond their expiry — tokens are short-lived and non-renewable without fresh authentication.

---

## Timeline & Next Steps

| Phase | Duration | Activities |
|-------|----------|-----------|
| **Discovery** | 1–2 weeks | Align on integration tier, auth model, and API contracts |
| **Development** | 4–8 weeks | Your team implements the API endpoints; Pointspay builds the adapter |
| **Testing** | 2–3 weeks | End-to-end testing in sandbox; edge cases and error scenarios |
| **Go-live** | 1 week | Production credentials exchange, smoke testing, launch |

> **Ready to start?** Contact the Pointspay Integration Team to schedule a discovery session.

---

## Frequently Asked Questions

**Q: What if we want to stop the integration temporarily?**
A: Revoke or rotate the API credentials. All Pointspay calls will fail immediately and gracefully. No points will be affected. Re-enable by issuing new credentials.

**Q: Can a member drain their entire balance in one transaction?**
A: Only if your system allows it. Your redeem endpoint controls the maximum. You can enforce per-transaction caps, daily limits, or minimum balance thresholds.

**Q: What happens if our system goes down during a transaction?**
A: If the redeem call fails, no points are debited and no card charge occurs — the transaction is cancelled. If the system goes down *after* a successful redeem but before the card charge, Pointspay immediately reverses the redeem (points returned). The member is never left in an inconsistent state.

**Q: Who bears the liability if a refund reversal fails repeatedly?**
A: Pointspay retries automatically. If all retries fail, our operations team contacts your designated escalation contact. Both parties work together to resolve manually. The member's points are restored as a priority.

**Q: Does this require changes to our mobile banking app?**
A: Only if you choose the in-app push approval model. If you prefer OTP via SMS, no changes to your app are needed.

**Q: How do we audit transactions?**
A: Every Pointspay request includes a unique order reference and operation reference. Your system can log these and cross-reference with Pointspay's transaction records at any time. A reconciliation API is available.

---

*See [S2S_INTEGRATION.md](S2S_INTEGRATION.md) for the full technical specification.*
