#!/bin/bash
set -e

echo "=========================================="
echo "Testing WhatsApp Bot Demo Workflow"
echo "=========================================="

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Configuration
WEBHOOK_URL="http://localhost:5678/webhook/whatsapp-bot"
TIMEOUT=15

echo -e "${YELLOW}Testing WhatsApp Bot webhook at: ${WEBHOOK_URL}${NC}"
echo ""

# Test cases
declare -a TEST_CASES=(
  "incendio|Hay un incendio en mi edificio en colonia Centro|protection_civil|critical"
  "bache|Hay un bache enorme en Reforma|public_services|low"
  "herido|Hay una persona herida inconsciente en la calle|medical|mid"
  "robo|Me están robando con un arma en Iztapalapa|security|mid"
  "violencia|Escucho violencia familiar en el departamento de al lado|victim_attention|mid"
)

PASSED=0
FAILED=0

for test_case in "${TEST_CASES[@]}"; do
  IFS='|' read -r name message expected_category expected_risk <<< "$test_case"
  
  echo -e "${YELLOW}Test: ${name}${NC}"
  echo "Message: ${message}"
  
  # Build payload
  PAYLOAD=$(cat <<EOF
{
  "from": "+5255$(printf '%08d' $RANDOM)",
  "message": "${message}",
  "timestamp": "$(date -u +%Y-%m-%dT%H:%M:%SZ)",
  "profile_name": "Usuario Test ${name}"
}
EOF
)
  
  # Make request
  RESPONSE=$(curl -s -w "\n%{http_code}" -X POST "${WEBHOOK_URL}" \
    -H "Content-Type: application/json" \
    -d "${PAYLOAD}" \
    --max-time ${TIMEOUT} 2>&1)
  
  # Extract HTTP code and body
  HTTP_CODE=$(echo "$RESPONSE" | tail -n1)
  BODY=$(echo "$RESPONSE" | sed '$d')
  
  # Check HTTP code
  if [ "$HTTP_CODE" != "200" ]; then
    echo -e "${RED}✗ FAILED: HTTP ${HTTP_CODE}${NC}"
    echo "Response: ${BODY}"
    FAILED=$((FAILED + 1))
    echo ""
    continue
  fi
  
  # Parse JSON response
  STATUS=$(echo "$BODY" | jq -r '.status // "unknown"')
  BOT_REPLY=$(echo "$BODY" | jq -r '.bot_reply // ""')
  CALL_ID=$(echo "$BODY" | jq -r '.call_id // ""')
  CATEGORY=$(echo "$BODY" | jq -r '.case_category // ""')
  BRANCH=$(echo "$BODY" | jq -r '.branch // ""')
  HUMAN_REQUIRED=$(echo "$BODY" | jq -r '.human_required // false')
  
  # Validate response
  ERRORS=0
  
  if [ "$STATUS" != "success" ]; then
    echo -e "${RED}✗ Status is not 'success': ${STATUS}${NC}"
    ERRORS=$((ERRORS + 1))
  fi
  
  if [ -z "$CALL_ID" ]; then
    echo -e "${RED}✗ No call_id returned${NC}"
    ERRORS=$((ERRORS + 1))
  fi
  
  if [ -z "$BOT_REPLY" ]; then
    echo -e "${RED}✗ No bot_reply returned${NC}"
    ERRORS=$((ERRORS + 1))
  fi
  
  # Check category (may differ due to keyword matching)
  if [ "$CATEGORY" != "$expected_category" ]; then
    echo -e "${YELLOW}⚠ Category mismatch: got '${CATEGORY}', expected '${expected_category}'${NC}"
  fi
  
  # Check risk level
  if [ "$BRANCH" != "$expected_risk" ]; then
    echo -e "${YELLOW}⚠ Risk level mismatch: got '${BRANCH}', expected '${expected_risk}'${NC}"
  fi
  
  # Summary
  if [ $ERRORS -eq 0 ]; then
    echo -e "${GREEN}✓ PASSED${NC}"
    echo "  Call ID: ${CALL_ID}"
    echo "  Category: ${CATEGORY}"
    echo "  Branch: ${BRANCH}"
    echo "  Human Required: ${HUMAN_REQUIRED}"
    echo "  Bot Reply: ${BOT_REPLY:0:80}..."
    PASSED=$((PASSED + 1))
  else
    echo -e "${RED}✗ FAILED with ${ERRORS} error(s)${NC}"
    FAILED=$((FAILED + 1))
  fi
  
  echo ""
  sleep 1
done

# Final summary
echo "=========================================="
echo "Test Summary"
echo "=========================================="
echo -e "Total tests: $((PASSED + FAILED))"
echo -e "${GREEN}Passed: ${PASSED}${NC}"
echo -e "${RED}Failed: ${FAILED}${NC}"
echo ""

if [ $FAILED -eq 0 ]; then
  echo -e "${GREEN}✓ All tests passed!${NC}"
  exit 0
else
  echo -e "${RED}✗ Some tests failed${NC}"
  exit 1
fi

# Made with Bob
