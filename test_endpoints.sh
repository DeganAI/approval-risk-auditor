#!/bin/bash

# Test script for Approval Risk Auditor endpoints
# Tests both local and production deployments

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Default to localhost, override with BASE_URL env var
BASE_URL=${BASE_URL:-"http://localhost:8000"}

echo "Testing Approval Risk Auditor API"
echo "Base URL: $BASE_URL"
echo "=================================="
echo ""

# Test 1: Landing Page
echo -e "${YELLOW}Test 1: Landing Page (GET /)${NC}"
STATUS=$(curl -s -o /dev/null -w "%{http_code}" "$BASE_URL/")
if [ "$STATUS" -eq 200 ]; then
    echo -e "${GREEN}✓ PASS${NC} - Landing page returned 200"
else
    echo -e "${RED}✗ FAIL${NC} - Expected 200, got $STATUS"
fi
echo ""

# Test 2: Health Check
echo -e "${YELLOW}Test 2: Health Check (GET /health)${NC}"
RESPONSE=$(curl -s "$BASE_URL/health")
STATUS=$(echo $RESPONSE | jq -r '.status // empty')
if [ "$STATUS" = "healthy" ]; then
    echo -e "${GREEN}✓ PASS${NC} - Health check returned healthy"
    echo "Response: $RESPONSE"
else
    echo -e "${RED}✗ FAIL${NC} - Health check failed"
    echo "Response: $RESPONSE"
fi
echo ""

# Test 3: List Chains
echo -e "${YELLOW}Test 3: List Chains (GET /chains)${NC}"
RESPONSE=$(curl -s "$BASE_URL/chains")
TOTAL=$(echo $RESPONSE | jq -r '.total // 0')
if [ "$TOTAL" -eq 7 ]; then
    echo -e "${GREEN}✓ PASS${NC} - Listed 7 supported chains"
    echo "Chains: $(echo $RESPONSE | jq -r '.chains[].name' | tr '\n' ', ' | sed 's/,$//')"
else
    echo -e "${RED}✗ FAIL${NC} - Expected 7 chains, got $TOTAL"
fi
echo ""

# Test 4: AP2 Metadata (agent.json)
echo -e "${YELLOW}Test 4: AP2 Metadata (GET /.well-known/agent.json)${NC}"
STATUS=$(curl -s -o /dev/null -w "%{http_code}" "$BASE_URL/.well-known/agent.json")
if [ "$STATUS" -eq 200 ]; then
    echo -e "${GREEN}✓ PASS${NC} - agent.json returned 200"
    RESPONSE=$(curl -s "$BASE_URL/.well-known/agent.json")
    NAME=$(echo $RESPONSE | jq -r '.name // empty')
    echo "Agent Name: $NAME"

    # Validate critical fields
    URL=$(echo $RESPONSE | jq -r '.url // empty')
    if [[ $URL == http://* ]]; then
        echo -e "${GREEN}✓ PASS${NC} - URL uses http:// (required)"
    else
        echo -e "${RED}✗ FAIL${NC} - URL must use http://, got: $URL"
    fi

    FACILITATOR=$(echo $RESPONSE | jq -r '.payments[0].extensions.x402.facilitatorUrl // empty')
    if [ "$FACILITATOR" = "https://facilitator.daydreams.systems" ]; then
        echo -e "${GREEN}✓ PASS${NC} - Facilitator URL correct"
    else
        echo -e "${RED}✗ FAIL${NC} - Facilitator URL incorrect: $FACILITATOR"
    fi
else
    echo -e "${RED}✗ FAIL${NC} - Expected 200, got $STATUS"
fi
echo ""

# Test 5: x402 Metadata
echo -e "${YELLOW}Test 5: x402 Metadata (GET /.well-known/x402)${NC}"
STATUS=$(curl -s -o /dev/null -w "%{http_code}" "$BASE_URL/.well-known/x402")
if [ "$STATUS" -eq 402 ]; then
    echo -e "${GREEN}✓ PASS${NC} - x402 endpoint returned 402"
    RESPONSE=$(curl -s "$BASE_URL/.well-known/x402")

    # Validate required fields
    NETWORK=$(echo $RESPONSE | jq -r '.accepts[0].network // empty')
    ASSET=$(echo $RESPONSE | jq -r '.accepts[0].asset // empty')
    PAYTO=$(echo $RESPONSE | jq -r '.accepts[0].payTo // empty')

    echo "Network: $NETWORK"
    echo "Asset: $ASSET"
    echo "PayTo: $PAYTO"

    if [ "$NETWORK" = "base" ]; then
        echo -e "${GREEN}✓ PASS${NC} - Network is base"
    else
        echo -e "${RED}✗ FAIL${NC} - Network should be base, got: $NETWORK"
    fi

    if [ "$ASSET" = "0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913" ]; then
        echo -e "${GREEN}✓ PASS${NC} - Asset is Base USDC"
    else
        echo -e "${RED}✗ FAIL${NC} - Asset incorrect: $ASSET"
    fi
else
    echo -e "${RED}✗ FAIL${NC} - Expected 402, got $STATUS"
fi
echo ""

# Test 6: AP2 Entrypoint Discovery (GET)
echo -e "${YELLOW}Test 6: AP2 Entrypoint Discovery (GET)${NC}"
STATUS=$(curl -s -o /dev/null -w "%{http_code}" "$BASE_URL/entrypoints/approval-risk-auditor/invoke")
if [ "$STATUS" -eq 402 ]; then
    echo -e "${GREEN}✓ PASS${NC} - Entrypoint returned 402 (payment required)"
else
    echo -e "${RED}✗ FAIL${NC} - Expected 402, got $STATUS"
fi
echo ""

# Test 7: HEAD Method Support
echo -e "${YELLOW}Test 7: HEAD Method Support${NC}"
STATUS=$(curl -s -o /dev/null -w "%{http_code}" -I "$BASE_URL/.well-known/agent.json")
if [ "$STATUS" -eq 200 ]; then
    echo -e "${GREEN}✓ PASS${NC} - HEAD request to agent.json returned 200"
else
    echo -e "${RED}✗ FAIL${NC} - Expected 200, got $STATUS"
fi

STATUS=$(curl -s -o /dev/null -w "%{http_code}" -I "$BASE_URL/.well-known/x402")
if [ "$STATUS" -eq 402 ]; then
    echo -e "${GREEN}✓ PASS${NC} - HEAD request to x402 returned 402"
else
    echo -e "${RED}✗ FAIL${NC} - Expected 402, got $STATUS"
fi
echo ""

# Test 8: Approval Audit (Functional Test)
echo -e "${YELLOW}Test 8: Approval Audit Functional Test${NC}"
echo "Testing with Vitalik's address on Ethereum mainnet..."
RESPONSE=$(curl -s -X POST "$BASE_URL/approvals/audit" \
    -H "Content-Type: application/json" \
    -d '{
        "wallet": "0xd8dA6BF26964aF9D7eEd9e03E53415D37aA96045",
        "chains": [1]
    }')

STATUS=$(echo $RESPONSE | jq -r '.wallet // empty')
if [ ! -z "$STATUS" ]; then
    echo -e "${GREEN}✓ PASS${NC} - Audit completed successfully"
    TOTAL=$(echo $RESPONSE | jq -r '.total_approvals // 0')
    CHAINS=$(echo $RESPONSE | jq -r '.chains_scanned | length // 0')
    echo "Total approvals found: $TOTAL"
    echo "Chains scanned: $CHAINS"

    # Show sample approval if any
    if [ "$TOTAL" -gt 0 ]; then
        echo "Sample approval:"
        echo $RESPONSE | jq '.approvals[0]' 2>/dev/null || echo "Could not display sample"
    fi
else
    echo -e "${RED}✗ FAIL${NC} - Audit failed"
    echo "Response: $RESPONSE"
fi
echo ""

# Test 9: Invalid Chain ID
echo -e "${YELLOW}Test 9: Invalid Chain ID Handling${NC}"
STATUS=$(curl -s -o /dev/null -w "%{http_code}" -X POST "$BASE_URL/approvals/audit" \
    -H "Content-Type: application/json" \
    -d '{
        "wallet": "0xd8dA6BF26964aF9D7eEd9e03E53415D37aA96045",
        "chains": [99999]
    }')
if [ "$STATUS" -eq 400 ]; then
    echo -e "${GREEN}✓ PASS${NC} - Invalid chain rejected with 400"
else
    echo -e "${RED}✗ FAIL${NC} - Expected 400, got $STATUS"
fi
echo ""

# Test 10: Missing Required Fields
echo -e "${YELLOW}Test 10: Missing Required Fields${NC}"
STATUS=$(curl -s -o /dev/null -w "%{http_code}" -X POST "$BASE_URL/approvals/audit" \
    -H "Content-Type: application/json" \
    -d '{"wallet": "0xd8dA6BF26964aF9D7eEd9e03E53415D37aA96045"}')
if [ "$STATUS" -eq 422 ]; then
    echo -e "${GREEN}✓ PASS${NC} - Missing field rejected with 422"
else
    echo -e "${RED}✗ FAIL${NC} - Expected 422, got $STATUS"
fi
echo ""

# Summary
echo "=================================="
echo "Test suite completed!"
echo ""
echo "For production deployment:"
echo "1. Set BASE_URL environment variable:"
echo "   export BASE_URL=https://approval-risk-auditor-production.up.railway.app"
echo "2. Run this script again: ./test_endpoints.sh"
echo ""
echo "To register on x402scan:"
echo "Visit: https://www.x402scan.com/resources/register"
echo "URL: $BASE_URL/entrypoints/approval-risk-auditor/invoke"
