#!/usr/bin/env bash
set -euo pipefail

BASE_URL="${BASE_URL:-http://localhost:8088}"

echo "Smoke test target: $BASE_URL"

echo "1) Health check"
curl -fsS "$BASE_URL/api/health" | python3 -m json.tool

echo "2) OpenAPI check"
curl -fsS "$BASE_URL/api/openapi" | python3 -c 'import sys,json; d=json.load(sys.stdin); print({"openapi": d.get("openapi"), "title": d.get("info",{}).get("title"), "paths": len(d.get("paths",{}))})'

echo "3) Reset reliability state"
curl -fsS -X POST "$BASE_URL/api/reliability/reset" | python3 -m json.tool

echo "4) Rate limit sequence: expected 200,200,200,429"
for i in 1 2 3 4; do
  code=$(curl -s -o /tmp/commproto_rate_${i}.json -w "%{http_code}" "$BASE_URL/api/reliability/rate-limited")
  echo "request $i -> HTTP $code"
done

echo "5) Load-balanced endpoint"
curl -fsS "$BASE_URL/api/reliability/load-balanced" | python3 -m json.tool

echo "6) XML endpoint"
curl -fsS "$BASE_URL/api/exchange/xml" | head -c 300; echo

echo "7) Protobuf endpoint"
curl -fsS -X POST "$BASE_URL/api/encoding/convert" \
  -H 'Content-Type: application/json' \
  -d '{"to":"protobuf","records":[{"id":1,"sensor":"mac-m4-demo","value":88,"unit":"score"}]}' | python3 -m json.tool

echo "DONE: macOS Apple Silicon smoke test completed."
