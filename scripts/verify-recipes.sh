#!/usr/bin/env bash
# Lint the contract, then run one mock request per recipe. Exits non-zero on the first failure.
set -euo pipefail
cd "$(dirname "$0")/.."
c=scripts/mock-check.sh

npx -y @redocly/cli@1 lint loyalty-orchestrator-api.yaml >/dev/null 2>&1 && echo "ok   lint"
$c GET /redemptions/op_missing 404 '.code == "LOYALTY_OPERATION_NOT_FOUND" and .traceId'
$c GET /programs/SAS 200 '.authMode == "REDIRECT" and .burnStep == "SUBMIT_OTP" and .availability == "AVAILABLE" and (.capabilities | has("memberNumberCheck"))' '' 'example=SAS'
$c GET /programs 200 '.programs | length == 4'
$c POST /auth/member-context 200 '.nextStep == "REDIRECT" and .contextRef and .redirectUrl' '{"programCode":"FLB","redirectCompletionUrl":"https://partner.example/loyalty/complete","saveLink":true}'
$c GET /auth/member-context/ctx_8Jk2p 200 '.status == "READY" and .memberRef'
$c POST /members/mbr_7Qx2/token 200 '.memberToken and .expiresAt'
$c GET /members/mbr_7Qx2 200 '.linkLevel == "SIGNED_IN" and .savedLink.active == true'
$c POST /members/validate 200 '.result == "VERIFIED" and .linkLevel == "NUMBER_VERIFIED"' '{"programCode":"ETH","memberNumber":"100200300","firstName":"Ada","lastName":"Doe"}'
$c GET /members/mbr_7Qx2/balance 200 '.source and .asOf and .cashValue.currency'
$c POST /redemptions/quote 200 '.quoteRef and .eligibleAmount.value and .rate.points and .cashRemainder.currency and .pointsIncrement' '{"programCode":"ETH","memberRef":"mbr_ETH_4kP9","lines":[{"type":"ROOM","amount":{"value":20000,"currency":"EUR"}},{"type":"TAX","amount":{"value":5000,"currency":"EUR"}}],"points":8000}'
$c POST /redemptions 200 '.status == "REDEEMED" and .nextStep == "NONE"' '{"quoteRef":"q_ETH_abc1","points":8000,"partnerOrderRef":"ORD-2026-0099887"}'
$c POST /redemptions 202 '.nextStep == "SUBMIT_OTP" and .otp.attemptsRemaining' '{"quoteRef":"q_SAS_x1","points":9000,"partnerOrderRef":"ORD-2026-0100021"}' 'example=otp'
$c POST /accruals/estimate 200 '.validUntil and .items[0].estimates[0].estimateRef and .items[0].estimates[0].creditDelayDays' '{"programCodes":["FLB"],"items":[{"itemRef":"hotel-123","vertical":"STAYS","amount":{"value":45000,"currency":"EUR"}}]}'
$c POST /accruals 202 '.status == "SCHEDULED" and .creditAfter' '{"programCode":"FLB","memberRef":"mbr_7Qx2","partnerOrderRef":"ORD-2026-0100100","estimateRef":"est_9Hc1","creditAfter":"2026-07-04"}' 'example=scheduled'
$c POST /redemptions/op_B7n2/reverse 200 '.status == "PARTIALLY_REVERSED" and .reversals[0].componentRef and .reversals[0].partnerReversalRef' '{"points":800,"reasonCode":"CANCELLATION","partnerReversalRef":"CXL-2026-0001","componentRef":"car-1"}'
$c GET '/operations?updatedSince=2026-06-30T00:00:00Z' 200 'has("items") and has("nextCursor")'
$c GET '/events?since=2026-06-30T00:00:00Z' 200 '.items[0].evt'
$c GET /redemptions/op_E5b21 200 '.statusUpdates[0].initiatedBy.type'
