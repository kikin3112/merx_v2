#!/usr/bin/env bash
# OWASP ZAP Authenticated Scan Script
# Used by .github/workflows/dast.yml
#
# Required env vars:
#   ZAP_TARGET_URL        — Base URL of the running API (e.g. https://staging.example.com)
#   ZAP_API_KEY           — ZAP daemon API key (set via GitHub Secret)
#   TEST_USER_EMAIL       — Email for obtaining a JWT token
#   TEST_USER_PASSWORD    — Password for obtaining a JWT token
#   TEST_TENANT_ID        — UUID of the test tenant to scan against

set -euo pipefail

echo "=== ZAP Authenticated Scan ==="
echo "Target: ${ZAP_TARGET_URL}"

# -------------------------------------------------------------------------
# Step 1: Obtain a JWT access token
# -------------------------------------------------------------------------
echo "[1/5] Obtaining JWT token..."
LOGIN_RESPONSE=$(curl -sS -X POST "${ZAP_TARGET_URL}/api/v1/auth/login" \
  -H "Content-Type: application/json" \
  -d "{\"username\": \"${TEST_USER_EMAIL}\", \"password\": \"${TEST_USER_PASSWORD}\"}")

ACCESS_TOKEN=$(echo "$LOGIN_RESPONSE" | python3 -c "import sys, json; print(json.load(sys.stdin)['access_token'])")

if [ -z "$ACCESS_TOKEN" ]; then
  echo "ERROR: Failed to obtain JWT token. Check TEST_USER_EMAIL/TEST_USER_PASSWORD."
  echo "Login response: $LOGIN_RESPONSE"
  exit 1
fi

echo "[1/5] JWT token obtained successfully."

# -------------------------------------------------------------------------
# Step 2: Generate OpenAPI spec URL for ZAP to import
# -------------------------------------------------------------------------
OPENAPI_URL="${ZAP_TARGET_URL}/api/v1/openapi.json"
echo "[2/5] Using OpenAPI spec at: $OPENAPI_URL"

# -------------------------------------------------------------------------
# Step 3: Run ZAP with authentication header
# -------------------------------------------------------------------------
echo "[3/5] Starting ZAP authenticated scan..."

docker run --rm \
  -v "$(pwd):/zap/wrk:rw" \
  -e "ZAP_API_KEY=${ZAP_API_KEY:-changeme}" \
  ghcr.io/zaproxy/zaproxy:stable zap-api-scan.py \
    -t "${OPENAPI_URL}" \
    -f openapi \
    -r zap-auth-report.html \
    -J zap-auth-report.json \
    -z "-config globalexcludeurl.url_list.url\(0\).regex=.*/api/v1/auth/.* \
        -config globalexcludeurl.url_list.url\(0\).description=Auth \
        -config globalexcludeurl.url_list.url\(0\).enabled=true" \
    -H "Authorization: Bearer ${ACCESS_TOKEN}" \
    -H "X-Tenant-ID: ${TEST_TENANT_ID}" \
    --hook=/zap/wrk/.security/zap-hook.py \
    2>&1 || true  # Don't fail CI on findings — report them as GitHub Issues instead

echo "[3/5] ZAP scan complete."

# -------------------------------------------------------------------------
# Step 4: Parse findings and create GitHub Issues for HIGH/CRITICAL
# -------------------------------------------------------------------------
echo "[4/5] Parsing ZAP results..."

if [ -f "zap-auth-report.json" ]; then
  CRITICAL_COUNT=$(python3 -c "
import json, sys
with open('zap-auth-report.json') as f:
  data = json.load(f)
alerts = data.get('site', [{}])[0].get('alerts', [])
high = [a for a in alerts if int(a.get('riskcode', 0)) >= 3]
print(len(high))
" 2>/dev/null || echo "0")

  echo "HIGH/CRITICAL findings: $CRITICAL_COUNT"

  if [ "$CRITICAL_COUNT" -gt "0" ] && [ -n "${GITHUB_TOKEN:-}" ]; then
    echo "[4/5] Creating GitHub Issue for findings..."
    ISSUE_BODY="## ZAP Authenticated Scan — Security Findings

**Target:** \`${ZAP_TARGET_URL}\`
**Date:** $(date -u +%Y-%m-%dT%H:%M:%SZ)
**HIGH/CRITICAL Alerts:** ${CRITICAL_COUNT}

See attached artifact \`zap-authenticated-report\` in the [Actions run](${GITHUB_SERVER_URL}/${GITHUB_REPOSITORY}/actions/runs/${GITHUB_RUN_ID}) for full details.

### Required Action
Review and remediate all HIGH/CRITICAL findings before next release.

/cc @luisr"

    gh issue create \
      --title "🔴 ZAP Scan: ${CRITICAL_COUNT} HIGH/CRITICAL findings ($(date +%Y-%m-%d))" \
      --body "$ISSUE_BODY" \
      --label "security,dast" \
      2>/dev/null || echo "WARNING: Could not create GitHub Issue (gh not available or no GITHUB_TOKEN)"
  fi
fi

# -------------------------------------------------------------------------
# Step 5: Summary
# -------------------------------------------------------------------------
echo "[5/5] ZAP authenticated scan complete."
echo "Report: zap-auth-report.json"
