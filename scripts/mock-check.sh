#!/usr/bin/env bash
# Send one request to loyalty-orchestrator-api.yaml served as a local mock (Prism) and assert on the answer.
#
#   scripts/mock-check.sh METHOD PATH STATUS JQ_FILTER [JSON_BODY] [PREFER]
#   scripts/mock-check.sh GET /programs/SAS 200 '.burnStep == "SUBMIT_OTP"' '' 'example=SAS'
#
# PATH is the spec's `paths` key (no /loyalty/v1 prefix). STATUS is also sent as `Prefer: code=STATUS`, so Prism
# returns that response's example. Reuses a mock already listening on MOCK_PORT (default 4010), else starts one.
set -euo pipefail
cd "$(dirname "$0")/.."

method=$1 path=$2 status=$3 filter=$4 body=${5:-} prefer=${6:-}
port=${MOCK_PORT:-4010}
base="http://127.0.0.1:$port"

if ! curl -s -o /dev/null "$base/"; then
  log=$(mktemp)
  npx -y @stoplight/prism-cli@5 mock -p "$port" loyalty-orchestrator-api.yaml >"$log" 2>&1 &
  mock_pid=$!
  trap 'kill "$mock_pid" 2>/dev/null || true' EXIT
  for _ in $(seq 90); do curl -s -o /dev/null "$base/" && break; sleep 1; done
  curl -s -o /dev/null "$base/" || { echo "mock did not start:"; cat "$log"; exit 1; }
fi

[[ $prefer == *code=* ]] || prefer="code=$status${prefer:+, $prefer}"
out=$(mktemp)
args=(-s -o "$out" -w '%{http_code}' -X "$method" "$base$path"
  -H 'X-API-Key: mock-key' -H 'X-Partner-Code: mock-partner' -H 'X-Member-Token: mock-member-token'
  -H 'X-Idempotency-Key: mock-check-0000000001' -H "Prefer: $prefer")
[[ -n $body ]] && args+=(-H 'Content-Type: application/json' --data "$body")

code=$(curl "${args[@]}")
if [[ $code != "$status" ]]; then echo "FAIL $method $path: expected HTTP $status, got $code"; cat "$out"; echo; exit 1; fi
if ! jq -e "$filter" "$out" >/dev/null; then echo "FAIL $method $path: $filter"; cat "$out"; echo; exit 1; fi
echo "ok   $method $path -> $code"
