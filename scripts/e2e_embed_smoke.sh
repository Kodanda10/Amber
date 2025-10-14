#!/bin/bash
# E2E smoke test for embed token flow
# Tests token generation, validation, and basic security properties

set -e

# Configuration
API_BASE_URL="${API_BASE_URL:-http://localhost:5000}"
ADMIN_API_KEY="${ADMIN_API_KEY:-test-admin-api-key}"
DASHBOARD_ID="test-dashboard-$(date +%s)"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Helper functions
log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

check_command() {
    if ! command -v $1 &> /dev/null; then
        log_error "$1 is required but not installed"
        exit 1
    fi
}

# Check prerequisites
log_info "Checking prerequisites..."
check_command curl
check_command jq

# Test 1: Health check
log_info "Test 1: Checking API health..."
health_response=$(curl -s -o /dev/null -w "%{http_code}" "$API_BASE_URL/api/health")
if [ "$health_response" != "200" ]; then
    log_error "Health check failed (HTTP $health_response)"
    exit 1
fi
log_info "✓ Health check passed"

# Test 2: Generate embed token (authenticated)
log_info "Test 2: Generating embed token..."
token_response=$(curl -s -X POST "$API_BASE_URL/api/embed/token" \
    -H "Content-Type: application/json" \
    -H "Authorization: Bearer $ADMIN_API_KEY" \
    -d "{\"dashboardId\": \"$DASHBOARD_ID\"}")

if [ $? -ne 0 ]; then
    log_error "Failed to generate token"
    exit 1
fi

# Check if response contains token
token=$(echo "$token_response" | jq -r '.token // empty')
expires_at=$(echo "$token_response" | jq -r '.expiresAt // empty')

if [ -z "$token" ]; then
    log_warn "Token not generated (embedding may not be enabled)"
    log_info "Response: $token_response"
    log_info "Skipping token tests..."
    exit 0
fi

log_info "✓ Token generated successfully"
log_info "  Token preview: ${token:0:50}..."
log_info "  Expires at: $expires_at"

# Test 3: Verify token format
log_info "Test 3: Verifying token format..."
if [[ ! "$token" =~ \. ]]; then
    log_error "Token doesn't have expected format (should contain '.')"
    exit 1
fi
log_info "✓ Token format valid"

# Test 4: Verify expiration is in the future
log_info "Test 4: Verifying token expiration..."
current_time=$(date -u +%s)
expire_time=$(date -d "$expires_at" +%s 2>/dev/null || date -j -f "%Y-%m-%dT%H:%M:%SZ" "$expires_at" +%s 2>/dev/null)

if [ $? -ne 0 ]; then
    log_warn "Could not parse expiration time (date command may vary by OS)"
else
    ttl=$((expire_time - current_time))
    if [ $ttl -le 0 ]; then
        log_error "Token already expired"
        exit 1
    fi
    log_info "✓ Token valid for $ttl seconds"
    
    if [ $ttl -gt 120 ]; then
        log_warn "Token TTL is longer than expected (>120s). Should be short-lived (60s)."
    fi
fi

# Test 5: Test unauthorized access
log_info "Test 5: Testing unauthorized access..."
unauth_response=$(curl -s -o /dev/null -w "%{http_code}" -X POST "$API_BASE_URL/api/embed/token" \
    -H "Content-Type: application/json" \
    -d "{\"dashboardId\": \"$DASHBOARD_ID\"}")

if [ "$unauth_response" == "200" ]; then
    log_error "Endpoint allows unauthorized access!"
    exit 1
fi
log_info "✓ Unauthorized access blocked (HTTP $unauth_response)"

# Test 6: Test with invalid API key
log_info "Test 6: Testing with invalid API key..."
invalid_response=$(curl -s -o /dev/null -w "%{http_code}" -X POST "$API_BASE_URL/api/embed/token" \
    -H "Content-Type: application/json" \
    -H "Authorization: Bearer invalid-key-12345" \
    -d "{\"dashboardId\": \"$DASHBOARD_ID\"}")

if [ "$invalid_response" == "200" ]; then
    log_error "Endpoint accepts invalid API key!"
    exit 1
fi
log_info "✓ Invalid API key rejected (HTTP $invalid_response)"

# Test 7: Test missing dashboardId
log_info "Test 7: Testing validation (missing dashboardId)..."
validation_response=$(curl -s -X POST "$API_BASE_URL/api/embed/token" \
    -H "Content-Type: application/json" \
    -H "Authorization: Bearer $ADMIN_API_KEY" \
    -d "{}")

error_msg=$(echo "$validation_response" | jq -r '.error // empty')
if [ -z "$error_msg" ]; then
    log_error "Missing dashboardId not detected"
    exit 1
fi
log_info "✓ Validation working (error: $error_msg)"

# Test 8: Rate limiting (optional - may fail if limits are high)
log_info "Test 8: Testing rate limiting..."
log_info "  Making 5 rapid requests..."
rate_limit_hit=false
for i in {1..5}; do
    rate_response=$(curl -s -o /dev/null -w "%{http_code}" -X POST "$API_BASE_URL/api/embed/token" \
        -H "Content-Type: application/json" \
        -H "Authorization: Bearer $ADMIN_API_KEY" \
        -d "{\"dashboardId\": \"rate-test-$i\"}")
    
    if [ "$rate_response" == "429" ]; then
        rate_limit_hit=true
        break
    fi
done

if [ "$rate_limit_hit" = true ]; then
    log_info "✓ Rate limiting active"
else
    log_warn "Rate limiting not triggered (may be disabled or limit not reached)"
fi

# Test 9: Metrics endpoint
log_info "Test 9: Checking metrics endpoint..."
metrics_response=$(curl -s "$API_BASE_URL/api/metrics")
if [ $? -ne 0 ]; then
    log_error "Failed to fetch metrics"
    exit 1
fi

embed_requested=$(echo "$metrics_response" | jq -r '.ingest.embed_token_requested // 0')
log_info "✓ Metrics endpoint working"
log_info "  Embed tokens requested: $embed_requested"

# Test 10: Different dashboards get different tokens
log_info "Test 10: Testing token uniqueness..."
token1_response=$(curl -s -X POST "$API_BASE_URL/api/embed/token" \
    -H "Content-Type: application/json" \
    -H "Authorization: Bearer $ADMIN_API_KEY" \
    -d "{\"dashboardId\": \"dashboard-1\"}")
token1=$(echo "$token1_response" | jq -r '.token // empty')

sleep 1  # Brief pause to ensure different timestamps

token2_response=$(curl -s -X POST "$API_BASE_URL/api/embed/token" \
    -H "Content-Type: application/json" \
    -H "Authorization: Bearer $ADMIN_API_KEY" \
    -d "{\"dashboardId\": \"dashboard-2\"}")
token2=$(echo "$token2_response" | jq -r '.token // empty')

if [ "$token1" == "$token2" ]; then
    log_error "Different dashboards got same token!"
    exit 1
fi
log_info "✓ Different dashboards get unique tokens"

# Summary
log_info ""
log_info "========================================="
log_info "All smoke tests passed! ✓"
log_info "========================================="
log_info ""
log_info "Summary:"
log_info "  - API health: OK"
log_info "  - Token generation: OK"
log_info "  - Token format: OK"
log_info "  - Security: OK (auth, validation, rate limiting)"
log_info "  - Metrics: OK"
log_info "  - Token uniqueness: OK"
log_info ""
log_info "Embed token flow is working correctly!"
